from task import Task
import asyncio
import random
import printer
import webbrowser
from PIL import Image
from io import BytesIO
import re
import time


def CurrentTime():
    # currenttime = int(time.mktime(datetime.datetime.now().timetuple()))
    return int(time.time())
    

class SuperUser():
        
    def __init__(self, user):
        self.webhub = user.webhub
        self.user_id = -1
        self.list_raffle_id = []
        
    def add2raffle_id(self, raffle_id):
        self.list_raffle_id.append(raffle_id)
        if len(self.list_raffle_id) > 150:
            # print(self.list_raffle_id)
            del self.list_raffle_id[:75]
            # print(self.list_raffle_id)
    
    def check_duplicate(self, raffle_id):
        return (raffle_id in self.list_raffle_id)
     
    async def check_room_state(self, roomid):
        json_rsp = await self.webhub.req_room_init(roomid)
        return json_rsp['data']['live_status']
    
    async def get_one(self, areaid):
        # 1 娱乐分区, 2 游戏分区, 3 手游分区, 4 绘画分区
        if areaid == 1:
            roomid = 23058
            state = await self.check_room_state(roomid)
            if state == 1:
                printer.info([f'{areaid}号弹幕监控选择房间（{roomid}）'], True)
                return roomid
                
        while True:
            json_rsp = await self.webhub.req_realroomid(areaid)
            data = json_rsp['data']
            roomid = random.choice(data)['roomid']
            state = await self.check_room_state(roomid)
            if state == 1:
                printer.info([f'{areaid}号弹幕监控选择房间（{roomid}）'], True)
                return roomid
            
    async def FetchRoomArea(self, roomid):
        json_response = await self.webhub.ReqRoomInfo(roomid)
    
        if not json_response['code']:
            # print(json_response)
            # print(json_response['data']['parent_area_id'])
            return json_response['data']['parent_area_id']
            
    async def find_live_user_roomid(self, wanted_name):
        print('发现名字', wanted_name)
        for i in range(len(wanted_name), 0, -1):
            json_rsp = await self.webhub.search_biliuser(wanted_name[:i])
            results = json_rsp['result']
            if results is None:
                # print('屏蔽全名')
                continue
            for i in results:
                real_name = re.sub(r'<[^>]*>', '', i['uname'])
                # print('去除干扰', real_name)
                if real_name == wanted_name:
                    print('找到结果', i['room_id'])
                    return i['room_id']
            # print('结束一次')
    
        print('第2备份启用')
        for i in range(len(wanted_name)):
            json_rsp = await self.webhub.search_biliuser(wanted_name[i:])
            results = json_rsp['result']
            if results is None:
                # print('屏蔽全名')
                continue
            for i in results:
                real_name = re.sub(r'<[^>]*>', '', i['uname'])
                # print('去除干扰', real_name)
                if real_name == wanted_name:
                    print('找到结果', i['room_id'])
                    return i['room_id']
    
        print('第3备份启用')
        for i in range(len(wanted_name), 0, -1):
            json_rsp = await self.webhub.search_liveuser(wanted_name[:i])
            results = json_rsp['result']
            if results is None:
                # print('屏蔽全名')
                continue
            for i in results:
                real_name = re.sub(r'<[^>]*>', '', i['uname'])
                # print('去除干扰', real_name)
                if real_name == wanted_name:
                    print('找到结果', i['roomid'])
                    return i['roomid']
    
        print('第4备份启用')
        for i in range(len(wanted_name)):
            json_rsp = await self.webhub.search_liveuser(wanted_name[i:])
            results = json_rsp['result']
            if results is None:
                # print('屏蔽全名')
                continue
            for i in results:
                real_name = re.sub(r'<[^>]*>', '', i['uname'])
                # print('去除干扰', real_name)
                if real_name == wanted_name:
                    print('找到结果', i['roomid'])
                    return i['roomid']
            
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
        
    async def watch_living_video(self, cid):
        import sound
        sound.set_honors_silent_switch(False)
        sound.set_volume(1)
        sound.play_effect('piano:D3')
        json_response = await self.webhub.playurl(cid)
        print(json_response)
        if not json_response['code']:
            data = json_response['data']
            print(data)
            webbrowser.open(data)
            
    async def check_if_normal_room(self, roomid):
        json_response = await self.webhub.check_room(roomid)
        if not json_response['code']:
            data = json_response['data']
            param1 = data['is_hidden']
            param2 = data['is_locked']
            param3 = data['encrypted']
            if any((param1, param2, param3)):
                printer.info([f'抽奖脚本检测到房间{roomid:^9}为异常房间'], True)
                return False
            else:
                printer.info([f'抽奖脚本检测到房间{roomid:^9}为正常房间'], True)
                return True
                
    # 与弹幕抽奖对应，这里的i其实是抽奖id
    async def handle_1_room_substant(self):
        list_available_raffleid = []
        blacklist = ['test', 'TEST', '测试', '加密']
        max = 10000
        min = 50
        while max > min:
            # print(min, max)
            middle = int((min + max + 1) / 2)
            code_middle = (await self.webhub.get_lotterylist(middle))['code']
            if code_middle:
                code_middle1 = (await self.webhub.get_lotterylist(middle + 1))['code']
                code_middle2 = (await self.webhub.get_lotterylist(middle + 2))['code']
                if code_middle1 and code_middle2:
                    max = middle - 1
                else:
                    min = middle + 1
            else:
                min = middle
        print('最新实物抽奖id为', min, max)
        for i in range(max - 30, max + 1):
            json_response = await self.webhub.get_lotterylist(i)
            print('id对应code数值为', json_response['code'], i)
            # -400 不存在
            if not json_response['code']:
                temp = json_response['data']['title']
                if any(word in temp for word in blacklist):
                    print("检测到疑似钓鱼类测试抽奖，默认不参与，请自行判断抽奖可参与性")
                    # print(temp)
                else:
                    check = json_response['data']['typeB']
                    for g, value in enumerate(check):
                        join_end_time = value['join_end_time']
                        join_start_time = value['join_start_time']
                        ts = CurrentTime()
                        if int(join_end_time) > int(ts) > int(join_start_time):
                            print('本次获取到的抽奖id为', i, g)
                            list_available_raffleid.append((i, g), 100)
    
        for tuple_values, max_wait in list_available_raffleid:
            Task().call_after('handle_1_substantial_raffle', 0, tuple_values, time_range=max_wait)
            
    async def handle_1_room_activity(self, room_id, text2):
        result = True
        if result:
            json_response = await self.webhub.get_giftlist_of_events(room_id)
            checklen = json_response['data']
            list_available_raffleid = []
            for j in checklen:
                # await asyncio.sleep(random.uniform(0.5, 1))
                # resttime = j['time']
                raffleid = j['raffleId']
                # if self.statistics.check_activitylist(text1, raffleid):
                #    list_available_raffleid.append(raffleid)
                list_available_raffleid.append((room_id, text2, raffleid), 00000)
            for tuple_values, max_wait in list_available_raffleid:
                Task().call_after('handle_1_activity_raffle', 0, tuple_values, time_range=max_wait)
                
    async def handle_1_room_TV(self, real_roomid):
        json_response = await self.webhub.get_giftlist_of_TV(real_roomid)
        # print(json_response['data']['list'])
        checklen = json_response['data']['list']
        list_available_raffleid = []
        for j in checklen:
            raffle_id = j['raffleId']
            raffle_type = j['type']
            max_wait = j['time'] - 10
            # 处理一些重复
            if not self.check_duplicate(raffle_id):
                print('本次获取到的抽奖id为', raffle_id)
                list_available_raffleid.append(((real_roomid, raffle_id, raffle_type), max_wait))
                self.add2raffle_id(raffle_id)
                
        # print(list_available_raffleid)
        for tuple_values, max_wait in list_available_raffleid:
            Task().call_after('handle_1_TV_raffle', 0, tuple_values, time_range=max_wait)
                
    async def handle_1_room_guard(self, roomid, raffleid=None):
        if raffleid is not None:
            json_response1 = {'data': [{'id': raffleid, 'time': 65}]}
        else:
            while True:
                json_response1 = await self.webhub.get_giftlist_of_guard(roomid)
                print(json_response1)
                if json_response1['data']:
                    break
                await asyncio.sleep(1)
            if not json_response1['data']:
                print(f'{roomid}没有guard或者guard已经领取')
                return
        list_available_raffleid = []
        # guard这里领取后，list对应会消失，其实就没有status了，这里是为了统一
        for j in json_response1['data']:
            id = j['id']
            # 总督长达一天，额外处理
            max_wait = min(j['time'] - 10, 240)
            if not self.check_duplicate(id):
                self.add2raffle_id(id)
                list_available_raffleid.append(((roomid, id), max_wait))
            
        for tuple_values, max_wait in list_available_raffleid:
            Task().call_after('handle_1_guard_raffle', 0, tuple_values, time_range=max_wait)
                
    async def update(self, func, value):
        return (await getattr(self, func)(*value))
    
    
    
    
            
