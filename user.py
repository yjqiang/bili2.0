from web_hub import WebHub, HostWebHub
from task import RaffleHandler, Task
from config_loader import ConfigLoader
import asyncio
import time
import rsa
import base64
from urllib import parse
from statistic import Statistics
import printer
import random
import re
from operator import itemgetter
import json
from PIL import Image
from io import BytesIO
import utils


class User():
    def __init__(self, user_id, dict_user, dict_bili, task_control, high_concurency):
        if high_concurency:
            self.webhub = HostWebHub(user_id, dict_user, dict_bili)
        else:
            self.webhub = WebHub(user_id, dict_user, dict_bili)
        self.statistics = Statistics()
        self.user_id = user_id
        self.user_name = dict_user['username']
        self.task_control = task_control
        if not dict_user['cookie']:
            self.login(dict_user['username'], dict_user['password'])
            
    def printer_with_id(self, list_msg, tag_time=False):
        list_msg[0] += f'(用户id:{self.user_id}  用户名:{self.user_name})'
        printer.info(list_msg, tag_time)
        
    def login(self, username, password):
        response = self.webhub.fetch_key()
        value = response.json()['data']
        key = value['key']
        Hash = str(value['hash'])
        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(key.encode())
        hashed_password = base64.b64encode(rsa.encrypt((Hash + password).encode('utf-8'), pubkey))
        url_password = parse.quote_plus(hashed_password)
        url_username = parse.quote_plus(username)
        
        response = self.webhub.normal_login(url_username, url_password)
        
        while response.json()['code'] == -105:
            response = self.webhub.captcha_login(url_username, url_password)
        json_rsp = response.json()
        # print(json_rsp)
        if not json_rsp['code'] and not json_rsp['data']['status']:
            data = json_rsp['data']
            access_key = data['token_info']['access_token']
            refresh_token = data['token_info']['refresh_token']
            cookie = data['cookie_info']['cookies']
            generator_cookie = (f'{i["name"]}={i["value"]}' for i in cookie)
            cookie_format = ';'.join(generator_cookie)
            dic_saved_session = {
                'csrf': cookie[0]['value'],
                'access_key': access_key,
                'refresh_token': refresh_token,
                'cookie': cookie_format,
                'uid': cookie[1]['value']
                }
            # print(dic_saved_session)
            
            self.write_user(dic_saved_session)
            print("[{}] {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), '密码登陆成功'))
            return True
            
        else:
            print("[{}] 登录失败,错误信息为:{}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), json_rsp))
            return False
            
    def fall_in_jail(self):
        RaffleHandler().remove(self.user_id)
        Task().remove(self.user_id)
        self.printer_with_id([f'抽奖脚本检测{self.user_id}为小黑屋'], True)
                
    def write_user(self, dict_new):
        self.webhub.set_status(dict_new)
        ConfigLoader().write_user(dict_new, self.user_id)
        
    async def get_statistic(self):
        await asyncio.sleep(0)
        self.statistics.getlist()
        self.statistics.getresult()
         
    async def heartbeat(self):
        json_response = await self.webhub.apppost_heartbeat()
        # print(json_response)
        self.printer_with_id(['心跳包(5分钟左右间隔)'], True)
        json_response = await self.webhub.pcpost_heartbeat()
        # print(json_response)
        json_response = await self.webhub.heart_gift()
        if json_response['code'] == 400:
            self.fall_in_jail()
        return 260
        # print(json_response)

    async def open_silver_box(self):
        while True:
            self.printer_with_id(["检查宝箱状态"], True)
            temp = await self.webhub.get_time_about_silver()
            # print (temp['code'])    #宝箱领完返回的code为-10017
            if temp['code'] == -10017:
                self.printer_with_id(["# 今日宝箱领取完毕"])
                json_rsp = None
            else:
                time_start = temp['data']['time_start']
                time_end = temp['data']['time_end']
                json_rsp = await self.webhub.get_silver(time_start, time_end)
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
                
    async def handle_1_substantial_raffle(self, i, g):
        json_response1 = await self.webhub.get_gift_of_lottery(i, g)
        print("当前时间:", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        print("参与实物抽奖回显：", json_response1)
        
    async def check_tv_result(self, raffleid, real_roomid):
        json_response = await self.webhub.get_TV_result(real_roomid, raffleid)
        # print(json_response)
        if not json_response['code']:
            # {'code': 0, 'msg': '正在抽奖中..', 'message': '正在抽奖中..', 'data': {'gift_id': '-1', 'gift_name': '', 'gift_num': 0, 'gift_from': '', 'gift_type': 0, 'gift_content': '', 'status': 3}}
            if json_response['data']['gift_id'] == '-1':
                print([f'json_response'], True)
                return
            elif json_response['data']['gift_id'] != '-1':
                data = json_response['data']
                self.printer_with_id([f'# 房间{real_roomid:^9}道具抽奖结果: {data["gift_name"]}X{data["gift_num"]}'], True)
                self.statistics.add_to_result(data['gift_name'], int(data['gift_num']))
        
    async def handle_1_TV_raffle(self, real_roomid, raffleid, raffle_type):
        print('参与', raffleid)
        json_response2 = await self.webhub.get_gift_of_TV(real_roomid, raffleid)
        self.statistics.append_to_TVlist()
        self.printer_with_id([f'参与了房间{real_roomid:^9}的道具抽奖'], True)
        self.printer_with_id([f'# 道具抽奖状态: {json_response2["msg"]}'])
        # -400不存在
        # -500繁忙
        code = json_response2['code']
        if not code:
            # Statistics.append_to_TVlist(raffleid, real_roomid)
            Task().call_after('check_tv_result', 190, (raffleid, real_roomid), id=self.user_id)
            return True
        elif code == -500:
            print('# -500繁忙，稍后重试')
            return False
        elif code == 400:
            self.fall_in_jail()
            return False
        else:
            print(json_response2)
            return True
                
    async def handle_1_captain_raffle(self, roomid, raffleid):
        self.statistics.append_to_captainlist()
        json_response2 = await self.webhub.get_gift_of_captain(roomid, raffleid)
        if not json_response2['code']:
            print("# 获取到房间 %s 的总督奖励: " % (roomid), json_response2['data']['message'])
            # print(json_response2)
            self.statistics.append_to_captainlist()
        else:
            print(json_response2)
        return True
                                                
    async def handle_1_activity_raffle(self, text1, text2, raffleid):
        # print('参与')
        json_response1 = await self.webhub.get_gift_of_events_app(text1, text2, raffleid)
        json_pc_response = await self.webhub.get_gift_of_events_web(text1, text2, raffleid)
        
        self.printer_with_id([f'参与了房间{text1:^9}的活动抽奖'], True)
    
        if not json_response1['code']:
            self.printer_with_id([f'# 移动端活动抽奖结果: {json_response1["data"]["gift_desc"]}'])
            self.statistics.add_to_result(*(json_response1['data']['gift_desc'].split('X')))
        else:
            print(json_response1)
            self.printer_with_id([f'# 移动端活动抽奖结果: {json_response1}'])
            
        self.printer_with_id(
                [f'# 网页端活动抽奖状态:  {json_pc_response}'])
        if not json_pc_response['code']:
            self.statistics.append_to_activitylist()
        else:
            print(json_pc_response)
        return True
    
    async def post_watching_history(self, roomid):
        print('进入', roomid)
        await self.webhub.post_watching_history(roomid)
    
    async def handle_1_room_activity(self, text1, text2):
        result = True
        if result:
            json_response = await self.webhub.get_giftlist_of_events(text1)
            checklen = json_response['data']
            list_available_raffleid = []
            for j in checklen:
                # await asyncio.sleep(random.uniform(0.5, 1))
                # resttime = j['time']
                raffleid = j['raffleId']
                # if self.statistics.check_activitylist(text1, raffleid):
                #    list_available_raffleid.append(raffleid)
                list_available_raffleid.append(raffleid)
            tasklist = []
            for raffleid in list_available_raffleid:
                task = asyncio.ensure_future(self.handle_1_activity_raffle(text1, text2, raffleid))
                tasklist.append(task)
            if tasklist:
                raffle_results = await asyncio.gather(*tasklist)
                if False in raffle_results:
                    print('有繁忙提示，稍后重新尝试')
                    RaffleHandler().Put2Queue((text1, text2), 'handle_1_room_activity', self.user_id)
                                    
    async def fetch_capsule_info(self):
        json_response = await self.webhub.fetch_capsule()
        # print(json_response)
        if not json_response['code']:
            data = json_response['data']
            if data['colorful']['status']:
                print(f'梦幻扭蛋币: {data["colorful"]["coin"]}个')
            else:
                print('梦幻扭蛋币暂不可用')
    
            data = json_response['data']
            if data['normal']['status']:
                print(f'普通扭蛋币: {data["normal"]["coin"]}个')
            else:
                print('普通扭蛋币暂不可用')
    
    async def open_capsule(self, count):
        json_response = await self.webhub.open_capsule(count)
        # print(json_response)
        if not json_response['code']:
            # print(json_response['data']['text'])
            for i in json_response['data']['text']:
                print(i)
    
    async def fetch_user_info(self):
        json_response = await self.webhub.fetch_user_info()
        json_response_ios = await self.webhub.fetch_user_infor_ios()
        print('[{}] 查询用户信息'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
        if not json_response_ios['code']:
            gold_ios = json_response_ios['data']['gold']
        # print(json_response_ios)
        if not json_response['code']:
            data = json_response['data']
            # print(data)
            userInfo = data['userInfo']
            userCoinIfo = data['userCoinIfo']
            uname = userInfo['uname']
            achieve = data['achieves']
            user_level = userCoinIfo['user_level']
            silver = userCoinIfo['silver']
            gold = userCoinIfo['gold']
            identification = bool(userInfo['identification'])
            mobile_verify = bool(userInfo['mobile_verify'])
            user_next_level = userCoinIfo['user_next_level']
            user_intimacy = userCoinIfo['user_intimacy']
            user_next_intimacy = userCoinIfo['user_next_intimacy']
            user_level_rank = userCoinIfo['user_level_rank']
            billCoin = userCoinIfo['coins']
            bili_coins = userCoinIfo['bili_coins']
            print('# 用户名', uname)
            size = 100, 100
            response_face = await self.webhub.load_img(userInfo['face'])
            img = Image.open(BytesIO(await response_face.read()))
            img.thumbnail(size)
            try:
                img.show()
            except:
                pass
            print(f'# 手机认证状况 {mobile_verify} | 实名认证状况 {identification}')
            print('# 银瓜子', silver)
            print('# 通用金瓜子', gold)
            print('# ios可用金瓜子', gold_ios)
            print('# 硬币数', billCoin)
            print('# b币数', bili_coins)
            print('# 成就值', achieve)
            print('# 等级值', user_level, '———>', user_next_level)
            print('# 经验值', user_intimacy)
            print('# 剩余值', user_next_intimacy - user_intimacy)
            arrow = int(user_intimacy * 30 / user_next_intimacy)
            line = 30 - arrow
            percent = user_intimacy / user_next_intimacy * 100.0
            process_bar = '# [' + '>' * arrow + '-' * line + ']' + '%.2f' % percent + '%'
            print(process_bar)
            print('# 等级榜', user_level_rank)
    
    async def fetch_bag_list(self, verbose=False, bagid=None, show=True):
        json_response = await self.webhub.fetch_bag_list()
        gift_list = []
        # print(json_response)
        if show:
            print('[{}] 查询可用礼物'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
        for i in json_response['data']['list']:
            bag_id = i['bag_id']
            gift_id = i['gift_id']
            gift_num = i['gift_num']
            gift_name = i['gift_name']
            expireat = i['expire_at']
            left_time = (expireat - json_response['data']['time'])
            if not expireat:
                left_days = '+∞'.center(6)
                left_time = None
            else:
                left_days = round(left_time / 86400, 1)
            if bagid is not None:
                if bag_id == int(bagid):
                    return gift_id, gift_num
            else:
                if verbose:
                    print(f'# 编号为{bag_id}的{gift_name:^3}X{gift_num:^4} (在{left_days:^6}天后过期)')
                elif show:
                    print(f'# {gift_name:^3}X{gift_num:^4} (在{left_days:^6}天后过期)')
    
            gift_list.append([gift_id, gift_num, bag_id, left_time])
        # print(gift_list)
        return gift_list
    
    async def check_taskinfo(self):
        json_response = await self.webhub.check_taskinfo()
        # print(json_response)
        if not json_response['code']:
            data = json_response['data']
            double_watch_info = data['double_watch_info']
            box_info = data['box_info']
            sign_info = data['sign_info']
            live_time_info = data['live_time_info']
            print('双端观看直播：')
            if double_watch_info['status'] == 1:
                print('# 该任务已完成，但未领取奖励')
            elif double_watch_info['status'] == 2:
                print('# 该任务已完成，已经领取奖励')
            else:
                print('# 该任务未完成')
                if double_watch_info['web_watch'] == 1:
                    print('## 网页端观看任务已完成')
                else:
                    print('## 网页端观看任务未完成')
    
                if double_watch_info['mobile_watch'] == 1:
                    print('## 移动端观看任务已完成')
                else:
                    print('## 移动端观看任务未完成')
    
            print('直播在线宝箱：')
            if box_info['status'] == 1:
                print('# 该任务已完成')
            else:
                print('# 该任务未完成')
                print(f'## 一共{box_info["max_times"]}次重置次数，当前为第{box_info["freeSilverTimes"]}次第{box_info["type"]}个礼包(每次3个礼包)')
    
            print('每日签到：')
            if sign_info['status'] == 1:
                print('# 该任务已完成')
            else:
                print('# 该任务未完成')
    
            if sign_info['signDaysList'] == list(range(1, sign_info['curDay'] + 1)):
                print('# 当前全勤')
            else:
                print('# 出现断签')
    
            print('直播奖励：')
            if live_time_info['status'] == 1:
                print('# 已完成')
            else:
                print('# 未完成(目前本项目未实现自动完成直播任务)')
    
    async def check_room(self, roomid):
        json_response = await self.webhub.check_room(roomid)
        if not json_response['code']:
            # print(json_response)
            print('查询结果:')
            data = json_response['data']
    
            if not data['short_id']:
                print('# 此房间无短房号')
            else:
                print(f'# 短号为:{data["short_id"]}')
            print(f'# 真实房间号为:{data["room_id"]}')
            return data['room_id']
        # 房间不存在
        elif json_response['code'] == 60004:
            print(json_response['msg'])
    
    async def send_gift_web(self, roomid, num_wanted, bagid, giftid=None):
        if giftid is None:
            giftid, num_owned = await self.fetch_bag_list(False, bagid)
            num_wanted = min(num_owned, num_wanted)
        json_response = await self.webhub.check_room(roomid)
        ruid = json_response['data']['uid']
        biz_id = json_response['data']['room_id']
        # 200027 不足数目
        json_response1 = await self.webhub.send_gift_web(giftid, num_wanted, bagid, ruid, biz_id)
        if not json_response1['code']:
            # print(json_response1['data'])
            print(f'# 送出礼物: {json_response1["data"]["gift_name"]}X{json_response1["data"]["gift_num"]}')
        else:
            print("# 错误", json_response1['msg'])
    
    async def fetch_liveuser_info(self, real_roomid):
        json_response = await self.webhub.fetch_liveuser_info(real_roomid)
        if not json_response['code']:
            data = json_response['data']
            # print(data)
            print(f'# 主播姓名 {data["info"]["uname"]}')
    
            uid = data['level']['uid']  # str
            json_response_fan = await self.webhub.fetch_fan(real_roomid, uid)
            # print(json_response_fan)
            data_fan = json_response_fan['data']
            if not json_response_fan['code'] and data_fan['medal']['status'] == 2:
                print(f'# 勋章名字: {data_fan["list"][0]["medal_name"]}')
            else:
                print('# 该主播暂时没有开通勋章')  # print(json_response_fan)
    
            size = 100, 100
            response_face = await self.webhub.load_img(data['info']['face'])
            img = Image.open(BytesIO(await response_face.read()))
            img.thumbnail(size)
            try:
                img.show()
            except:
                pass
        
    async def GiveCoin2Av(self, video_id, num):
        if num not in (1, 2):
            return False
        # 10004 稿件已经被删除
        # 34005 超过，满了
        # -104 不足硬币
        json_rsp = await self.webhub.ReqGiveCoin2Av(video_id, num)
        code = json_rsp['code']
        if not code:
            print(f'给视频av{video_id}投{num}枚硬币成功')
            return True
        else:
            print('投币失败', json_rsp)
            if code == -104 or code == -102:
                return None
            return False
    
    async def GetTopVideoList(self):
        text_rsp = await self.webhub.req_fetch_av()
        # print(text_rsp)
        list_av = re.findall(r'(?<=www.bilibili.com/video/av)\d+(?=/)', text_rsp)
        list_av = list(set(list_av))
        return list_av
    
    async def fetch_uper_video(self, list_mid):
        list_av = []
        for mid in list_mid:
            json_rsp = await self.webhub.req_fetch_uper_video(mid, 1)
            # print(json_rsp)
            data = json_rsp['data']
            pages = data['pages']
            if data['vlist']:
                list_av += [av['aid'] for av in data['vlist']]
            for page in range(2, pages + 1):
                json_rsp = await self.webhub.req_fetch_uper_video(mid, page)
                # print(json_rsp)
                data = json_rsp['data']
                list_av += [av['aid'] for av in data['vlist']]
        # print(len(list_av), list_av)
        return list_av
    
    async def GetVideoCid(self, video_aid):
        json_rsp = await self.webhub.ReqVideoCid(video_aid)
        # print(json_rsp[0]['cid'])
        return (json_rsp[0]['cid'])
    
    async def GetRewardInfo(self, show=True):
        json_rsp = await self.webhub.ReqMasterInfo()
        login = json_rsp['login']
        watch_av = json_rsp['watch_av']
        coins_av = json_rsp['coins_av']
        share_av = json_rsp['share_av']
        level_info = json_rsp["level_info"]
        current_exp = level_info['current_exp']
        next_exp = level_info['next_exp']
        if next_exp == -1:
            next_exp = current_exp
        print(f'# 主站等级值 {level_info["current_level"]}')
        print(f'# 主站经验值 {level_info["current_exp"]}')
        print(f'# 主站剩余值 {- current_exp + next_exp}')
        arrow = int(current_exp * 30 / next_exp)
        line = 30 - arrow
        percent = current_exp / next_exp * 100.0
        process_bar = '# [' + '>' * arrow + '-' * line + ']' + '%.2f' % percent + '%'
        print(process_bar)
        if show:
            print(f'每日登陆：{login} 每日观看：{watch_av} 每日投币经验：{coins_av}/50 每日分享：{share_av}')
        return login, watch_av, coins_av, share_av
                        
    async def WearingMedalInfo(self):
        json_response = await self.webhub.ReqWearingMedal()
        if not json_response['code']:
            data = json_response['data']
            if data:
                return [(data['roominfo']['room_id'],  int(data['day_limit']) - int(data['today_feed']), data['medal_name']), ]
            else:
                # print('暂无佩戴任何勋章')
                return []
    
            # web api返回值信息少
    
    async def TitleInfo(self):
        json_response = await self.webhub.ReqTitleInfo()
        # print(json_response)
        if not json_response['code']:
            data = json_response['data']
            for i in data['list']:
                if i['level']:
                    max = i['level'][1]
                else:
                    max = '-'
                print(i['activity'], i['score'], max)
    
    async def fetch_medal(self, show=True, list_wanted_medal=[]):
        printlist = []
        list_medal = []
        if show:
            printlist.append('查询勋章信息')
            printlist.append(
                '{} {} {:^12} {:^10} {} {:^6} '.format(utils. adjust_for_chinese('勋章'), utils. adjust_for_chinese('主播昵称'), '亲密度',
                                                       '今日的亲密度', utils. adjust_for_chinese('排名'), '勋章状态'))
        dic_worn = {'1': '正在佩戴', '0': '待机状态'}
        json_response = await self.webhub.fetchmedal()
        # print(json_response)
        if not json_response['code']:
            for i in json_response['data']['fansMedalList']:
                list_medal.append((i['roomid'], int(i['dayLimit']) - int(i['todayFeed']), i['medal_name'], i['level']))
                if show:
                    printlist.append(
                        '{} {} {:^14} {:^14} {} {:^6} '.format(utils. adjust_for_chinese(i['medal_name'] + '|' + str(i['level'])),
                                                               utils. adjust_for_chinese(i['anchorInfo']['uname']),
                                                               str(i['intimacy']) + '/' + str(i['next_intimacy']),
                                                               str(i['todayFeed']) + '/' + str(i['dayLimit']),
                                                               utils. adjust_for_chinese(str(i['rank'])),
                                                               dic_worn[str(i['status'])]))
            if show:
                self.printer_with_id(printlist, True)
            if list_wanted_medal:
                list_return_medal = []
                for roomid in list_wanted_medal:
                    for i in list_medal:
                        if i[0] == roomid:
                            list_return_medal.append(i[:3])
                            break
            else:
                list_return_medal = [i[:3] for i in sorted(list_medal, key=itemgetter(3), reverse=True)]
            return list_return_medal
    
    async def send_danmu_msg_web(self, msg, roomId):
        json_response = await self.webhub.send_danmu_msg_web(msg, roomId)
        print(json_response)
                                    
    async def Daily_bag(self):
        json_response = await self.webhub.get_dailybag()
        # no done code
        for i in json_response['data']['bag_list']:
            self.printer_with_id(["# 获得-" + i['bag_name'] + "-成功"])
        return 21600
        
    # 签到功能
    async def DoSign(self):
        # -500 done
        temp = await self.webhub.get_dosign()
        self.printer_with_id([f'# 签到状态: {temp["msg"]}'])
        if temp['code'] == -500 and '已' in temp['msg']:
            sleeptime = (utils.seconds_until_tomorrow() + 300)
        else:
            sleeptime = 350
        return sleeptime
    
    # 领取每日任务奖励
    async def Daily_Task(self):
        # -400 done/not yet
        json_response2 = await self.webhub.get_dailytask()
        self.printer_with_id([f'# 双端观看直播:  {json_response2["msg"]}'])
        if json_response2['code'] == -400 and '已' in json_response2['msg']:
            sleeptime = (utils.seconds_until_tomorrow() + 300)
        else:
            sleeptime = 350
        return sleeptime
    
    async def Sign1Group(self, i1, i2):
        json_response = await self.webhub.assign_group(i1, i2)
        if not json_response['code']:
            if json_response['data']['status']:
                self.printer_with_id([f'# 应援团 {i1} 已应援过'])
            else:
                self.printer_with_id([f'# 应援团 {i1} 应援成功,获得 {json_response["data"]["add_num"]} 点亲密度'])
        else:
            self.printer_with_id([f'# 应援团 {i1} 应援失败'])
    
    # 应援团签到
    async def link_sign(self):
        json_rsp = await self.webhub.get_grouplist()
        list_check = json_rsp['data']['list']
        id_list = ((i['group_id'], i['owner_uid']) for i in list_check)
        if list_check:
            tasklist = []
            for (i1, i2) in id_list:
                task = asyncio.ensure_future(self.Sign1Group(i1, i2))
                tasklist.append(task)
            results = await asyncio.gather(*tasklist)
        return 21600
    
    async def send_gift(self):
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
    
    async def auto_send_gift(self):
        # await utils.WearingMedalInfo()
        # return
        list_medal = []
        if self.task_control['send2wearing-medal']:
            list_medal = await self.WearingMedalInfo()
            if not list_medal:
                print('暂未佩戴任何勋章')
                # await BiliTimer.append2list_jobs(auto_send_gift, 21600)
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
                
        # self.printer_with_id(["# 自动送礼共送出亲密度为%s的礼物" % int(calculate)])
        return 21600
    
    async def full_intimate(self, list_gift, list_medal):
        json_res = await self.webhub.gift_list()
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
            json_response0 = await self.webhub.doublegain_coin2silver()
            json_response1 = await self.webhub.doublegain_coin2silver()
            print(json_response0['msg'], json_response1['msg'])
        return 21600
    
    async def sliver2coin(self):
        if self.task_control['silver2coin']:
            # 403 done
            json_response1 = await self.webhub.silver2coin_app()
            # -403 done
            json_response = await self.webhub.silver2coin_web()
            self.printer_with_id([f'#  {json_response["msg"]}'])
            self.printer_with_id([f'#  {json_response1["msg"]}'])
            if json_response['code'] == -403 and '只' in json_response['msg']:
                finish_web = True
            else:
                finish_web = False
    
            if json_response1['code'] == 403 and '最多' in json_response1['msg']:
                finish_app = True
            else:
                finish_app = False
            if finish_app and finish_web:
                sleeptime = (utils.seconds_until_tomorrow() + 300)
                return sleeptime
                return
            else:
                return 350
                return
    
        return 21600
    
    async def GetVideoExp(self, list_topvideo):
        print('开始获取视频观看经验')
        aid = list_topvideo[random.randint(0, 19)]
        cid = await self.GetVideoCid(aid)
        await self.webhub.Heartbeat(aid, cid)
    
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
        aid = list_topvideo[random.randint(0, 19)]
        await self.webhub.DailyVideoShare(aid)
    
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
        text_rsp = await self.webhub.req_check_voted(id)
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
            temp = await self.webhub.req_fetch_case()
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
                json_rsp = await self.webhub.req_vote_case(id, vote)
                if not json_rsp['code']:
                    print(f'投票{id}成功')
                    num_voted += 1
                else:
                    print(f'投票{id}失败，请反馈作者')
            
            print('______________________________')
            # await asyncio.sleep(1)
        
        self.printer_with_id([f'风纪委员会共获取{num_case}件案例，其中有效投票{num_voted}件'], True)
        return 3600

    async def update(self, func, value):
        return await getattr(self, func)(*value)
        
    async def daily_task(self, task_name):
        time_delay = await getattr(self, task_name)()
        time_delay += random.uniform(0, 30)
        Task().call_after('daily_task', time_delay, (task_name,), self.user_id)
        
