"""实物抽奖中假设b站aid设置之后永不变（即aid有效后对应抽奖内容只读，不会更改），但是为无效的aid可能刷新。
而且刷新是指，b站可能会回溯填空的aid（eg：本来没有121，直接到了123，但是某天突然121可用了，有了抽奖）。
"""


import asyncio
from typing import Optional

import printer
import utils
import notifier
from .bili_data_types import SubstanceRaffleStatus, SubstanceRaffleResults
from tasks.substance_raffle_handler import SubstanceRaffleHandlerTask
from . import substance_raffle_sql


class SubstanceRaffleMonitor:
    def __init__(self, init_aid: Optional[int] = None):
        self.init_aid = init_aid
        # 过滤黑名单主要来自 https://github.com/Dawnnnnnn/bilibili-live-tools/blob/master/OnlineHeart.py
        self.substance_raffle_description_filter = [
            "123", "1111", "测试", "測試", "测一测", "ce-shi", "test", "T-E-S-T", "lala",  # 已经出现
            "測一測", "TEST", "Test", "t-e-s-t"   # 合理猜想
        ]

        self.should_join_immediately = False
        self._init_handle_status = -1 if not self.should_join_immediately else 0

    # 获取dyn_raffle抽奖更多信息并且进行过滤
    async def dig_and_filter(self, substance_raffle_status: SubstanceRaffleStatus):
        aid = substance_raffle_status.aid
        number = substance_raffle_status.number

        if substance_raffle_status.join_end_time <= utils.curr_time() + 90:
            printer.info([f'{aid}({number})的实物抽奖已经开奖或马上开奖，不再参与/记录'], True)
            return
        for key_word in self.substance_raffle_description_filter:
            if key_word in substance_raffle_status.describe:
                printer.info([f'{aid}({number})的实物抽奖正文触发关键词过滤({key_word})'], True)
                return
        if substance_raffle_sql.is_raffleid_duplicate(aid, number):
            printer.info([f'{aid}({number})的实物抽奖触发重复性过滤'], True)
            return

        substance_raffle_sql.insert_substanceraffle_status_table(substance_raffle_status)

        printer.info([f'{aid}({number})的实物抽奖通过过滤与验证，正式处理'], True)
        assert not self.should_join_immediately
        if not self.should_join_immediately:
            printer.info([f'{aid}({number})的实物抽奖暂不参与，仅记录数据库中等候轮询'], True)
        return

    async def check_raffle(self):
        if self.init_aid is None:
            init_aid = substance_raffle_sql.init_id()  # 1.数据库查询
            if init_aid < 0:
                # 二分法查询最新aid
                # 中途如果b站刷新增加了aid，那么会导致aid求出来比实际小，无所谓。。
                max_aid = 1000
                min_aid = 0
                while max_aid > min_aid:
                    print('初始化实物抽奖id中', min_aid, max_aid)
                    mid_aid = int((min_aid + max_aid + 1) / 2)
                    is_midaid_exist = await notifier.exec_func(-1, SubstanceRaffleHandlerTask.check, mid_aid)
                    await asyncio.sleep(0.25)

                    print(is_midaid_exist, mid_aid)
                    if not is_midaid_exist:
                        for aid in range(mid_aid + 1, mid_aid + 5):
                            is_aid_exist = await notifier.exec_func(-1, SubstanceRaffleHandlerTask.check, aid)
                            await asyncio.sleep(0.25)
                            if is_aid_exist:
                                min_aid = aid
                                break
                        else:
                            print('真顶点', mid_aid)
                            max_aid = mid_aid - 1
                    else:
                        print('存在', mid_aid)
                        min_aid = mid_aid
                print('最新实物抽奖id为', min_aid, max_aid)
                assert min_aid == max_aid  # 经过验证过，还是以防万一，防止翻车
                init_aid = min_aid  # 初次的话会往前查看10个id，否则不用（因为有数据库说明之前已经处理了）
                substance_raffle_sql.insert_or_replace_other_able('init_id', init_aid)
            self.init_aid = init_aid + 1

        top_aid = self.init_aid
        # CAVEAT: 存储aid的状态，假设aid设置之后永不变（即aid有效后对应抽奖内容只读，不会更改），但是为无效的aid可能刷新。
        cache_aid_code = {}
        while True:
            # 刷新真正的顶点，查看是否b站更新了上限
            while True:
                is_aid_exist = await notifier.exec_func(-1, SubstanceRaffleHandlerTask.check, top_aid)
                await asyncio.sleep(1)
                if not is_aid_exist:
                    print('可能不存在或者到达顶点（开区间）', top_aid)
                    for tmp_aid in range(top_aid + 1, top_aid + 6):
                        is_tmpaid_exist = await notifier.exec_func(
                            -1, SubstanceRaffleHandlerTask.check, tmp_aid)
                        await asyncio.sleep(1)
                        if is_tmpaid_exist:
                            top_aid = tmp_aid
                            break
                    else:
                        print('真顶点（开区间）', top_aid)
                        break
                top_aid += 1
            print(f'当前实物抽奖的顶点为{top_aid}（开区间）')

            # 暴力查找，b站可能会回溯填空的aid（eg：本来没有121，直接到了123，但是某天突然121可用了）
            for curr_aid in range(top_aid-10, top_aid):
                code_in_cache = cache_aid_code.get(curr_aid, 404)
                if code_in_cache != 404:
                    continue
                code, raffles = await notifier.exec_func(
                    -1, SubstanceRaffleHandlerTask.check_and_fetch_raffle, curr_aid)
                cache_aid_code[curr_aid] = code
                print('TEST', curr_aid, code, cache_aid_code)
                if not code:
                    print(raffles)
                    for substance_raffle_status in raffles:
                        await self.dig_and_filter(substance_raffle_status)
                await asyncio.sleep(1)
            substance_raffle_sql.insert_or_replace_other_able('init_id', top_aid-1)

            await asyncio.sleep(60)

    # 查看过期的抽奖
    async def check_result(self):
        while True:
            results = substance_raffle_sql.select_rafflestatus(1, None, utils.curr_time() - 900)  # 延迟15min处理抽奖
            results += substance_raffle_sql.select_rafflestatus(-1, None, utils.curr_time() - 900)
            printer.info(['正在查找已经结束的实物抽奖：', results], True)
            for substance_raffle_status in results:

                substance_raffle_results: Optional[SubstanceRaffleResults] = await notifier.exec_func(
                    -1, SubstanceRaffleHandlerTask.fetch_substance_raffle_results,
                    substance_raffle_status)
                print(substance_raffle_status, substance_raffle_results)

                await notifier.exec_task_awaitable(-2, SubstanceRaffleHandlerTask, 2, substance_raffle_status, substance_raffle_results, delay_range=(0, 30))
                if substance_raffle_results is not None:
                    substance_raffle_sql.insert_substanceraffle_results_table(substance_raffle_results)
                substance_raffle_sql.del_from_substanceraffle_status_table(substance_raffle_status.aid, substance_raffle_status.number)

            await asyncio.sleep(30)

    # 如果选择should_join_immediately为false，那么就需要这个函数轮询查找即将到期的抽奖，参与
    async def check_handle(self):
        while True:
            curr_time = utils.curr_time()
            results = substance_raffle_sql.select_rafflestatus(-1, (curr_time - 45, curr_time + 90))[:5]
            printer.info(['正在查找需要参与的实物抽奖：', results], True)
            for substance_raffle_status in results:
                print(substance_raffle_status)
                aid = substance_raffle_status.aid
                number = substance_raffle_status.number
                is_exist = await notifier.exec_func(-1, SubstanceRaffleHandlerTask.check, aid)
                if not is_exist:
                    substance_raffle_sql.del_from_substanceraffle_status_table(aid, number)
                    printer.warn(f'{substance_raffle_status}消失了。。。。。')
                    continue
                printer.info([f'{aid}({number})的实物抽奖正在参与'], True)
                await notifier.exec_task_awaitable(-2, SubstanceRaffleHandlerTask, 1, substance_raffle_status)
                substance_raffle_sql.set_rafflestatus_handle_status(1, aid, number)
                printer.info([f'{aid}({number})的实物抽奖参与完毕'], True)
            if not results:
                await asyncio.sleep(60)

    async def run(self):
        results = substance_raffle_sql.select_rafflestatus(0)
        for substance_raffle_status in results:
            print(substance_raffle_status)
            aid = substance_raffle_status.aid
            number = substance_raffle_status.number
            printer.info([f'正在暴力处理上次中断的{aid}({number})的实物抽奖后续'], True)
            substance_raffle_sql.set_rafflestatus_handle_status(1, aid, number)

        printer.info([f'欢迎使用实物抽奖'], True)
        tasks = []
        task_check_raffle = asyncio.ensure_future(self.check_raffle())
        tasks.append(task_check_raffle)
        task_check_result = asyncio.ensure_future(self.check_result())
        tasks.append(task_check_result)
        if not self.should_join_immediately:
            task_check_join = asyncio.ensure_future(self.check_handle())
            tasks.append(task_check_join)
        await asyncio.wait(tasks)
