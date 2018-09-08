import sys
import hashlib
import time
import requests
import base64
import aiohttp
import asyncio
import random
import copy
import json
from cdn import Host


def CurrentTime():
    currenttime = int(time.time())
    return str(currenttime)


def randomint():
    return ''.join(str(random.randint(0, 9)) for _ in range(17))


def cnn_captcha(img):
    url = "http://47.95.255.188:5000/code"
    data = {"image": img}
    rsp = requests.post(url, data=data)
    captcha = rsp.text
    print(f'此次登录出现验证码,识别结果为{captcha}')
    return captcha


class WebHub():
    base_url = 'https://api.live.bilibili.com'
    
    def __init__(self, id, dict_new, dict_bili):
        self.dict_bili = copy.deepcopy(dict_bili)
        self.set_status(dict_new)
        self.bili_session = None
        self.var_other_session = None
        if dict_bili:
            self.app_params = f'actionKey={dict_bili["actionKey"]}&appkey={dict_bili["appkey"]}&build={dict_bili["build"]}&device={dict_bili["device"]}&mobi_app={dict_bili["mobi_app"]}&platform={dict_bili["platform"]}'
    
    def set_status(self, dict_new):
        for i, value in dict_new.items():
            self.dict_bili[i] = value
            if i == 'cookie':
                self.dict_bili['pcheaders']['cookie'] = value
                self.dict_bili['appheaders']['cookie'] = value
    
    def print_status(self):
        print(self.dict_bili)
        
    @property
    def bili_section(self):
        if self.bili_session is None:
            self.bili_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2.5))
            # print(0)
        return self.bili_session
        
    @property
    def other_session(self):
        if self.var_other_session is None:
            self.var_other_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2.5))
            # print(0)
        return self.var_other_session

    def calc_sign(self, str):
        str = f'{str}{self.dict_bili["app_secret"]}'
        hash = hashlib.md5()
        hash.update(str.encode('utf-8'))
        sign = hash.hexdigest()
        return sign
        
    async def get_json_rsp(self, rsp, url):
        if rsp.status == 200:
            # json_response = await response.json(content_type=None)
            data = await rsp.read()
            json_rsp = json.loads(data)
            if isinstance(json_rsp, dict) and 'code' in json_rsp:
                code = json_rsp['code']
                if code == 1024:
                    print('b站炸了，暂停所有请求1.5s后重试，请耐心等待')
                    await asyncio.sleep(1.5)
                    return None
                elif code == 3 or code == -401 or code == 1003 or code == -101:
                    print('api错误，稍后重试，请反馈给作者')
                    await asyncio.sleep(1)
                    return 3
            return json_rsp
        elif rsp.status == 403:
            print('403频繁', url)
        return None
        
    async def get_text_rsp(self, rsp, url):
        if rsp.status == 200:
            return await rsp.text()
        elif rsp.status == 403:
            print('403频繁', url)
        return None

    async def bili_section_post(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.bili_section.post(url, headers=headers, data=data, params=params) as response:
                    json_rsp = await self.get_json_rsp(response, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue

    async def other_session_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.other_session.get(url, headers=headers, data=data, params=params) as response:
                    json_rsp = await self.get_json_rsp(response, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
                
    async def other_session_post(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.other_session.post(url, headers=headers, data=data, params=params) as response:
                    json_rsp = await self.get_json_rsp(response, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue

    async def bili_section_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.bili_section.get(url, headers=headers, data=data, params=params) as response:
                    json_rsp = await self.get_json_rsp(response, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
                
    async def session_text_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.other_session.get(url, headers=headers, data=data, params=params) as response:
                    text_rsp = await self.get_text_rsp(response, url)
                    if text_rsp is not None:
                        return text_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue

    async def playurl(self, cid):
        # cid real_roomid
        # url = 'http://api.live.bilibili.com/room/v1/Room/playUrl?'
        url = f'{self.base_url}/api/playurl?device=phone&platform=ios&scale=3&build=10000&cid={cid}&otype=json&platform=h5'
        response = await self.bili_section_get(url)
        return response

    async def search_liveuser(self, name):
        search_url = f'https://search.bilibili.com/api/search?search_type=live_user&keyword={name}&page=1'
        json_rsp = await self.other_session_get(search_url)
        return json_rsp

    async def search_biliuser(self, name):
        search_url = f"https://search.bilibili.com/api/search?search_type=bili_user&keyword={name}"
        json_rsp = await self.other_session_get(search_url)
        return json_rsp

    async def fetch_capsule(self):
        url = f"{self.base_url}/api/ajaxCapsule"
        response = await self.bili_section_get(url, headers=self.dict_bili['pcheaders'])
        return response

    async def open_capsule(self, count):
        url = f"{self.base_url}/api/ajaxCapsuleOpen"
        data = {
            'type': 'normal',
            "count": count,
            "csrf_token": self.dict_bili['csrf']
        }
        response = await self.bili_section_post(url, data=data, headers=self.dict_bili['pcheaders'])
        return response

    def logout(self):
        url = 'https://passport.bilibili.com/login?act=exit'
        response = requests.get(url, headers=self.dict_bili['pcheaders'])
        return response

    # 1:900兑换
    async def doublegain_coin2silver(self):
        # url: "/exchange/coin2silver",
        data = {'coin': 10}
        url = f"{self.base_url}/exchange/coin2silver"
        response = await self.bili_section_post(url, data=data, headers=self.dict_bili['pcheaders'])
        return response

    async def post_watching_history(self, room_id):
        data = {
            "room_id": room_id,
            "csrf_token": self.dict_bili['csrf']
        }
        url = f"{self.base_url}/room/v1/Room/room_entry_action"
        response = await self.bili_section_post(url, data=data, headers=self.dict_bili['pcheaders'])
        return response
    
    async def silver2coin_web(self):
        url = f"{self.base_url}/exchange/silver2coin"
        response = await self.bili_section_post(url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def silver2coin_app(self):
        temp_params = f'access_key={self.dict_bili["access_key"]}&{self.app_params}&ts={CurrentTime()}'
        sign = self.calc_sign(temp_params)
        app_url = f"{self.base_url}/AppExchange/silver2coin?{temp_params}&sign={sign}"
        response1 = await self.bili_section_post(app_url, headers=self.dict_bili['appheaders'])
        return response1
    
    async def fetch_fan(self, real_roomid, uid):
        url = f'{self.base_url}/rankdb/v1/RoomRank/webMedalRank?roomid={real_roomid}&ruid={uid}'
        response = await self.bili_section_get(url)
        return response
    
    async def check_room(self, roomid):
        url = f"{self.base_url}/room/v1/Room/room_init?id={roomid}"
        response = await self.bili_section_get(url)
        return response
    
    async def fetch_bag_list(self):
        url = f"{self.base_url}/gift/v2/gift/bag_list"
        response = await self.bili_section_get(url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def check_taskinfo(self):
        url = f'{self.base_url}/i/api/taskInfo'
        response = await self.bili_section_get(url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def send_gift_web(self, giftid, giftnum, bagid, ruid, biz_id):
        url = f"{self.base_url}/gift/v2/live/bag_send"
        data = {
            'uid': self.dict_bili['uid'],
            'gift_id': giftid,
            'ruid': ruid,
            'gift_num': giftnum,
            'bag_id': bagid,
            'platform': 'pc',
            'biz_code': 'live',
            'biz_id': biz_id,
            'rnd': CurrentTime(),
            'storm_beat_id': '0',
            'metadata': '',
            'price': '0',
            'csrf_token': self.dict_bili['csrf']
        }
        response = await self.bili_section_post(url, headers=self.dict_bili['pcheaders'], data=data)
        return response
    
    async def fetch_user_info(self):
        url = f"{self.base_url}/i/api/liveinfo"
        response = await self.bili_section_get(url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def fetch_user_infor_ios(self):
        temp_params = f'access_key={self.dict_bili["access_key"]}&platform=ios'
        url = f'{self.base_url}/mobile/getUser?{temp_params}'
        response = await self.bili_section_get(url)
        return response
    
    async def fetch_liveuser_info(self, real_roomid):
        url = f'{self.base_url}/live_user/v1/UserInfo/get_anchor_in_room?roomid={real_roomid}'
        response = await self.bili_section_get(url)
        return response
    
    async def load_img(self, url):
        return await self.other_session.get(url)
    
    async def send_danmu_msg_web(self, msg, roomId):
        url = f'{self.base_url}/msg/send'
        data = {
            'color': '16777215',
            'fontsize': '25',
            'mode': '1',
            'msg': msg,
            'rnd': '0',
            'roomid': int(roomId),
            'csrf_token': self.dict_bili['csrf']
        }

        response = await self.bili_section_post(url, headers=self.dict_bili['pcheaders'], data=data)
        return response
    
    async def fetchmedal(self):
        url = f'{self.base_url}/i/api/medal?page=1&pageSize=50'
        response = await self.bili_section_post(url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def ReqWearingMedal(self):
        url = f'{self.base_url}/live_user/v1/UserInfo/get_weared_medal'
        data = {
            'uid': self.dict_bili['uid'],
            'csrf_token': ''
        }
        response = await self.bili_section_post(url, data=data, headers=self.dict_bili['pcheaders'])
        return response

    async def ReqTitleInfo(self):
        temp_params = f'access_key={self.dict_bili["access_key"]}&{self.app_params}'
        sign = self.calc_sign(temp_params)
        url = f'{self.base_url}/appUser/myTitleList?{temp_params}&sign={sign}'
        response = await self.bili_section_get(url, headers=self.dict_bili['appheaders'])
        return response

    def fetch_key(self):
        url = 'https://passport.bilibili.com/api/oauth2/getKey'
        temp_params = f'appkey={self.dict_bili["appkey"]}'
        sign = self.calc_sign(temp_params)
        params = {'appkey': self.dict_bili['appkey'], 'sign': sign}
        response = requests.post(url, data=params)
        return response

    def normal_login(self, username, password):
        url = "https://passport.bilibili.com/api/v2/oauth2/login"
        temp_params = f'appkey={self.dict_bili["appkey"]}&password={password}&username={username}'
        sign = self.calc_sign(temp_params)
        payload = f'appkey={self.dict_bili["appkey"]}&password={password}&username={username}&sign={sign}'
        response = requests.post(url, params=payload)
        return response

    def captcha_login(self, username, password):
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
            'Host': 'passport.bilibili.com',
            'cookie': "sid=hxt5szbb"
        }
        with requests.Session() as s:
            url = "https://passport.bilibili.com/captcha"
            res = s.get(url, headers=headers)
            tmp1 = base64.b64encode(res.content)
    
            captcha = cnn_captcha(tmp1)
            temp_params = f'actionKey={self.dict_bili["actionKey"]}&appkey={self.dict_bili["appkey"]}&build={self.dict_bili["build"]}&captcha={captcha}&device={self.dict_bili["device"]}&mobi_app={self.dict_bili["mobi_app"]}&password={password}&platform={self.dict_bili["platform"]}&username={username}'
            sign = self.calc_sign(temp_params)
            payload = f'{temp_params}&sign={sign}'
            url = "https://passport.bilibili.com/api/v2/oauth2/login"
            response = s.post(url, params=payload, headers=headers)
        return response

    def check_token(self):
        list_url = f'access_key={self.dict_bili["access_key"]}&{self.app_params}&ts={CurrentTime()}'
        list_cookie = self.dict_bili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = self.calc_sign(params)
        true_url = f'https://passport.bilibili.com/api/v2/oauth2/info?{params}&sign={sign}'
        response1 = requests.get(true_url, headers=self.dict_bili['appheaders'])
        return response1

    def refresh_token(self):
        list_url = f'access_key={self.dict_bili["access_key"]}&access_token={self.dict_bili["access_key"]}&{self.app_params}&refresh_token={self.dict_bili["refresh_token"]}&ts={CurrentTime()}'
        list_cookie = self.dict_bili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = self.calc_sign(params)
        payload = f'{params}&sign={sign}'
        # print(payload)
        url = f'https://passport.bilibili.com/api/v2/oauth2/refresh_token'
        response1 = requests.post(url, headers=self.dict_bili['appheaders'], params=payload)
        return response1

    async def get_giftlist_of_storm(self, dic):
        roomid = dic['roomid']
        get_url = f"{self.base_url}/lottery/v1/Storm/check?roomid={roomid}"
        response = await self.bili_section_get(get_url, headers=self.dict_bili['pcheaders'])
        return response

    async def get_gift_of_storm(self, id):
        storm_url = f'{self.base_url}/lottery/v1/Storm/join'
        payload = {
            "id": id,
            "color": "16777215",
            "captcha_token": "",
            "captcha_phrase": "",
            "token": "",
            "csrf_token": self.dict_bili['csrf']}
        response1 = await self.bili_section_post(storm_url, data=payload, headers=self.dict_bili['pcheaders'])
        return response1

    async def get_gift_of_events_web(self, room_id, text2, raffleid):
        headers = {
            **(self.dict_bili['pcheaders']),
            'referer': text2
        }
        pc_url = f'{self.base_url}/activity/v1/Raffle/join?roomid={room_id}&raffleId={raffleid}'
        pc_response = await self.bili_section_get(pc_url, headers=headers)

        return pc_response

    async def get_gift_of_events_app(self, room_id, text2, raffleid):
        headers = {
            **(self.dict_bili['appheaders']),
            'referer': text2
        }
        temp_params = f'access_key={self.dict_bili["access_key"]}&actionKey={self.dict_bili["actionKey"]}&appkey={self.dict_bili["appkey"]}&build={self.dict_bili["build"]}&device={self.dict_bili["device"]}&event_type=flower_rain-{raffleid}&mobi_app={self.dict_bili["mobi_app"]}&platform={self.dict_bili["platform"]}&room_id={room_id}&ts={CurrentTime()}'
        # params = temp_params + self.dict_bili['app_secret']
        sign = self.calc_sign(temp_params)
        true_url = f'{self.base_url}/YunYing/roomEvent?{temp_params}&sign={sign}'
        # response1 = await self.bili_section_get(true_url, params=params, headers=headers)
        response1 = await self.bili_section_get(true_url, headers=headers)
        return response1
   
    async def get_gift_of_TV(self, real_roomid, TV_raffleid):
        url = f"{self.base_url}/gift/v3/smalltv/join"
        payload = {
            "roomid": real_roomid,
            "raffleId": TV_raffleid,
            "type": "Gift",
            "csrf_token": ''
            }
            
        response = await self.bili_section_post(url, data=payload, headers=self.dict_bili['pcheaders'])
        return response
        
    async def get_gift_of_TV_app(self, real_roomid, raffle_id, raffle_type):
        url = f"{self.base_url}/gift/v4/smalltv/getAward"
        temp_params = f'access_key={self.dict_bili["access_key"]}&{self.app_params}&raffleId={raffle_id}&roomid={real_roomid}&ts={CurrentTime()}&type={raffle_type}'
        sign = self.calc_sign(temp_params)
        payload = f'{temp_params}&sign={sign}'
        # print(payload)
        response = await self.bili_section_post(url, params=payload, headers=self.dict_bili['appheaders'])
        # print(response)
        return response

    async def get_gift_of_guard(self, roomid, id):
        url = f"{self.base_url}/lottery/v2/Lottery/join"
        data = {
            'roomid': roomid,
            'id': id,
            'type': 'guard',
            'csrf_token': self.dict_bili['csrf']
        }
        json_rsp = await self.bili_section_post(url, data=data, headers=self.dict_bili['pcheaders'])
        return json_rsp
    
    async def get_giftlist_of_events(self, room_id):
        url = f'{self.base_url}/activity/v1/Raffle/check?roomid={room_id}'
        response = await self.bili_section_get(url, headers=self.dict_bili['pcheaders'])
        return response

    async def get_giftlist_of_TV(self, real_roomid):
        url = f"{self.base_url}/gift/v3/smalltv/check?roomid={real_roomid}"
        response = await self.bili_section_get(url)
        return response

    async def get_giftlist_of_guard(self, roomid):
        url = f'{self.base_url}/lottery/v1/Lottery/check_guard?roomid={roomid}'
        json_rsp = await self.bili_section_get(url, headers=self.dict_bili['pcheaders'])
        return json_rsp
    
    async def get_activity_result(self, activity_roomid, activity_raffleid):
        url = f"{self.base_url}/activity/v1/Raffle/notice?roomid={activity_roomid}&raffleId={activity_raffleid}"
        response = await self.bili_section_get(url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def get_TV_result(self, TV_roomid, TV_raffleid):
        url = f"{self.base_url}/gift/v3/smalltv/notice?type=small_tv&raffleId={TV_raffleid}"
        response = await self.bili_section_get(url, headers=self.dict_bili['pcheaders'])
        return response

    async def pcpost_heartbeat(self):
        
        url = f'{self.base_url}/User/userOnlineHeart'
        response = await self.bili_section_post(url, headers=self.dict_bili['pcheaders'])
        return response

    # 发送app心跳包
    
    async def apppost_heartbeat(self):
        
        time = CurrentTime()
        temp_params = f'access_key={self.dict_bili["access_key"]}&{self.app_params}&ts={time}'
        sign = self.calc_sign(temp_params)
        url = f'{self.base_url}/mobile/userOnlineHeart?{temp_params}&sign={sign}'
        payload = {'roomid': 23058, 'scale': 'xhdpi'}
        response = await self.bili_section_post(url, data=payload, headers=self.dict_bili['appheaders'])
        return response

    # 心跳礼物
    async def heart_gift(self):
        url = f"{self.base_url}/gift/v2/live/heart_gift_receive?roomid=3&area_v2_id=34"
        response = await self.bili_section_get(url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def get_lotterylist(self, i):
        url = f"{self.base_url}/lottery/v1/box/getStatus?aid={i}"
        response = await self.bili_section_get(url, headers=self.dict_bili['pcheaders'])
        return response

    async def get_gift_of_lottery(self, i, g):
        url1 = f'{self.base_url}/lottery/v1/box/draw?aid={i}&number={g + 1}'
        response1 = await self.bili_section_get(url1, headers=self.dict_bili['pcheaders'])
        return response1

    async def get_time_about_silver(self):
        time = CurrentTime()
        temp_params = f'access_key={self.dict_bili["access_key"]}&{self.app_params}&ts={time}'
        sign = self.calc_sign(temp_params)
        GetTask_url = f'{self.base_url}/mobile/freeSilverCurrentTask?{temp_params}&sign={sign}'
        response = await self.bili_section_get(GetTask_url, headers=self.dict_bili['appheaders'])
        return response
    
    async def get_silver(self, timestart, timeend):
        time = CurrentTime()
        temp_params = f'access_key={self.dict_bili["access_key"]}&{self.app_params}&time_end={timeend}&time_start={timestart}&ts={time}'
        sign = self.calc_sign(temp_params)
        url = f'{self.base_url}/mobile/freeSilverAward?{temp_params}&sign={sign}'
        response = await self.bili_section_get(url, headers=self.dict_bili['appheaders'])
        return response

    async def get_dailybag(self):
        url = f'{self.base_url}/gift/v2/live/receive_daily_bag'
        response = await self.bili_section_get(url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def get_dosign(self):
        url = f'{self.base_url}/sign/doSign'
        response = await self.bili_section_get(url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def get_dailytask(self):
        url = f'{self.base_url}/activity/v1/task/receive_award'
        payload2 = {'task_id': 'double_watch_task'}
        response2 = await self.bili_section_post(url, data=payload2, headers=self.dict_bili['appheaders'])
        return response2
    
    async def get_grouplist(self):
        url = "https://api.vc.bilibili.com/link_group/v1/member/my_groups"
        json_rsp = await self.other_session_get(url, headers=self.dict_bili['pcheaders'])
        return json_rsp
    
    async def assign_group(self, i1, i2):
        temp_params = f'access_key={self.dict_bili["access_key"]}&actionKey={self.dict_bili["actionKey"]}&appkey={self.dict_bili["appkey"]}&build={self.dict_bili["build"]}&device={self.dict_bili["device"]}&group_id={i1}&mobi_app={self.dict_bili["mobi_app"]}&owner_id={i2}&platform={self.dict_bili["platform"]}&ts={CurrentTime()}'
        sign = self.calc_sign(temp_params)
        url = f'https://api.vc.bilibili.com/link_setting/v1/link_setting/sign_in?{temp_params}&sign={sign}'
        json_rsp = await self.other_session_get(url, headers=self.dict_bili['appheaders'])
        return json_rsp
    
    async def gift_list(self):
        url = f"{self.base_url}/gift/v3/live/gift_config"
        res = await self.bili_section_get(url)
        return res
            
    async def req_realroomid(self, areaid):
        url = f'{self.base_url}/room/v1/area/getRoomList?platform=web&parent_area_id={areaid}&cate_id=0&area_id=0&sort_type=online&page=1&page_size=30'
        json_rsp = await self.bili_section_get(url)
        return json_rsp
         
    async def req_room_init(self, roomid):
        url = f'{self.base_url}/room/v1/Room/room_init?id={roomid}'
        json_rsp = await self.bili_section_get(url)
        return json_rsp
        
    async def ReqRoomInfo(self, roomid):
        url = f"{self.base_url}/room/v1/Room/get_info?room_id={roomid}"
        res = await self.bili_section_get(url)
        return res

    async def ReqGiveCoin2Av(self, video_id, num):
        url = 'https://api.bilibili.com/x/web-interface/coin/add'
        pcheaders = {
            **(self.dict_bili['pcheaders']),
            'referer': f'https://www.bilibili.com/video/av{video_id}'
            }
        data = {
            'aid': video_id,
            'multiply': num,
            'cross_domain': 'true',
            'csrf': self.dict_bili['csrf']
        }
        json_rsp = await self.other_session_post(url, headers=pcheaders, data=data)
        return json_rsp

    async def Heartbeat(self, aid, cid):
        url = 'https://api.bilibili.com/x/report/web/heartbeat'
        data = {'aid': aid, 'cid': cid, 'mid': self.dict_bili['uid'], 'csrf': self.dict_bili['csrf'],
                'played_time': 0, 'realtime': 0,
                'start_ts': int(time.time()), 'type': 3, 'dt': 2, 'play_type': 1}
        json_rsp = await self.other_session_post(url, data=data, headers=self.dict_bili['pcheaders'])
        return json_rsp

    async def ReqMasterInfo(self):
        url = 'https://account.bilibili.com/home/reward'
        json_rsp = await self.other_session_get(url, headers=self.dict_bili['pcheaders'])
        return json_rsp

    async def ReqVideoCid(self, video_aid):
        url = f'https://www.bilibili.com/widget/getPageList?aid={video_aid}'
        json_rsp = await self.other_session_get(url)
        return json_rsp

    async def DailyVideoShare(self, video_aid):
        url = 'https://api.bilibili.com/x/web-interface/share/add'
        data = {'aid': video_aid, 'jsonp': 'jsonp', 'csrf': self.dict_bili['csrf']}
        json_rsp = await self.other_session_post(url, data=data, headers=self.dict_bili['pcheaders'])
        return json_rsp
    
    async def req_fetch_uper_video(self, mid, page):
        url = f'https://space.bilibili.com/ajax/member/getSubmitVideos?mid={mid}&pagesize=100&page={page}'
        json_rsp = await self.other_session_get(url)
        return json_rsp
                
    async def req_fetch_av(self):
        text_tsp = await self.session_text_get('https://www.bilibili.com/ranking/all/0/0/1/')
        return text_tsp
    
    async def req_vote_case(self, id, vote):
        url = 'http://api.bilibili.com/x/credit/jury/vote'
        payload = {
            "jsonp": "jsonp",
            "cid": id,
            "vote": vote,
            "content": "",
            "likes": "",
            "hates": "",
            "attr": "1",
            "csrf": self.dict_bili['csrf']
        }
        json_rsp = await self.other_session_post(url, headers=self.dict_bili['pcheaders'], data=payload)
        return json_rsp
        
    async def req_fetch_case(self):
        url = 'http://api.bilibili.com/x/credit/jury/caseObtain'
        payload = {
            "jsonp": "jsonp",
            "csrf": self.dict_bili['csrf']
        }
        json_rsp = await self.other_session_post(url, headers=self.dict_bili['pcheaders'], data=payload)
        return json_rsp
        
    async def req_check_voted(self, id):
        headers = {
            **(self.dict_bili['pcheaders']),
            'Referer': f'https://www.bilibili.com/judgement/vote/{id}',
        }
        url = f'https://api.bilibili.com/x/credit/jury/juryCase?jsonp=jsonp&callback=jQuery1720{randomint()}_{CurrentTime()}&cid={id}&_={CurrentTime()}'
        text_rsp = await self.session_text_get(url, headers=headers)
        # print(text_rsp)
        return text_rsp
        
        
class HostWebHub(WebHub):
    base_url = 'https://api.live.bilibili.com'
    
    def __init__(self, id, dict_new, dict_bili):
        self.dict_bili = copy.deepcopy(dict_bili)
        self.set_status(dict_new)
        self.user_id = id
        self.bili_session = None
        self.var_other_session = None
        if dict_bili:
            self.app_params = f'actionKey={dict_bili["actionKey"]}&appkey={dict_bili["appkey"]}&build={dict_bili["build"]}&device={dict_bili["device"]}&mobi_app={dict_bili["mobi_app"]}&platform={dict_bili["platform"]}'
        self.base_url = f'http://{Host().get_host()}'
        self.headers_host = {'host': 'api.live.bilibili.com'}
    
    async def bili_section_post(self, url, headers={}, data=None, parama=None):
        i = 5
        while True:
            i -= 1
            if i < 0:
                self.base_url = f'http://{Host().get_host()}'
                list_words = url.split('/')
                list_words[2] = self.base_url
                url = '/'.join(list_words[2:])
                print('ip切换为', url)
                i = 5
            try:
                async with self.bili_section.post(url, headers={**headers, **(self.headers_host)}, data=data, params=parama) as response:
                    json_rsp = await self.get_json_rsp(response, url)
                    if json_rsp is not None:
                        return json_rsp
                    elif response.status == 403:
                        print('403频繁')
                        i = -1
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url, self.user_id)
                continue

    async def bili_section_get(self, url, headers={}, data=None, params=None):
        i = 5
        while True:
            i -= 1
            if i < 0:
                self.base_url = f'http://{Host().get_host()}'
                list_words = url.split('/')
                list_words[2] = self.base_url
                url = '/'.join(list_words[2:])
                print('ip切换为', url)
                i = 5
            try:
                async with self.bili_section.get(url, headers={**headers, **(self.headers_host)}, data=data, params=params) as response:
                    json_rsp = await self.get_json_rsp(response, url)
                    if json_rsp is not None:
                        return json_rsp
                    elif response.status == 403:
                        print('403频繁')
                        i = -1
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url, self.user_id)
                continue
                
    
