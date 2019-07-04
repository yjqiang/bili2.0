import asyncio
from .utils import UtilsTask
from reqs.live_daily_job import (
    HeartBeatReq,
    RecvHeartGiftReq,
    OpenSilverBoxReq,
    RecvDailyBagReq,
    SignReq,
    WatchTvReq,
    SignFansGroupsReq,
    SendGiftReq,
    ExchangeSilverCoinReq,
)
from .task_func_decorator import unique
from .base_class import SchedTask


class HeartBeatTask(SchedTask):
    TASK_NAME = 'heartbeat'
    @staticmethod
    async def check(_):
        return (-2, (0, 30)),
        
    @staticmethod
    @unique
    async def work(user):
        while True:
            json_rsp = await user.req_s(HeartBeatReq.pc_heartbeat, user)
            # print(json_rsp)
            user.info('心跳包(5分钟左右间隔)')
            json_rsp = await user.req_s(HeartBeatReq.app_heartbeat, user)
            print(json_rsp)
            await asyncio.sleep(300)

                
class RecvHeartGiftTask(SchedTask):
    TASK_NAME = 'recv_heart_gift'
    @staticmethod
    async def check(_):
        return (-2, (0, 30)),
        
    @staticmethod
    @unique
    async def work(user):
        while True:
            json_rsp = await user.req_s(RecvHeartGiftReq.recv_heartgift, user)
            if json_rsp['code'] == 400:
                user.fall_in_jail()
                return
            await asyncio.sleep(300)
 
               
class OpenSilverBoxTask(SchedTask):
    TASK_NAME = 'open_silver_box'
    @staticmethod
    async def check(_):
        return (-2, (0, 30)),
                
    @staticmethod
    @unique
    async def work(user):
        while True:
            user.info("检查宝箱状态")
            temp = await user.req_s(OpenSilverBoxReq.check_time, user)
            # print (temp['code'])    #宝箱领完返回的code为-10017
            if temp['code'] == -10017:
                user.info("今日宝箱领取完毕")
                json_rsp = None
            else:
                time_start = temp['data']['time_start']
                time_end = temp['data']['time_end']
                json_rsp = await user.req_s(OpenSilverBoxReq.open_silver_box, user, time_start, time_end)
            if json_rsp is None or json_rsp['code'] == -10017 or json_rsp['code'] == -800:
                return
            elif not json_rsp['code']:
                user.info("打开了宝箱")
            elif json_rsp['code'] == 400:
                user.info("宝箱开启中返回了小黑屋提示")
                user.fall_in_jail()
                # 马上继续调用，由下一次的user去supend这个task
                return
            else:
                user.info("继续等待宝箱冷却...")
                sleeptime = (json_rsp['data'].get('surplus', 3)) * 60 + 5
                await asyncio.sleep(sleeptime)
                
                
class RecvDailyBagTask(SchedTask):
    TASK_NAME = 'recv_daily_bag'
    @staticmethod
    async def check(_):
        return (-2, (0, 30)),
        
    @staticmethod
    @unique
    async def work(user):
        json_rsp = await user.req_s(RecvDailyBagReq.recv_dailybag, user)
        try:
            json_rsp['data']['bag_list']
        except TypeError:
            user.warn(f'recv_dailybag {json_rsp}')
        for i in json_rsp['data']['bag_list']:
            user.info(f'获得-{i["bag_name"]}-成功')

                
class SignTask(SchedTask):
    TASK_NAME = 'sign'
    @staticmethod
    async def check(_):
        return (-2, (0, 30)),
        
    @staticmethod
    @unique
    async def work(user):
        while True:
            json_rsp = await user.req_s(SignReq.sign, user)
            user.info(f'签到状态: {json_rsp["msg"]}')
            if json_rsp['code'] == -500 and '已' in json_rsp['msg']:
                return
            sleeptime = 350
            await asyncio.sleep(sleeptime)
        
        
