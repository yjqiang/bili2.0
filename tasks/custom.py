# 自定义的task
from tasks.live_daily_job import SendGiftTask
from tasks.utils import UtilsTask
from reqs.custom import BuyLatiaoReq, BuyMedalReq
from .task_func_decorator import normal
from .base_class import ForcedTask


class SendLatiaoTask(ForcedTask):
    @staticmethod
    async def check(_, room_id, num_max):
        return (-2, None, room_id, num_max),
        
    # 到达users的顶之后，notify函数返回None，自然会停止
    @staticmethod
    @normal
    async def work(user, room_id, num_max, remain=None):
        if remain is None:
            remain = num_max
        if remain <= 0:
            return 0

        gift_bags = await SendGiftTask.fetch_giftbags(user)
        num_finished = 0
        send_giftbags = []
        for gift in gift_bags:
            gift_id = int(gift[0])
            left_time = gift[3]
            if gift_id == 1 and left_time is not None:
                send_giftbags.append(gift[:3])
        print(user.id, send_giftbags)
        for gift_id, gift_num, bag_id in send_giftbags:
            if remain - num_finished >= gift_num:
                num_sent = gift_num
            elif remain > num_finished:
                num_sent = remain - num_finished
            else:
                continue
            num_finished += num_sent
            await UtilsTask.send_gift(user, room_id, num_sent, bag_id, gift_id)
        user.infos([f'一共送出{num_finished}个辣条给{room_id}'])
        return remain - num_finished
        

class BuyLatiaoTask(ForcedTask):
    @staticmethod
    async def check(_, room_id, num_wanted):
        return (-2, None, room_id, num_wanted),

    @staticmethod
    async def fetch_silver(user):
        json_rsp = await user.req_s(BuyLatiaoReq.fetch_livebili_userinfo_pc, user)
        if not json_rsp['code']:
            silver = json_rsp['data']['silver']
            return silver
                
    @staticmethod
    @normal
    async def work(user, room_id, num_wanted: int):
        gift_id = 1
        coin_type = 'silver'
        if num_wanted == -1:
            num_sent = int((await BuyLatiaoTask.fetch_silver(user)) / 100)
        elif num_wanted <= 0:
            return
        else:
            num_sent = num_wanted
        await UtilsTask.buy_gift(user, room_id, num_sent, coin_type, gift_id)
        

class BuyMedalTask(ForcedTask):
    @staticmethod
    async def check(_, user_id, room_id, coin_type):
        return (user_id, None, room_id, coin_type),

    @staticmethod
    @normal
    async def work(user, room_id, coin_type):
        if coin_type == 'metal' or coin_type == 'silver':
            uid = await UtilsTask.check_uid_by_roomid(user, room_id)
            if uid is not None:
                json_rsp = await BuyMedalReq.buy_medal(user, uid, coin_type)
                user.info(json_rsp['msg'])
                return
        user.info('请重新检查填写coin_type或者房间号')
