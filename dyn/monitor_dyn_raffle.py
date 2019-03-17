import asyncio
from typing import Optional
import printer
import utils
import notifier
from .bili_data_types import DynRaffleStatus, DynRaffleResults
from tasks.dyn_raffle_handler import DynRaffleHandlerTask
from . import dyn_raffle_sql


class DynRaffleMonitor:
    def __init__(self, should_join_immediately: bool, init_docid=None):
        self.init_docid = init_docid

        self.dyn_raffle_description_filter = []
        self.dyn_prize_cmt_filter = []

        self.should_join_immediately = should_join_immediately
        self._init_handle_status = -1 if not self.should_join_immediately else 0

    # 获取dyn_raffle抽奖更多信息并且进行过滤
    async def dig_and_filter(self, doc_id: int, uid: int, post_time: int, describe: str):
        dyn_raffle_status: DynRaffleStatus = await notifier.exec_func(
            -1, DynRaffleHandlerTask.fetch_dyn_raffle_status,
            doc_id, uid, post_time, describe, self._init_handle_status)
        if dyn_raffle_status.lottery_time <= utils.curr_time() + 180:
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

        if dyn_raffle_sql.is_raffleid_duplicate(dyn_raffle_status.dyn_id):
            printer.info([f'{dyn_raffle_status.doc_id}的动态抽奖触发重复性过滤'], True)
            return
        dyn_raffle_sql.insert_dynraffle_status_table(dyn_raffle_status)

        printer.info([f'{doc_id}的动态抽奖通过过滤与验证，正式处理'], True)

        if not self.should_join_immediately:
            printer.info([f'{dyn_raffle_status.doc_id}的动态抽奖暂不参与，仅记录数据库中等候轮询'], True)
            return
        printer.info([f'{doc_id}的动态抽奖正在参与'], True)
        await notifier.exec_task_awaitable(-1, DynRaffleHandlerTask, 1, dyn_raffle_status,
                                           delay_range=(0, 30))
        dyn_raffle_sql.set_rafflestatus_handle_status(1, dyn_raffle_status.dyn_id)
        printer.info([f'{doc_id}的动态抽奖参与完毕'], True)

    # 暴力docid，查找动态抽奖
    async def check_raffle(self):
        if self.init_docid is None:
            init_docid = dyn_raffle_sql.init_docid()  # 1.数据库查询
            if init_docid < 0:
                doc_id = await notifier.exec_func(-1, DynRaffleHandlerTask.create_dyn)  # 2.动态获取最新的id
                await notifier.exec_func(-1, DynRaffleHandlerTask.del_dyn_by_docid, doc_id)
                init_docid = doc_id - 1000 - 1
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

    # 查看过期的抽奖
    async def check_result(self):
        while True:
            results = dyn_raffle_sql.select_rafflestatus(1, None, utils.curr_time() - 900)  # 延迟15min处理抽奖
            results += dyn_raffle_sql.select_rafflestatus(-1, None, utils.curr_time() - 900)
            printer.info(['正在查找已经结束的动态抽奖：', results], True)
            for dyn_raffle_status in results:

                dyn_raffle_results: Optional[DynRaffleResults] = await notifier.exec_func(
                    -1, DynRaffleHandlerTask.fetch_dyn_raffle_results,
                    dyn_raffle_status)
                print(dyn_raffle_status, dyn_raffle_results)

                await notifier.exec_task_awaitable(-1, DynRaffleHandlerTask, 2, dyn_raffle_status, dyn_raffle_results, delay_range=(0, 30))
                if dyn_raffle_results is not None:
                    dyn_raffle_sql.insert_dynraffle_results_table(dyn_raffle_results)
                dyn_raffle_sql.del_from_dynraffle_status_table(dyn_raffle_status.dyn_id)

            await asyncio.sleep(120)

    # 如果选择should_join_immediately为false，那么就需要这个函数轮询查找即将到期的抽奖，参与
    async def check_handle(self):
        while True:
            curr_time = utils.curr_time()
            results = dyn_raffle_sql.select_rafflestatus(-1, curr_time + 300, curr_time + 1200)[:5]  # 20分钟到5分钟
            printer.info(['正在查找需要参与的动态抽奖：', results], True)
            for dyn_raffle_status in results:
                print(dyn_raffle_status)
                is_exist = await notifier.exec_func(
                    -1, DynRaffleHandlerTask.check, dyn_raffle_status.doc_id)
                if not is_exist:
                    dyn_raffle_sql.del_from_dynraffle_status_table(dyn_raffle_status.dyn_id)
                    continue
                printer.info([f'{dyn_raffle_status.doc_id}的动态抽奖正在参与'], True)
                await notifier.exec_task_awaitable(-1, DynRaffleHandlerTask, 1, dyn_raffle_status)
                dyn_raffle_sql.set_rafflestatus_handle_status(1, dyn_raffle_status.dyn_id)
                printer.info([f'{dyn_raffle_status.doc_id}的动态抽奖参与完毕'], True)
            if not results:
                await asyncio.sleep(60)

    async def run(self):
        results = dyn_raffle_sql.select_rafflestatus(0)
        for dyn_raffle_status in results:
            print(dyn_raffle_status)
            printer.info([f'正在暴力处理上次中断的{dyn_raffle_status.doc_id}的动态抽奖后续'], True)
            dyn_raffle_sql.set_rafflestatus_handle_status(1, dyn_raffle_status.dyn_id)

        printer.info([f'欢迎使用动态抽奖'], True)
        tasks = []
        task_check_raffle = asyncio.ensure_future(self.check_raffle())
        tasks.append(task_check_raffle)
        task_check_result = asyncio.ensure_future(self.check_result())
        tasks.append(task_check_result)
        if not self.should_join_immediately:
            task_check_join = asyncio.ensure_future(self.check_handle())
            tasks.append(task_check_join)
        await asyncio.wait(tasks)
