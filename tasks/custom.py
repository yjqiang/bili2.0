# 理论上项目已有的task不要相互引用，只能引用utils的东西，防止交叉，但是自定义的无所谓，因为绝对不可能交叉
from tasks.live_daily_job import SendGiftTask
from tasks.utils import UtilsTask
from reqs.custom import BuyLatiaoReq, BuyMedalReq


class SendLatiaoTask:
    @staticmethod
    def target(step):
        if step == 0:
            return SendLatiaoTask.send_latiao
        return None
        
    # 到达users的顶之后，notify函数返回None，自然会停止
    @staticmethod
    async def send_latiao(user, room_id, num_max):
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
            if num_max - num_finished >= gift_num:
                num_sent = gift_num
            elif num_max > num_finished:
                num_sent = num_max - num_finished
            else:
                continue
            num_finished += num_sent
            await UtilsTask.send_gift(user, room_id, num_sent, bag_id, gift_id)
        user.infos([f'一共送出{num_finished}个辣条给{room_id}'])
        if num_max - num_finished == 0:
            return None
        return (0, (0, 1.5), user.id + 1, room_id, num_max - num_finished),
        

class BuyLatiaoTask:
    @staticmethod
    async def fetch_silver(user):
        json_rsp = await user.req_s(BuyLatiaoReq.fetch_livebili_userinfo_pc, user)
        if not json_rsp['code']:
            silver = json_rsp['data']['silver']
            return silver
                
    @staticmethod
    async def clean_latiao(user, room_id):
        gift_id = 1
        num_sent = 1
        coin_type = 'silver'
        num_sent = int((await BuyLatiaoTask.fetch_silver(user)) / 100)
        await UtilsTask.buy_gift(user, room_id, num_sent, coin_type, gift_id)
        

class BuyMedalTask:
    @staticmethod
    async def buy_medal(user, room_id, coin_type):
        if coin_type == 'metal' or coin_type == 'silver':
            uid = await UtilsTask.check_uid_by_roomid(user, room_id)
            if uid is not None:
                json_rsp = await BuyMedalReq.buy_medal(user, uid, coin_type)
                user.info(json_rsp['msg'])
        user.info('请重新检查填写coin_type或者房间号')
