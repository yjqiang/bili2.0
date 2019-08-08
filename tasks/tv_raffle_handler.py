import bili_statistics
from reqs.tv_raffle_handler import TvRaffleHandlerReq
from tasks.utils import UtilsTask
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
                user.info(f'确认获取到小电视抽奖 {raffle_id}', with_userid=False)
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
            user.info(f'小电视({raffleid})的参与结果: {gift_name}X{gift_num}')
            bili_statistics.add2results(gift_name, user.id, gift_num)
        elif code == -403 and '拒绝' in json_rsp['msg']:
            user.fall_in_jail()
        else:
            user.warn(f'小电视({raffleid})的参与结果: {json_rsp}')
