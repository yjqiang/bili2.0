import re
import json
import asyncio
import random
import utils
from bili_user.utils_user import UtilsUser
import printer
from task import Task


class DailyJobUser(UtilsUser):
    async def heartbeat(self):
        json_response = await self.online_request(self.webhub.apppost_heartbeat)
        # print(json_response)
        self.printer_with_id(['心跳包(5分钟左右间隔)'], True)
        json_response = await self.online_request(self.webhub.pcpost_heartbeat)
        # print(json_response)
        return 260
        # print(json_response)
    
    async def fetch_heart_gift(self):
        json_response = await self.online_request(self.webhub.heart_gift)
        if json_response['code'] == 400:
            self.fall_in_jail()
        return 260

    async def open_silver_box(self):
        while True:
            self.printer_with_id(["检查宝箱状态"], True)
            temp = await self.online_request(self.webhub.get_time_about_silver)
            # print (temp['code'])    #宝箱领完返回的code为-10017
            if temp['code'] == -10017:
                self.printer_with_id(["# 今日宝箱领取完毕"])
                json_rsp = None
            else:
                time_start = temp['data']['time_start']
                time_end = temp['data']['time_end']
                json_rsp = await self.online_request(self.webhub.get_silver, time_start, time_end)
            if json_rsp is None or json_rsp['code'] == -10017 or json_rsp['code'] == -800:
                sleeptime = (utils.seconds_until_tomorrow() + 300)
                return sleeptime
                break
                # await asyncio.sleep(sleeptime)
            elif not json_rsp['code']:
                self.printer_with_id(["# 打开了宝箱"])
            elif json_rsp['code'] == 400:
                self.printer_with_id(["# 宝箱开启中返回了小黑屋提示"])
                self.fall_in_jail()
                return 0
                break
            else:
                self.printer_with_id(["# 继续等待宝箱冷却..."])
                # 未来如果取消了这个东西就睡眠185s，否则精确睡眠
                # surplus里面是min，float格式
                try:
                    sleeptime = (json_rsp['data'].get('surplus', 3)) * 60 + 5
                except:
                    sleeptime = 180
                    print(json_rsp)
                return sleeptime
                break
        
    async def Daily_bag(self):
        json_response = await self.online_request(self.webhub.get_dailybag)
        # no done code
        try:
            for i in json_response['data']['bag_list']:
                self.printer_with_id(["# 获得-" + i['bag_name'] + "-成功"])
        except:
            print('hhhhhhjjjjdjdjdjddjdjdjjdjdjdjdjdjdjdjdjddjjddjjdjdjdjdj', json_response)
            printer.warn(f'{json_response}')
        return 21600
        
    # 签到功能
    async def DoSign(self):
        # -500 done
        temp = await self.online_request(self.webhub.get_dosign)
        self.printer_with_id([f'# 签到状态: {temp["msg"]}'])
        if temp['code'] == -500 and '已' in temp['msg']:
            sleeptime = (utils.seconds_until_tomorrow() + 300)
        else:
            sleeptime = 350
        return sleeptime
    
    # 领取每日任务奖励
    async def Daily_Task(self):
        # -400 done/not yet
        json_response2 = await self.online_request(self.webhub.get_dailytask)
        self.printer_with_id([f'# 双端观看直播:  {json_response2["msg"]}'])
        if json_response2['code'] == -400 and '已' in json_response2['msg']:
            sleeptime = (utils.seconds_until_tomorrow() + 300)
        else:
            sleeptime = 350
        return sleeptime
    
    async def Sign1Group(self, i1, i2):
        json_response = await self.online_request(self.webhub.assign_group, i1, i2)
        if not json_response['code']:
            if json_response['data']['status']:
                self.printer_with_id([f'# 应援团 {i1} 已应援过'])
            else:
                self.printer_with_id([f'# 应援团 {i1} 应援成功,获得 {json_response["data"]["add_num"]} 点亲密度'])
        else:
            self.printer_with_id([f'# 应援团 {i1} 应援失败'])
    
    # 应援团签到
    async def link_sign(self):
        json_rsp = await self.online_request(self.webhub.get_grouplist)
        list_check = json_rsp['data']['list']
        id_list = ((i['group_id'], i['owner_uid']) for i in list_check)
        if list_check:
            for (i1, i2) in id_list:
                asyncio.ensure_future(self.Sign1Group(i1, i2))
        return 21600
        
    async def send_latiao(self, room_id, num_wanted):
        argvs = await self.fetch_bag_list(show=False)
        sum = 0
        list_gift = []
        for i in argvs:
            left_time = i[3]
            gift_id = int(i[0])
            if (gift_id == 1) and (left_time is not None):
                list_gift.append(i[:3])
                
        for i in list_gift:
            giftID = i[0]
            giftNum = i[1]
            if num_wanted - sum >= giftNum:
                sum += int(giftNum)
                bagID = i[2]
                await self.send_gift_web(room_id, giftNum, bagID, giftID)
                self.printer_with_id([f'送出{giftNum}个辣条'], True)
            elif num_wanted - sum > 0:
                giftNum = num_wanted - sum
                sum += giftNum
                bagID = i[2]
                await self.send_gift_web(room_id, giftNum, bagID, giftID)
                self.printer_with_id([f'送出{giftNum}个辣条'], True)
        self.printer_with_id([f'一共送出{sum}个辣条'], True)
        return num_wanted - sum
    
    async def send_expiring_gift(self):
        if self.task_control['clean-expiring-gift']:
            argvs = await self.fetch_bag_list(show=False)
            roomID = self.task_control['clean-expiring-gift2room']
            time_set = self.task_control['set-expiring-time']
            list_gift = []
            for i in argvs:
                left_time = i[3]
                if left_time is not None and 0 < int(left_time) < time_set:  # 剩余时间少于半天时自动送礼
                    list_gift.append(i[:3])
            if list_gift:
                print('发现即将过期的礼物')
                if self.task_control['clean_expiring_gift2all_medal']:
                    print('正在投递其他勋章')
                    list_medal = await self.fetch_medal(show=False)
                    list_gift = await self.full_intimate(list_gift, list_medal)
                    
                print('正在清理过期礼物到指定房间')
                for i in list_gift:
                    giftID = i[0]
                    giftNum = i[1]
                    bagID = i[2]
                    await self.send_gift_web(roomID, giftNum, bagID, giftID)
            else:
                print('未发现即将过期的礼物')
        return 21600
    
    async def send_medal_gift(self):
        list_medal = []
        if self.task_control['send2wearing-medal']:
            list_medal = await self.WearingMedalInfo()
            if not list_medal:
                print('暂未佩戴任何勋章')
        if self.task_control['send2medal']:
            list_medal += await self.fetch_medal(False, self.task_control['send2medal'])
        # print(list_medal)
        print('正在投递勋章')
        temp = await self.fetch_bag_list(show=False)
        # print(temp)
        list_gift = []
        for i in temp:
            gift_id = int(i[0])
            left_time = i[3]
            if (gift_id not in [4, 3, 9, 10]) and left_time is not None:
                list_gift.append(i[:3])
        await self.full_intimate(list_gift, list_medal)
        return 21600
        
    async def auto_send_gift(self):
        await self.send_medal_gift()
        await self.send_expiring_gift()
        return 21600
    
    async def full_intimate(self, list_gift, list_medal):
        json_res = await self.online_request(self.webhub.gift_list)
        dic_gift = {j['id']: (j['price'] / 100) for j in json_res['data']}
        for roomid, left_intimate, medal_name in list_medal:
            calculate = 0
            # print(list_gift)
            for i in list_gift:
                gift_id, gift_num, bag_id = i
                # print(gift_id, bag_id)
                if (gift_num * dic_gift[gift_id] <= left_intimate):
                    pass
                elif left_intimate - dic_gift[gift_id] >= 0:
                    gift_num = int((left_intimate) / (dic_gift[gift_id]))
                else:
                    continue
                i[1] -= gift_num
                score = dic_gift[gift_id] * gift_num
                await asyncio.sleep(1.5)
                await self.send_gift_web(roomid, gift_num, bag_id, gift_id)
                calculate = calculate + score
                left_intimate = left_intimate - score
            self.printer_with_id([f'# 对{medal_name}共送出亲密度为{int(calculate)}的礼物'])
        return [i for i in list_gift if i[1]]
        
    async def doublegain_coin2silver(self):
        if self.task_control['doublegain_coin2silver']:
            json_response0 = await self.online_request(self.webhub.doublegain_coin2silver)
            json_response1 = await self.online_request(self.webhub.doublegain_coin2silver)
            print(json_response0['msg'], json_response1['msg'])
        return 21600
    
    async def sliver2coin(self):
        if self.task_control['silver2coin']:
            # 403 done
            # json_response1 = await self.online_request(self.webhub.silver2coin_app)
            # -403 done
            json_response = await self.online_request(self.webhub.silver2coin_web)
            self.printer_with_id([f'#  {json_response["msg"]}'])
            # self.printer_with_id([f'#  {json_response1["msg"]}'])
            if json_response['code'] == 403 and '最多' in json_response['msg']:
                finish_web = True
            else:
                finish_web = False
    
            
            if finish_web:
                sleeptime = (utils.seconds_until_tomorrow() + 300)
                return sleeptime
            else:
                return 350
    
        return 21600
    
    async def GetVideoExp(self, list_topvideo):
        print('开始获取视频观看经验')
        aid = random.choice(list_topvideo)
        cid = await self.GetVideoCid(aid)
        await self.online_request(self.webhub.Heartbeat, aid, cid)
    
    async def GiveCoinTask(self, coin_remain, list_topvideo):
        while coin_remain > 0:
            aid = random.choice(list_topvideo)
            rsp = await self.GiveCoin2Av(aid, 1)
            if rsp is None:
                break
            elif rsp:
                coin_remain -= 1
    
    async def GetVideoShareExp(self, list_topvideo):
        print('开始获取视频分享经验')
        aid = random.choice(list_topvideo)
        await self.online_request(self.webhub.DailyVideoShare, aid)
    
    async def BiliMainTask(self):
        login, watch_av, num, share_av = await self.GetRewardInfo()
        if self.task_control['fetchrule'] == 'bilitop':
            list_topvideo = await self.GetTopVideoList()
            # print(list_topvideo)
        else:
            list_topvideo = await self.fetch_uper_video(self.task_control['mid'])
        if (not login) or not watch_av:
            await self.GetVideoExp(list_topvideo)
        coin_sent = (num) / 10
        coin_set = min((self.task_control['givecoin']), 5)
        coin_remain = coin_set - coin_sent
        await self.GiveCoinTask(coin_remain, list_topvideo)
        if not share_av:
            await self.GetVideoShareExp(list_topvideo)
        # b站傻逼有记录延迟，3点左右成功率高一点
        return utils.seconds_until_tomorrow() + 10800
        
    async def check(self, id):
        # 3放弃
        # 2 否 voterule
        # 4 删除 votedelete
        # 1 封杀 votebreak
        text_rsp = await self.online_request(self.webhub.req_check_voted, id)
        # print(response.text)
            
        pattern = re.compile(r'\((.+)\)')
        match = pattern.findall(text_rsp)
        temp = json.loads(match[0])
        # print(temp['data']['originUrl'])
        data = temp['data']
        print(data['originContent'])
        votebreak = data['voteBreak']
        voteDelete = data['voteDelete']
        voteRule = data['voteRule']
        status = data['status']
        voted = votebreak+voteDelete+voteRule
        if voted:
            percent = voteRule / voted
        else:
            percent = 0
        print('目前已投票', voted)
        print('认为不违反规定的比例', percent)
        vote = None
        if voted >= 300:
            if percent >= 0.75:
                vote = 2
            elif percent <= 0.25:
                vote = 4
            elif 0.4 <= percent <= 0.6:
                vote = 2
        elif voted >= 150:
            if percent >= 0.9:
                vote = 2
            elif percent <= 0.1:
                vote = 4
        elif voted >= 50:
            if percent >= 0.97:
                vote = 2
            elif percent <= 0.03:
                vote = 4
        # 抬一手
        if vote is None and voted >= 400:
            vote = 2
            
        return vote, status, voted
                        
    async def judge(self):
        num_case = 0
        num_voted = 0
        while True:
            temp = await self.online_request(self.webhub.req_fetch_case)
            if not temp['code']:
                id = temp['data']['id']
            else:
                print('本次未获取到案件')
                # await asyncio.sleep(1)
                break
            num_case += 1
            while True:
                vote, status, voted = await self.check(id)
                if vote is None and status == 1:
                    if voted < 300:
                        printer.info([f'本次获取到的案件{id}暂时无法判定，在180s后重新尝试'], True)
                        await asyncio.sleep(180)
                    else:
                        printer.info([f'本次获取到的案件{id}暂时无法判定，在60s后重新尝试'], True)
                        await asyncio.sleep(60)
                else:
                    break
            if status != 1:
                print('超时失败，请联系作者')
            else:
                print('投票决策', id, vote)
                json_rsp = await self.online_request(self.webhub.req_vote_case, id, vote)
                if not json_rsp['code']:
                    print(f'投票{id}成功')
                    num_voted += 1
                else:
                    print(f'投票{id}失败，请反馈作者')
            
            print('______________________________')
            # await asyncio.sleep(1)
        
        self.printer_with_id([f'风纪委员会共获取{num_case}件案例，其中有效投票{num_voted}件'], True)
        return 3600

    async def daily_task(self, task_name):
        time_delay = await getattr(self, task_name)()
        time_delay += random.uniform(0, 30)
        Task().call_after('daily_task', time_delay, (task_name,), self.user_id)
