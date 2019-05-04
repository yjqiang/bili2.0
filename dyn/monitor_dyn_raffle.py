import asyncio
from typing import Optional

from printer import info as print
import utils
import notifier
from .bili_data_types import DynRaffleStatus, DynRaffleResults
from tasks.dyn_raffle_handler import (
    DynRaffleUtilsTask,
    DynRaffleJoinTask,
    DynRaffleNoticeTask
)
from . import dyn_raffle_sql


class DynRaffleMonitor:
    def __init__(self, should_join_immediately: bool, init_docid=None, init_feed_limit=False):
        self._loop = asyncio.get_event_loop()
        self._waiting_pause: Optional[asyncio.Future] = None
        self.init_docid = init_docid

        self.dyn_raffle_description_filter = []
        self.dyn_prize_cmt_filter = []

        self.should_join_immediately = should_join_immediately
        self._init_handle_status = -1 if not self.should_join_immediately else 0
        self._init_feed_limit = init_feed_limit

    # 获取dyn_raffle抽奖更多信息并且进行过滤
    async def dig_and_filter(self, dyn_raffle_status: DynRaffleStatus):
        doc_id = dyn_raffle_status.doc_id
        if dyn_raffle_status.lottery_time <= utils.curr_time() + 180:
            print(f'{doc_id}的动态抽奖已经开奖或马上开奖，不再参与')
            return
        for key_word in self.dyn_raffle_description_filter:
            if key_word in dyn_raffle_status.describe:
                print(f'{doc_id}的动态抽奖正文触发关键词过滤({key_word})')
                return
        for key_word in self.dyn_prize_cmt_filter:
            if key_word in dyn_raffle_status.prize_cmt_1st or \
                    key_word in dyn_raffle_status.prize_cmt_2nd or \
                    key_word in dyn_raffle_status.prize_cmt_3rd:
                print(f'{doc_id}的动态抽奖正文触发关键词过滤({key_word})')
                return
        # 如果是刚刚出来的抽奖，就延迟150秒，
        if dyn_raffle_status.post_time >= utils.curr_time() - 150:
            print(f'{doc_id}的动态抽奖触发时间约束，休眠150秒后再正式参与')
            await asyncio.sleep(150)

        if dyn_raffle_sql.is_raffleid_duplicate(dyn_raffle_status.dyn_id):
            print(f'{dyn_raffle_status.doc_id}的动态抽奖触发重复性过滤')
            return
        dyn_raffle_sql.insert_dynraffle_status_table(dyn_raffle_status)

        print(f'{doc_id}的动态抽奖通过过滤与验证，正式处理')

        if not self.should_join_immediately:
            print(f'{dyn_raffle_status.doc_id}的动态抽奖暂不参与，仅记录数据库中等候轮询')
            return
        print(f'{doc_id}的动态抽奖正在参与')
        await notifier.exec_task(DynRaffleJoinTask, dyn_raffle_status)
        dyn_raffle_sql.set_rafflestatus_handle_status(1, dyn_raffle_status.dyn_id)
        print(f'{doc_id}的动态抽奖参与完毕')

    # 暴力docid，查找动态抽奖
    async def check_raffle(self):
        if self.init_docid is None:
            init_docid = dyn_raffle_sql.init_docid()  # 1.数据库查询
            if init_docid < 0:
                doc_id = await notifier.exec_func(DynRaffleUtilsTask.create_dyn)  # 2.动态获取最新的id
                await notifier.exec_func(DynRaffleUtilsTask.del_dyn_by_docid, doc_id)
                init_docid = doc_id - 1000 - 1
                dyn_raffle_sql.insert_or_replace_other_able('init_docid', init_docid)
            self.init_docid = init_docid + 1
        curr_docid = self.init_docid
        i = 0
        while True:
            if self._waiting_pause is not None:
                print(f'暂停启动动态抽奖查找刷新循环，等待RESUME指令')
                await self._waiting_pause
            code, raffle = await notifier.exec_func(
                DynRaffleUtilsTask.check_and_fetch_raffle, curr_docid, self._init_handle_status, self._init_feed_limit)
            await asyncio.sleep(0.4)
            if code == 404:
                print(f'动态抽奖可能不存在或者到达顶点（开区间）{curr_docid}')
                for tmp_docid in range(curr_docid + 1, curr_docid + 11):
                    code, raffle = await notifier.exec_func(
                        DynRaffleUtilsTask.check_and_fetch_raffle, tmp_docid, self._init_handle_status, self._init_feed_limit)
                    await asyncio.sleep(0.4)
                    if code != 404:
                        curr_docid = tmp_docid
                        break
                else:
                    print(f'当前动态抽奖的顶点为{curr_docid}（开区间）')
                    await asyncio.sleep(30)
                    continue

            if not code:
                print('动态抽奖刷新获取到抽奖信息', raffle)
                await self.dig_and_filter(raffle)
                await asyncio.sleep(10)
            curr_docid += 1
            i += 1
            if not i % 50:
                dyn_raffle_sql.insert_or_replace_other_able('init_docid', curr_docid)

    # 查看过期的抽奖
    async def check_result(self):
        while True:
            if self._waiting_pause is not None:
                print(f'暂停启动动态抽奖查找过期循环，等待RESUME指令')
                await self._waiting_pause
            results = dyn_raffle_sql.select_rafflestatus(1, None, utils.curr_time() - 900)  # 延迟15min处理抽奖
            results += dyn_raffle_sql.select_rafflestatus(-1, None, utils.curr_time() - 900)
            print('正在查找已经结束的动态抽奖：', results)
            for dyn_raffle_status in results:

                dyn_raffle_results: Optional[DynRaffleResults] = await notifier.exec_func(
                    DynRaffleUtilsTask.fetch_dyn_raffle_results,
                    dyn_raffle_status)
                print(dyn_raffle_status, dyn_raffle_results)

                await notifier.exec_task(DynRaffleNoticeTask, dyn_raffle_status, dyn_raffle_results)
                if dyn_raffle_results is not None:
                    dyn_raffle_sql.insert_dynraffle_results_table(dyn_raffle_results)
                dyn_raffle_sql.del_from_dynraffle_status_table(dyn_raffle_status.dyn_id)

            await asyncio.sleep(120)

    # 如果选择should_join_immediately为false，那么就需要这个函数轮询查找即将到期的抽奖，参与
    async def check_handle(self):
        while True:
            if self._waiting_pause is not None:
                print(f'暂停启动动态抽奖查找参与循环，等待RESUME指令')
                await self._waiting_pause
            curr_time = utils.curr_time()
            results = dyn_raffle_sql.select_rafflestatus(-1, curr_time + 300, curr_time + 1200)[:5]  # 20分钟到5分钟
            print('正在查找需要参与的动态抽奖：', results)
            for dyn_raffle_status in results:
                print(dyn_raffle_status)
                is_exist = await notifier.exec_func(
                    DynRaffleUtilsTask.check, dyn_raffle_status.doc_id)
                if not is_exist:
                    dyn_raffle_sql.del_from_dynraffle_status_table(dyn_raffle_status.dyn_id)
                    continue
                print(f'{dyn_raffle_status.doc_id}的动态抽奖正在参与')
                await notifier.exec_task(DynRaffleJoinTask, dyn_raffle_status)
                dyn_raffle_sql.set_rafflestatus_handle_status(1, dyn_raffle_status.dyn_id)
                print(f'{dyn_raffle_status.doc_id}的动态抽奖参与完毕')
            if not results:
                await asyncio.sleep(60)

    def pause(self):
        if self._waiting_pause is None:
            self._waiting_pause = self._loop.create_future()

    def resume(self):
        if self._waiting_pause is not None:
            self._waiting_pause.set_result(True)
            self._waiting_pause = None

    async def run(self):
        results = dyn_raffle_sql.select_rafflestatus(0)
        for dyn_raffle_status in results:
            print(dyn_raffle_status)
            print(f'正在暴力处理上次中断的{dyn_raffle_status.doc_id}的动态抽奖后续')
            dyn_raffle_sql.set_rafflestatus_handle_status(1, dyn_raffle_status.dyn_id)

        print(f'欢迎使用动态抽奖')
        tasks = []
        task_check_raffle = self._loop.create_task(self.check_raffle())
        tasks.append(task_check_raffle)
        task_check_result = self._loop.create_task(self.check_result())
        tasks.append(task_check_result)
        if not self.should_join_immediately:
            task_check_join = self._loop.create_task(self.check_handle())
            tasks.append(task_check_join)
        await asyncio.wait(tasks)
