import asyncio
import printer
import utils
import notifier
from .bili_data_types import DynRaffleStatus, DynRaffleResults
from tasks.dyn_raffle_handler import DynRaffleHandlerTask
from . import dyn_raffle_sql


class DynRaffleMonitor:
    def __init__(self, dyn_raffle_description_filter=None, dyn_prize_cmt_filter=None, init_docid=None):
        self.init_docid = init_docid
        if dyn_raffle_description_filter is None:
            self.dyn_raffle_description_filter = []
        else:
            self.dyn_raffle_description_filter = dyn_raffle_description_filter
        if dyn_prize_cmt_filter is None:
            self.dyn_prize_cmt_filter = []
        else:
            self.dyn_prize_cmt_filter = dyn_prize_cmt_filter

    async def fetch_latest_docid(self):
        doc_id = await notifier.exec_func(-1, DynRaffleHandlerTask.create_dyn)
        await notifier.exec_func(-1, DynRaffleHandlerTask.del_dyn_by_docid, doc_id)
        return doc_id

    # 打算设置两步保险，一个是status表中最新doc_id，一个是开一个专门的表专门去定时更新doc_id
    async def get_latest_docid(self) -> int:
        return dyn_raffle_sql.init_docid()

    # 获取dyn_raffle抽奖更多信息并且进行过滤
    async def dig_and_filter(self, doc_id: int, uid: int, post_time: int, describe: str):
        dyn_raffle_status: DynRaffleStatus = await notifier.exec_func(
            -1, DynRaffleHandlerTask.fetch_dyn_raffle_status,
            doc_id, uid, post_time, describe)
        if dyn_raffle_status.lottery_time <= utils.curr_time() + 60:
            printer.info([f'{doc_id}的动态抽奖已经开奖或马上开奖，不再参与'], True)
            return
        for key_word in self.dyn_raffle_description_filter:
            if key_word in dyn_raffle_status.describe:
                printer.info([f'{doc_id}的动态抽奖正文触发关键词过滤({key_word})'], True)
                return
        for key_word in self.dyn_prize_cmt_filter:
            if key_word in dyn_raffle_status.prize_cmt_1st or \
                    key_word in dyn_raffle_status.prize_cmt_2nd or \
                    key_word in dyn_raffle_status.prize_cmt_3rd:
                printer.info([f'{doc_id}的动态抽奖正文触发关键词过滤({key_word})'], True)
                return
        # 如果是刚刚出来的抽奖，就延迟150秒，
        if dyn_raffle_status.post_time >= utils.curr_time() - 150:
            printer.info([f'{doc_id}的动态抽奖触发时间约束，休眠150秒后再正式参与'], True)
            await asyncio.sleep(150)
        printer.info([f'{doc_id}的动态抽奖通过时间和关键词过滤'], True)
        notifier.exec_task(-1, DynRaffleHandlerTask, 0, dyn_raffle_status, delay_range=(0, 0))

    async def run(self):
        if self.init_docid is None:
            init_docid = await self.get_latest_docid()
            if init_docid < 0:
                init_docid = await self.fetch_latest_docid() - 1000 - 1  # 最后保险，必须是有效doc_id
                dyn_raffle_sql.insert_or_replace_other_able('init_docid', init_docid)
            self.init_docid = init_docid + 1
        curr_docid = self.init_docid
        i = 0
        while True:
            code, data = await notifier.exec_func(-1, DynRaffleHandlerTask.is_dyn_raffle, curr_docid)
            await asyncio.sleep(0.4)
            if code == -1:
                print('可能不存在或者到达定点')
                for tmp_docid in range(curr_docid + 1, curr_docid + 11):
                    code, data = await notifier.exec_func(-1, DynRaffleHandlerTask.is_dyn_raffle, tmp_docid)
                    await asyncio.sleep(0.4)
                    if code != -1:
                        curr_docid = tmp_docid
                        break
                else:
                    print('真顶点')
                    await asyncio.sleep(30)
                    continue

            if code == 0:
                await self.dig_and_filter(curr_docid, *data)
                await asyncio.sleep(10)
            curr_docid += 1
            i += 1
            if not i % 50:
                dyn_raffle_sql.insert_or_replace_other_able('init_docid', curr_docid)

    async def check_result(self):
        while True:
            results = dyn_raffle_sql.select_bytime(utils.curr_time() + 7200)  # 延迟2小时处理抽奖
            for dyn_raffle_status in results:
                print(dyn_raffle_status)
                future = asyncio.Future()
                notifier.exec_task(-1, DynRaffleHandlerTask, 2, dyn_raffle_status, future, delay_range=(0, 30))
                await future
                dyn_raffle_results: DynRaffleResults = await notifier.exec_func(
                    -1, DynRaffleHandlerTask.fetch_dyn_raffle_results,
                    dyn_raffle_status)
                if dyn_raffle_results is not None:
                    dyn_raffle_sql.insert_dynraffle_results_table(dyn_raffle_results)

            print('Dnone')
            await asyncio.sleep(3600)