class WatchTvTask(SchedTask):
    TASK_NAME = 'watch_tv'
    @staticmethod
    async def check(_):
        return (-2, (0, 30)),
   
    @staticmethod
    @unique
    async def work(user):
        while True:
            # -400 done/not yet
            json_rsp = await user.req_s(WatchTvReq.watch_tv, user)
            user.info(f'双端观看直播:  {json_rsp["msg"]}')
            if json_rsp['code'] == -400 and '已' in json_rsp['msg']:
                return
            sleeptime = 350
            await asyncio.sleep(sleeptime)
        
        
class SignFansGroupsTask(SchedTask):
    TASK_NAME = 'sign_fans_group'
    @staticmethod
    async def check(_):
        return (-2, (0, 30)),
   
    @staticmethod
    @unique
    async def work(user):
        json_rsp = await user.req_s(SignFansGroupsReq.fetch_groups, user)
        for group in json_rsp['data']['list']:
            group_id = group['group_id']
            owner_uid = group['owner_uid']
            json_rsp = await user.req_s(SignFansGroupsReq.sign_group, user, group_id, owner_uid)
            if not json_rsp['code']:
                data = json_rsp['data']
                if data['status']:
                    user.info(f'应援团 {group_id} 已应援过')
                else:
                    user.info(f'应援团 {group_id} 应援成功,获得 {data["add_num"]} 点亲密度')
            else:
                user.info(f'应援团 {group_id} 应援失败')
            
            
