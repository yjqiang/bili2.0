import bili_statistics
from reqs.tv_raffle_handler import TvRaffleHandlerReq
from tasks.utils import UtilsTask


class TvRaffleHandlerTask:
    @staticmethod
    def target(step):
        if step == 0:
            return TvRaffleHandlerTask.check
        if step == 1:
            return TvRaffleHandlerTask.join
        if step == 2:
            return TvRaffleHandlerTask.notice
        return None
    
    # 这是superuser做的,做完之后就broadcast
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
            max_wait = j['time'] - 15
            # 处理一些重复
            if not bili_statistics.is_raffleid_duplicate(raffle_id):
                print('本次获取到的抽奖id为', raffle_id)
                next_step_setting = (1, (0, max_wait), -2, real_roomid, raffle_id, raffle_type)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id)
                
        return next_step_settings
                        
    @staticmethod
    async def join(user, real_roomid, raffleid, raffle_type):
        # print('参与', raffleid)
        # await UtilsTask.enter_room(user, real_roomid)
        json_response2 = await user.req_s(TvRaffleHandlerReq.join, user, real_roomid, raffleid)
        bili_statistics.add2joined_raffles('小电视(合计)', user.id)
        user.info([f'参与了房间{real_roomid:^9}的小电视抽奖'], True)
        user.info([f'# 小电视抽奖状态: {json_response2["msg"]}'])
        # -400不存在
        # -500繁忙
        code = json_response2['code']
        if not code:
            return (2, (170, 190), user.id, raffleid, real_roomid),
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
            if json_response['data']['gift_id'] == '-1':
                print([f'json_response'], True)
                return
            elif json_response['data']['gift_id'] != '-1':
                data = json_response['data']
                user.info([f'# 房间{real_roomid:^9}小电视抽奖结果: {data["gift_name"]}X{data["gift_num"]}'], True)
                bili_statistics.add2results(data['gift_name'], user.id, data['gift_num'])
