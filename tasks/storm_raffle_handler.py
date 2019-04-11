import bili_statistics
from reqs.storm_raffle_handler import StormRaffleHandlerReq
from tasks.utils import UtilsTask


class StormRaffleHandlerTask:
    @staticmethod
    def target(step):
        if step == 0:
            return StormRaffleHandlerTask.check
        if step == 1:
            return StormRaffleHandlerTask.join
        return None

    # 为了速度，有时不用等room_id验证就参加,置room_id为0，is_normal_room自然会返回固定值true
    @staticmethod
    async def check(user, room_id, raffle_id=None):
        if not await UtilsTask.is_normal_room(user, room_id):
            return
        if raffle_id is not None:
            json_rsp = {'data': {'id': raffle_id}}
        else:
            json_rsp = await user.req_s(StormRaffleHandlerReq.check, user, room_id)
        next_step_settings = []
        data = json_rsp['data']
        if data:
            raffle_id = data['id']
            if not bili_statistics.is_raffleid_duplicate(raffle_id):
                print('本次获取到的抽奖id为', raffle_id)
                next_step_setting = (1, (1, 3), -2, room_id, raffle_id)
                next_step_settings.append(next_step_setting)
                
                next_step_setting = (1, (2, 4), -2, room_id, raffle_id)
                next_step_settings.append(next_step_setting)
                
                bili_statistics.add2raffle_ids(raffle_id)
        return next_step_settings
            
    @staticmethod
    async def join(user, room_id, raffle_id):
        # await UtilsTask.enter_room(user, room_id)
        json_rsp = await user.req_s(StormRaffleHandlerReq.join, user, raffle_id)
        bili_statistics.add2joined_raffles('节奏风暴(合计)', user.id)
        if not json_rsp['code']:
            data = json_rsp['data']
            gift_name = data["gift_name"]
            gift_num = data["gift_num"]
            user.infos([f'飓风暴({raffle_id})的参与结果: {gift_name}X{gift_num}'])
            bili_statistics.add2results(gift_name, user.id, gift_num)
            return
        print(json_rsp)
