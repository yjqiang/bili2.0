import bili_statistics
from reqs.pk_raffle_handler import PkRaffleHandlerReq
from tasks.utils import UtilsTask
from .base_class import Forced, DontWait, Multi


class PkRaffleJoinTask(Forced, DontWait, Multi):
    TASK_NAME = 'join_pk_raffle'

    # 这是superuser做的,做完之后就broadcast
    @staticmethod
    async def check(user, real_roomid, json_rsp=None):
        if not await UtilsTask.is_normal_room(user, real_roomid):
            return None
        if json_rsp is None:
            json_rsp = await user.req_s(PkRaffleHandlerReq.check, user, real_roomid)

        next_step_settings = []
        for raffle in json_rsp['data']['pk']:
            raffle_id = raffle['id']
            max_wait = raffle['time'] - 10
            # 处理一些重复
            if not bili_statistics.is_raffleid_duplicate(raffle_id):
                user.info(f'确认获取到大乱斗抽奖 {raffle_id}', with_userid=False)
                next_step_setting = (-2, (0, max_wait), real_roomid, raffle_id)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id, 'PK')
                
        return next_step_settings
        
    @staticmethod
    async def work(user, real_roomid, raffleid):
        # print('参与', raffleid)
        # await UtilsTask.enter_room(user, real_roomid)
        json_rsp = await user.req_s(PkRaffleHandlerReq.join, user, real_roomid, raffleid)
        print(json_rsp)
        bili_statistics.add2joined_raffles('大乱斗(合计)', user.id)
        code = json_rsp['code']
        if not code:
            data = json_rsp['data']
            award_text = data['award_text']
            gift_name, gift_num = award_text.split('X')
            user.info(f'大乱斗({raffleid})的参与结果: {gift_name}X{gift_num}')
            bili_statistics.add2results(gift_name, user.id, int(gift_num))
        else:
            user.warn(f'大乱斗{raffleid})的参与结果: {json_rsp}')
