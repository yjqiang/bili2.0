import asyncio

import bili_statistics
from reqs.guard_raffle_handler import GuardRaffleHandlerReq
from tasks.utils import UtilsTask
from .base_class import Forced, DontWait, Multi


class GuardRafflJoinTask(Forced, DontWait, Multi):
    TASK_NAME = 'join_guard_raffle'

    @staticmethod
    async def check(user, real_roomid, raffle_id=None):
        if not await UtilsTask.is_normal_room(user, real_roomid):
            return
        if raffle_id is not None:
            json_rsp = {'data': {'guard': [{'id': raffle_id, 'time': 65}]}}
        else:
            await asyncio.sleep(5)  # 人为延迟
            json_rsp = await user.req_s(GuardRaffleHandlerReq.check, user, real_roomid)

        next_step_settings = []
        for raffle in json_rsp['data']['guard']:
            raffle_id = raffle['id']
            # 总督长达一天，额外处理
            max_wait = min(raffle['time'] - 15, 240)
            if not bili_statistics.is_raffleid_duplicate(raffle_id):
                user.info(f'确认获取到大航海抽奖 {raffle_id}', with_userid=False)
                next_step_setting = (-2, (0, max_wait), real_roomid, raffle_id)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id, 'GUARD')
        return next_step_settings
        
    @staticmethod
    async def work(user, real_roomid, raffle_id):
        json_rsp = await user.req_s(GuardRaffleHandlerReq.join, user, real_roomid, raffle_id)
        bili_statistics.add2joined_raffles('大航海(合计)', user.id)
        code = json_rsp['code']
        if not code:
            data = json_rsp['data']
            gift_name = data['award_name']
            gift_num = data['award_num']
            user.info(f'大航海({raffle_id})的参与结果: {gift_name}X{gift_num}')
            bili_statistics.add2results(gift_name, user.id, gift_num)
        else:
            user.info(f'大航海({raffle_id})的参与结果: {json_rsp}')
