import copy
from webhub.base_web_hub import BaseWebHub
from webhub.web_session import WebSession


class BiliWebHub(BaseWebHub):
    
    def __init__(self, id, dict_new, dict_bili):
        self.dict_bili = copy.deepcopy(dict_bili)
        self.base_url = 'https://api.live.bilibili.com'
        self.set_status(dict_new)
        self._bili_session = None
        if dict_bili:
            self.app_params = f'actionKey={dict_bili["actionKey"]}&appkey={dict_bili["appkey"]}&build={dict_bili["build"]}&device={dict_bili["device"]}&mobi_app={dict_bili["mobi_app"]}&platform={dict_bili["platform"]}'
            
    @property
    def bili_session(self):
        if self._bili_session is None:
            self._bili_session = WebSession()
            # print(0)
        return self._bili_session
                
    async def bili_req_json(self, method, url, headers=None, data=None, params=None):
        json_body = await self.bili_session.request_json(method, url, headers=headers, data=data, params=params)
        return json_body    
                
    async def playurl(self, cid):
        # cid real_roomid
        # url = 'http://api.live.bilibili.com/room/v1/Room/playUrl?'
        url = f'{self.base_url}/api/playurl?device=phone&platform=ios&scale=3&build=10000&cid={cid}&otype=json&platform=h5'
        response = await self.bili_req_json('GET', url)
        return response
        
    async def fetch_capsule(self):
        url = f"{self.base_url}/api/ajaxCapsule"
        response = await self.bili_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return response

    async def open_capsule(self, count):
        url = f"{self.base_url}/api/ajaxCapsuleOpen"
        data = {
            'type': 'normal',
            "count": count,
            "csrf_token": self.dict_bili['csrf']
        }
        response = await self.bili_req_json('POST', url, data=data, headers=self.dict_bili['pcheaders'])
        return response
        
    # 1:900兑换
    async def doublegain_coin2silver(self):
        # url: "/exchange/coin2silver",
        data = {'coin': 10}
        url = f"{self.base_url}/exchange/coin2silver"
        response = await self.bili_req_json('POST', url, data=data, headers=self.dict_bili['pcheaders'])
        return response

    async def post_watching_history(self, room_id):
        data = {
            "room_id": room_id,
            "csrf_token": self.dict_bili['csrf']
        }
        url = f"{self.base_url}/room/v1/Room/room_entry_action"
        response = await self.bili_req_json('POST', url, data=data, headers=self.dict_bili['pcheaders'])
        return response
    
    async def silver2coin_web(self):
        url = f"{self.base_url}/pay/v1/Exchange/silver2coin"
        data = {
            "platform": 'pc',
            "csrf_token": self.dict_bili['csrf']
        }
        response = await self.bili_req_json('POST', url, headers=self.dict_bili['pcheaders'], data=data)
        return response
    
    async def silver2coin_app(self):
        temp_params = f'access_key={self.dict_bili["access_key"]}&{self.app_params}&ts={self.CurrentTime()}'
        sign = self.calc_sign(temp_params)
        app_url = f"{self.base_url}/AppExchange/silver2coin?{temp_params}&sign={sign}"
        response1 = await self.bili_req_json('POST', app_url, headers=self.dict_bili['appheaders'])
        return response1
    
    async def fetch_fan(self, real_roomid, uid):
        url = f'{self.base_url}/rankdb/v1/RoomRank/webMedalRank?roomid={real_roomid}&ruid={uid}'
        response = await self.bili_req_json('GET', url)
        return response
    
    async def check_room(self, roomid):
        url = f"{self.base_url}/room/v1/Room/room_init?id={roomid}"
        response = await self.bili_req_json('GET', url)
        return response
    
    async def fetch_bag_list(self):
        url = f"{self.base_url}/gift/v2/gift/bag_list"
        response = await self.bili_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def check_taskinfo(self):
        url = f'{self.base_url}/i/api/taskInfo'
        response = await self.bili_req_json('GET', url, headers=self.dict_bili['pcheaders'])
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
            'rnd': self.CurrentTime(),
            'storm_beat_id': '0',
            'metadata': '',
            'price': '0',
            'csrf_token': self.dict_bili['csrf']
        }
        response = await self.bili_req_json('POST', url, headers=self.dict_bili['pcheaders'], data=data)
        return response
    
    async def fetch_user_info(self):
        url = f"{self.base_url}/i/api/liveinfo"
        response = await self.bili_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def fetch_user_infor_ios(self):
        temp_params = f'access_key={self.dict_bili["access_key"]}&platform=ios'
        url = f'{self.base_url}/mobile/getUser?{temp_params}'
        response = await self.bili_req_json('GET', url)
        return response
    
    async def fetch_liveuser_info(self, real_roomid):
        url = f'{self.base_url}/live_user/v1/UserInfo/get_anchor_in_room?roomid={real_roomid}'
        response = await self.bili_req_json('GET', url)
        return response
        
    async def send_danmu_msg_web(self, msg, roomId):
        url = f'{self.base_url}/msg/send'
        data = {
            'color': '16777215',
            'fontsize': '25',
            'mode': '1',
            'msg': msg,
            'rnd': '0',
            'roomid': int(roomId),
            'csrf_token': self.dict_bili['csrf'],
            'csrf': self.dict_bili['csrf']
        }

        response = await self.bili_req_json('POST', url, headers=self.dict_bili['pcheaders'], data=data)
        return response
    
    async def fetchmedal(self):
        url = f'{self.base_url}/i/api/medal?page=1&pageSize=50'
        response = await self.bili_req_json('POST', url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def ReqWearingMedal(self):
        url = f'{self.base_url}/live_user/v1/UserInfo/get_weared_medal'
        data = {
            'uid': self.dict_bili['uid'],
            'csrf_token': ''
        }
        response = await self.bili_req_json('POST', url, data=data, headers=self.dict_bili['pcheaders'])
        return response

    async def ReqTitleInfo(self):
        temp_params = f'access_key={self.dict_bili["access_key"]}&{self.app_params}'
        sign = self.calc_sign(temp_params)
        url = f'{self.base_url}/appUser/myTitleList?{temp_params}&sign={sign}'
        response = await self.bili_req_json('GET', url, headers=self.dict_bili['appheaders'])
        return response
        
    async def get_giftlist_of_storm(self, dic):
        roomid = dic['roomid']
        get_url = f"{self.base_url}/lottery/v1/Storm/check?roomid={roomid}"
        response = await self.bili_req_json('GET', get_url, headers=self.dict_bili['pcheaders'])
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
        response1 = await self.bili_req_json('POST', storm_url, data=payload, headers=self.dict_bili['pcheaders'])
        return response1

    async def get_gift_of_events_web(self, room_id, text2, raffleid):
        headers = {
            **(self.dict_bili['pcheaders']),
            'referer': text2
        }
        pc_url = f'{self.base_url}/activity/v1/Raffle/join?roomid={room_id}&raffleId={raffleid}'
        pc_response = await self.bili_req_json('GET', pc_url, headers=headers)

        return pc_response

    async def get_gift_of_events_app(self, room_id, text2, raffleid):
        headers = {
            **(self.dict_bili['appheaders']),
            'referer': text2
        }
        temp_params = f'access_key={self.dict_bili["access_key"]}&actionKey={self.dict_bili["actionKey"]}&appkey={self.dict_bili["appkey"]}&build={self.dict_bili["build"]}&device={self.dict_bili["device"]}&event_type=flower_rain-{raffleid}&mobi_app={self.dict_bili["mobi_app"]}&platform={self.dict_bili["platform"]}&room_id={room_id}&ts={self.CurrentTime()}'
        # params = temp_params + self.dict_bili['app_secret']
        sign = self.calc_sign(temp_params)
        true_url = f'{self.base_url}/YunYing/roomEvent?{temp_params}&sign={sign}'
        # response1 = await self.bili_req_json('GET', true_url, params=params, headers=headers)
        response1 = await self.bili_req_json('GET', true_url, headers=headers)
        return response1
   
    async def get_gift_of_TV(self, real_roomid, TV_raffleid):
        url = f"{self.base_url}/gift/v3/smalltv/join"
        payload = {
            "roomid": real_roomid,
            "raffleId": TV_raffleid,
            "type": "Gift",
            "csrf_token": ''
            }
            
        response = await self.bili_req_json('POST', url, data=payload, headers=self.dict_bili['pcheaders'])
        return response
        
    async def get_gift_of_TV_app(self, real_roomid, raffle_id, raffle_type):
        url = f"{self.base_url}/gift/v4/smalltv/getAward"
        temp_params = f'access_key={self.dict_bili["access_key"]}&{self.app_params}&raffleId={raffle_id}&roomid={real_roomid}&ts={self.CurrentTime()}&type={raffle_type}'
        sign = self.calc_sign(temp_params)
        payload = f'{temp_params}&sign={sign}'
        # print(payload)
        response = await self.bili_req_json('POST', url, params=payload, headers=self.dict_bili['appheaders'])
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
        json_rsp = await self.bili_req_json('POST', url, data=data, headers=self.dict_bili['pcheaders'])
        return json_rsp
    
    async def get_giftlist_of_events(self, room_id):
        url = f'{self.base_url}/activity/v1/Raffle/check?roomid={room_id}'
        response = await self.bili_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return response

    async def get_giftlist_of_TV(self, real_roomid):
        url = f"{self.base_url}/gift/v3/smalltv/check?roomid={real_roomid}"
        response = await self.bili_req_json('GET', url)
        return response

    async def get_giftlist_of_guard(self, roomid):
        url = f'{self.base_url}/lottery/v1/Lottery/check_guard?roomid={roomid}'
        json_rsp = await self.bili_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return json_rsp
    
    async def get_activity_result(self, activity_roomid, activity_raffleid):
        url = f"{self.base_url}/activity/v1/Raffle/notice?roomid={activity_roomid}&raffleId={activity_raffleid}"
        response = await self.bili_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def get_TV_result(self, TV_roomid, TV_raffleid):
        url = f"{self.base_url}/gift/v3/smalltv/notice?type=small_tv&raffleId={TV_raffleid}"
        response = await self.bili_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return response

    async def pcpost_heartbeat(self):
        
        url = f'{self.base_url}/User/userOnlineHeart'
        response = await self.bili_req_json('POST', url, headers=self.dict_bili['pcheaders'])
        return response

    # 发送app心跳包
    
    async def apppost_heartbeat(self):
        
        time = self.CurrentTime()
        temp_params = f'access_key={self.dict_bili["access_key"]}&{self.app_params}&ts={time}'
        sign = self.calc_sign(temp_params)
        url = f'{self.base_url}/mobile/userOnlineHeart?{temp_params}&sign={sign}'
        payload = {'roomid': 23058, 'scale': 'xhdpi'}
        response = await self.bili_req_json('POST', url, data=payload, headers=self.dict_bili['appheaders'])
        return response

    # 心跳礼物
    async def heart_gift(self):
        url = f"{self.base_url}/gift/v2/live/heart_gift_receive?roomid=3&area_v2_id=34"
        response = await self.bili_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def get_lotterylist(self, i):
        url = f"{self.base_url}/lottery/v1/box/getStatus?aid={i}"
        response = await self.bili_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return response

    async def get_gift_of_lottery(self, i, g):
        url1 = f'{self.base_url}/lottery/v1/box/draw?aid={i}&number={g + 1}'
        response1 = await self.bili_req_json('GET', url1, headers=self.dict_bili['pcheaders'])
        return response1

    async def get_time_about_silver(self):
        time = self.CurrentTime()
        temp_params = f'access_key={self.dict_bili["access_key"]}&{self.app_params}&ts={time}'
        sign = self.calc_sign(temp_params)
        GetTask_url = f'{self.base_url}/mobile/freeSilverCurrentTask?{temp_params}&sign={sign}'
        response = await self.bili_req_json('GET', GetTask_url, headers=self.dict_bili['appheaders'])
        return response
    
    async def get_silver(self, timestart, timeend):
        time = self.CurrentTime()
        temp_params = f'access_key={self.dict_bili["access_key"]}&{self.app_params}&time_end={timeend}&time_start={timestart}&ts={time}'
        sign = self.calc_sign(temp_params)
        url = f'{self.base_url}/mobile/freeSilverAward?{temp_params}&sign={sign}'
        response = await self.bili_req_json('GET', url, headers=self.dict_bili['appheaders'])
        return response

    async def get_dailybag(self):
        url = f'{self.base_url}/gift/v2/live/receive_daily_bag'
        response = await self.bili_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def get_dosign(self):
        url = f'{self.base_url}/sign/doSign'
        response = await self.bili_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return response
    
    async def get_dailytask(self):
        url = f'{self.base_url}/activity/v1/task/receive_award'
        payload2 = {'task_id': 'double_watch_task'}
        response2 = await self.bili_req_json('POST', url, data=payload2, headers=self.dict_bili['appheaders'])
        return response2
        
    async def gift_list(self):
        url = f"{self.base_url}/gift/v3/live/gift_config"
        res = await self.bili_req_json('GET', url)
        return res
            
    async def req_realroomid(self, areaid):
        url = f'{self.base_url}/room/v1/area/getRoomList?platform=web&parent_area_id={areaid}&cate_id=0&area_id=0&sort_type=online&page=1&page_size=30'
        json_rsp = await self.bili_req_json('GET', url)
        return json_rsp
         
    async def req_room_init(self, roomid):
        url = f'{self.base_url}/room/v1/Room/room_init?id={roomid}'
        json_rsp = await self.bili_req_json('GET', url)
        return json_rsp
        
    async def ReqRoomInfo(self, roomid):
        url = f"{self.base_url}/room/v1/Room/get_info?room_id={roomid}"
        res = await self.bili_req_json('GET', url)
        return res
        

class HostBiliWebHub(BiliWebHub):
    
    def __init__(self, id, dict_new, dict_bili, host):
        self.dict_bili = copy.deepcopy(dict_bili)
        self.set_status(dict_new)
        self.user_id = id
        self._bili_session = None
        if dict_bili:
            self.app_params = f'actionKey={dict_bili["actionKey"]}&appkey={dict_bili["appkey"]}&build={dict_bili["build"]}&device={dict_bili["device"]}&mobi_app={dict_bili["mobi_app"]}&platform={dict_bili["platform"]}'
        self.host = host
        self.base_url = f'http://{self.host.get_host()}'
        self.headers_host = {'host': 'api.live.bilibili.com'}
    
    async def bili_req_json(self, method, url, headers={}, data=None, parama=None):
        # print(url)
        i = 5
        while True:
            i -= 1
            if i < 0:
                self.base_url = f'http://{self.host.get_host()}'
                list_words = url.split('/')
                list_words[2] = self.base_url
                url = '/'.join(list_words[2:])
                print('ip切换为', url)
                i = 5
            json_body = await self.bili_session.request_json(method, url, headers={**headers, **(self.headers_host)}, data=data, params=parama, is_none_allowed=True)
            if json_body is not None:
                return json_body
            
            
    
