import re
import asyncio
import bili_statistics
from reqs.guard_raffle_handler import GuardRaffleHandlerReq
from tasks.utils import UtilsTask


class GuardRaffleHandlerTask:
    @staticmethod
    def target(step):
        if step == 0:
            return GuardRaffleHandlerTask.check
        if step == 1:
            return GuardRaffleHandlerTask.join
        return None
        
    @staticmethod
    async def check(user, real_roomid, raffle_id=None):
        if not await UtilsTask.is_normal_room(user, real_roomid):
            return
        if raffle_id is not None:
            json_rsp = {'data': [{'id': raffle_id, 'time': 65}]}
        else:
            for i in range(10):
                json_rsp = await user.req_s(GuardRaffleHandlerReq.check, user, real_roomid)
                # print(json_rsp)
                if json_rsp['data']:
                    break
                await asyncio.sleep(1)
            else:
                print(f'{real_roomid}没有guard或者guard已经领取')
                return
        next_step_settings = []
        for j in json_rsp['data']:
            raffle_id = j['id']
            # 总督长达一天，额外处理
            max_wait = min(j['time'] - 15, 240)
            if not bili_statistics.is_raffleid_duplicate(raffle_id):
                print('本次获取到的抽奖id为', raffle_id)
                next_step_setting = (1, (0, max_wait), -2, real_roomid, raffle_id)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id)
        return next_step_settings
        
    @staticmethod
    async def join(user, real_roomid, raffle_id):
        # print('参与', raffle_id)
        # {'code': 400, 'msg': '您的操作太快了, 请稍后再试', 'message': '您的操作太快了, 请稍后再试', 'data': []}
        # {'code': 400, 'msg': '你已经领取过啦', 'message': '你已经领取过啦', 'data': []}
        # await UtilsTask.enter_room(user, real_roomid)
        json_rsp = await user.req_s(GuardRaffleHandlerReq.join, user, real_roomid, raffle_id)
        if not json_rsp['code']:
            for award in json_rsp['data']['award_list']:
                result = re.search('(^获得|^)(.*)<%(\+|X)(\d*)%>', award['name'])
                bili_statistics.add2results(result.group(2), user.id, result.group(4))
            user.infos([
                f'大航海({raffle_id})的参与结果: {json_rsp["data"]["message"]}'])
            bili_statistics.add2joined_raffles('大航海(合计)', user.id)
        else:
            print(json_rsp)
