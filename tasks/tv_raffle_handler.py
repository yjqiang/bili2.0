import asyncio
import random

import bili_statistics
from reqs.tv_raffle_handler import TvRaffleHandlerReq
from tasks.utils import UtilsTask
import utils
from .task_func_decorator import normal
from .base_class import ForcedTask


class TvRaffleJoinTask(ForcedTask):
    TASK_NAME = 'join_tv_raffle'
    # 这是superuser做的,做完之后就broadcast
    @staticmethod
    async def check(user, real_roomid):  # v4
        if not await UtilsTask.is_normal_room(user, real_roomid):
            return None
        json_response = await user.req_s(TvRaffleHandlerReq.check, user, real_roomid)
        # print(json_response['data']['list'])
        checklen = json_response['data']['list']
        if not checklen:  # sb可能返回None
            return None
        next_step_settings = []
        for j in checklen:
            raffle_id = j['raffleId']
            raffle_type = j['type']
            max_wait = j['time'] - 10
            # 处理一些重复
            if not bili_statistics.is_raffleid_duplicate(raffle_id):
                print('本次获取到的抽奖id为', raffle_id)
                next_step_setting = (-2, (j['time_wait'], max_wait), real_roomid, raffle_id, raffle_type)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id, 'TV')
                
        return next_step_settings
        
    @staticmethod
    @normal
    async def work(user, real_roomid, raffleid, raffle_type):  # v4
        # print('参与', raffleid)
        # await UtilsTask.enter_room(user, real_roomid)
        json_rsp = await user.req_s(TvRaffleHandlerReq.join_v4, user, real_roomid, raffleid, raffle_type)
        bili_statistics.add2joined_raffles('小电视(合计)', user.id)
        code = json_rsp['code']
        if not code:
            data = json_rsp['data']
            gift_name = data['gift_name']
            gift_num = data['gift_num']
            user.infos([f'小电视({raffleid})的参与结果: {gift_name}X{gift_num}'])
            bili_statistics.add2results(gift_name, user.id, gift_num)
        elif code == -403 and '拒绝' in json_rsp['msg']:
            user.fall_in_jail()
        else:
            user.warn(f'小电视({raffleid})的参与结果: {json_rsp}')
        
    @staticmethod
    async def check_v3(user, real_roomid):
        if not await UtilsTask.is_normal_room(user, real_roomid):
            return None
        json_response = await user.req_s(TvRaffleHandlerReq.check, user, real_roomid)
        # print(json_response['data']['list'])
        checklen = json_response['data']['list']
        if not checklen:
            return None
        next_step_settings = []
        for j in checklen:
            raffle_id = j['raffleId']
            raffle_type = j['type']
            max_wait = j['time'] - 10
            raffle_end_time = j['time'] + utils.curr_time()
            # 处理一些重复
            if not bili_statistics.is_raffleid_duplicate(raffle_id):
                print('本次获取到的抽奖id为', raffle_id)
                next_step_setting = (-2, (0, max_wait), real_roomid, raffle_id, raffle_type, raffle_end_time)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id)
                
        return next_step_settings
                        
    @staticmethod
    @normal
    async def work_v3(user, real_roomid, raffleid, raffle_type, raffle_end_time):
        # print('参与', raffleid)
        # await UtilsTask.enter_room(user, real_roomid)
        json_response2 = await user.req_s(TvRaffleHandlerReq.join, user, real_roomid, raffleid)
        bili_statistics.add2joined_raffles('小电视(合计)', user.id)
        user.infos([f'小电视({raffleid})的参与状态: {json_response2["msg"]}'])
        # -400不存在
        # -500繁忙
        code = json_response2['code']
        if code:
            if code == -500:
                print('# -500繁忙，稍后重试')
            elif code == 400:
                user.fall_in_jail()
            else:
                print(json_response2)
        else:
            sleeptime = raffle_end_time - utils.curr_time() + 5  # 小于0，call_later自动置0
            delay = random.uniform(sleeptime, sleeptime+90)
            await asyncio.sleep(delay)
            json_response = await user.req_s(TvRaffleHandlerReq.notice, user, real_roomid, raffleid)
            # print(json_response)
            if not json_response['code']:
                # {'code': 0, 'msg': '正在抽奖中..', 'message': '正在抽奖中..', 'data': {'gift_id': '-1', 'gift_name': '', 'gift_num': 0, 'gift_from': '', 'gift_type': 0, 'gift_content': '', 'status': 3}}
                if json_response['data']['gift_id'] != '-1':
                    data = json_response['data']
                    user.infos([f'小电视({raffleid})的参与结果: {data["gift_name"]}X{data["gift_num"]}'])
                    bili_statistics.add2results(data['gift_name'], user.id, data['gift_num'])
                else:
                    user.warn(f'小电视({raffleid})的参与结果: {json_response}')