class SendGiftTask(SchedTask):
    TASK_NAME = 'send_gift'
    @staticmethod
    async def check(user):
        gift_intimacy = await SendGiftTask.fetch_gift_intimacy(user)
        return (-2, (0, 30), gift_intimacy),

    @staticmethod
    async def fetch_gift_intimacy(user) -> dict:
        json_rsp = await user.req_s(SendGiftReq.fetch_gift_config, user)
        gift_intimacy = {}
        for gift in json_rsp['data']:
            if gift['bag_gift']:  # 应该这个表示是否是包裹的（错了大不了不送了，嘻嘻）
                price = gift['price']
                if price >= 100:  # 猜测小于 100 的不会增加亲密度（错了大不了不送了，嘻嘻）
                    gift_intimacy[gift['id']] = price / 100
        return gift_intimacy
        
    @staticmethod
    async def fetch_giftbags(user):
        gift_bags = await UtilsTask.fetch_giftbags(user)
        results = []
        for bag_id, gift_id, gift_num, _, _, left_time in gift_bags:
            results.append([gift_id, gift_num, bag_id, left_time])
        return results
        
    @staticmethod
    async def fetch_wearing_medal(user):
        json_rsp = await user.req_s(SendGiftReq.fetch_wearing_medal, user)
        if not json_rsp['code']:
            data = json_rsp['data']
            if data:
                room_id = data['roominfo']['room_id']
                remain_intimacy = int(data['day_limit']) - int(data['today_feed'])
                medal_name = data['medal_name']
                return room_id, remain_intimacy, medal_name
        return None
    
    @staticmethod
    async def send_expiring_gift(user, gift_intimacy: dict):
        if not user.task_ctrl['clean-expiring-gift']:
            return
        gift_bags = await SendGiftTask.fetch_giftbags(user)
        room_id = user.task_ctrl['clean-expiring-gift2room']
        time_set = user.task_ctrl['set-expiring-time']
        # filter 用过期来过滤
        expiring_giftbags = []
        for gift in gift_bags:
            left_time = gift[3]
            if left_time is not None and 0 < int(left_time) < time_set:
                expiring_giftbags.append(gift[:3])
        if expiring_giftbags:
            print('发现即将过期的礼物')
            if user.task_ctrl['clean_expiring_gift2all_medal']:
                print('正在清理过期礼物到用户勋章')
                medals = await UtilsTask.fetch_medals(user)
                expiring_giftbags = await SendGiftTask.fill_intimacy(user, expiring_giftbags, medals, gift_intimacy)
                
            print('正在清理过期礼物到指定房间')
            for gift_id, gift_num, bag_id in expiring_giftbags:
                await UtilsTask.send_gift(user, room_id, gift_num, bag_id, gift_id)
        else:
            print('未发现即将过期的礼物')
    
    @staticmethod
    async def send_medal_gift(user, gift_intimacy: dict):
        medals = []
        if user.task_ctrl['send2wearing-medal']:
            medal = await SendGiftTask.fetch_wearing_medal(user)
            if medal is None:
                print('暂未佩戴任何勋章')
            else:
                medals.append(medal)

        send2medal_by_uid = user.task_ctrl['send2medal_by_uid']
        if send2medal_by_uid:
            medals += await UtilsTask.fetch_medals(user, send2medal_by_uid)
        # print('目前的勋章', medals)
        
        print('正在投递勋章')
        gift_bags = await SendGiftTask.fetch_giftbags(user)
        # print(temp)
        send_giftbags = []
        for gift in gift_bags:
            gift_id = int(gift[0])
            left_time = gift[3]
            # 过滤某些特定礼物以及永久礼物
            if gift_id not in (4, 3, 9, 10) and left_time is not None:
                send_giftbags.append(gift[:3])
        await SendGiftTask.fill_intimacy(user, send_giftbags, medals, gift_intimacy)
        
    @staticmethod
    async def fill_intimacy(user, gift_bags, medals, gift_intimacy: dict):
        gift_bags = [list(gift) for gift in gift_bags]  # gift_bags 元素必须是 list！！！！
        for room_id, remain_intimacy, medal_name in medals:
            if not remain_intimacy:  # 剩余亲密度为 0，就跳过
                user.info(f'勋章 {medal_name} 本日亲密度上限还剩{remain_intimacy}')
            else:
                init_remain_intimacy = remain_intimacy
                for gift in gift_bags:
                    gift_id, gift_num, bag_id = gift
                    gift_price_by_giftid = gift_intimacy.get(gift_id, 0)
                    if not remain_intimacy or not gift_price_by_giftid:  # 如果是单价为 0 或者剩余 0，跳过
                        continue
                    elif gift_num * gift_price_by_giftid <= remain_intimacy:  # 即使全部送走也送不满亲密度
                        num_sent = gift_num
                    elif remain_intimacy >= gift_price_by_giftid:  # 单价小于等于剩余亲密度
                        num_sent = int(remain_intimacy / gift_price_by_giftid)
                    else:
                        continue
                    await UtilsTask.send_gift(user, room_id, num_sent, bag_id, gift_id)
                    gift[1] -= num_sent
                    remain_intimacy -= gift_price_by_giftid * num_sent

                user.info(
                    f'勋章 {medal_name} 本次提升{init_remain_intimacy-remain_intimacy}亲密度，离上限还剩{remain_intimacy}')

        return [gift for gift in gift_bags if gift[1]]  # 过滤掉送光了的礼物包
        
    @staticmethod
    @unique
    async def work(user, gift_intimacy: dict):
        await SendGiftTask.send_medal_gift(user, gift_intimacy)
        await SendGiftTask.send_expiring_gift(user, gift_intimacy)

                
class ExchangeSilverCoinTask(SchedTask):
    TASK_NAME = 'exchange_silver_coin'
    @staticmethod
    async def check(_):
        return (-2, (0, 30)),
     
    @staticmethod
    @unique
    async def work(user):
        while True:
            if not user.task_ctrl['silver2coin']:
                return
            json_rsp = await user.req_s(ExchangeSilverCoinReq.silver2coin_web, user)
            user.info(f'{json_rsp["msg"]}')
            if json_rsp['code'] == 403 and '最多' in json_rsp['msg']:
                finish_web = True
            else:
                finish_web = False
            if finish_web:
                return
            sleeptime = 350
            await asyncio.sleep(sleeptime)
