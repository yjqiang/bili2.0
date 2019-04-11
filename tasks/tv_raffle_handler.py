import bili_statistics
from reqs.tv_raffle_handler import TvRaffleHandlerReq
from tasks.utils import UtilsTask
import utils


class TvRaffleHandlerTask:
    @staticmethod
    def target(step):
        if step == 0:
            return TvRaffleHandlerTask.check
        if step == 1:
            return TvRaffleHandlerTask.join
        if step == 2:
            return TvRaffleHandlerTask.notice
        if step == 3:
            return TvRaffleHandlerTask.join_v4
        return None
    
    # 这是superuser做的,做完之后就broadcast
    @staticmethod
    async def check_v4(user, real_roomid):
        if not await UtilsTask.is_normal_room(user, real_roomid):
            return
        json_response = await user.req_s(TvRaffleHandlerReq.check, user, real_roomid)
        # print(json_response['data']['list'])
        checklen = json_response['data']['list']
        next_step_settings = []
        for j in checklen:
            raffle_id = j['raffleId']
            raffle_type = j['type']
            max_wait = j['time'] - 10
            # 处理一些重复
            if not bili_statistics.is_raffleid_duplicate(raffle_id):
                print('本次获取到的抽奖id为', raffle_id)
                next_step_setting = (3, (j['time_wait'], max_wait), -2, real_roomid, raffle_id, raffle_type)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id)
                
        return next_step_settings
        
    @staticmethod
    async def join_v4(user, real_roomid, raffleid, raffle_type):
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
        return None
        
    @staticmethod
    async def check(user, real_roomid):
        if not await UtilsTask.is_normal_room(user, real_roomid):
            return
        json_response = await user.req_s(TvRaffleHandlerReq.check, user, real_roomid)
        # print(json_response['data']['list'])
        checklen = json_response['data']['list']
        next_step_settings = []
        for j in checklen:
            raffle_id = j['raffleId']
            raffle_type = j['type']
            max_wait = j['time'] - 10
            raffle_end_time = j['time'] + utils.curr_time()
            # 处理一些重复
            if not bili_statistics.is_raffleid_duplicate(raffle_id):
                print('本次获取到的抽奖id为', raffle_id)
                next_step_setting = (1, (0, max_wait), -2, real_roomid, raffle_id, raffle_type, raffle_end_time)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id)
                
        return next_step_settings
                        
    @staticmethod
    async def join(user, real_roomid, raffleid, raffle_type, raffle_end_time):
        # print('参与', raffleid)
        # await UtilsTask.enter_room(user, real_roomid)
        json_response2 = await user.req_s(TvRaffleHandlerReq.join, user, real_roomid, raffleid)
        bili_statistics.add2joined_raffles('小电视(合计)', user.id)
        user.infos([f'小电视({raffleid})的参与状态: {json_response2["msg"]}'])
        # -400不存在
        # -500繁忙
        code = json_response2['code']
        if not code:
            sleeptime = raffle_end_time - utils.curr_time() + 5 # 小于0，call_later自动置0
            return (2, (sleeptime, sleeptime+90), user.id, raffleid, real_roomid),
        elif code == -500:
            print('# -500繁忙，稍后重试')
            return ()
        elif code == 400:
            user.fall_in_jail()
            return ()
        else:
            print(json_response2)
            return ()
            
    @staticmethod
    async def notice(user, raffleid, real_roomid):
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
