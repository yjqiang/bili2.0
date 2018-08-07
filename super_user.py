from task import Task
import asyncio
import random
import printer
import webbrowser
from PIL import Image
from io import BytesIO
import re


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
                
    async def handle_1_room_TV(self, real_roomid):
        json_response = await self.webhub.get_giftlist_of_TV(real_roomid)
        # print(json_response['data']['list'])
        checklen = json_response['data']['list']
        list_available_raffleid = []
        for j in checklen:
            raffle_id = j['raffleId']
            raffle_type = j['type']
            max_wait = j['time_wait'] - 5
            # 处理一些重复
            if not self.check_duplicate(raffle_id):
                print('本次获取到的抽奖id为', raffle_id)
                list_available_raffleid.append(((real_roomid, raffle_id, raffle_type), max_wait))
                self.add2raffle_id(raffle_id)
                
        # print(list_available_raffleid)
        for tuple_values, max_wait in list_available_raffleid:
            Task().call_after('handle_1_TV_raffle', 0, tuple_values, time_range=max_wait)
                
    async def handle_1_room_captain(self, roomid):
        print('初步测试', roomid)
        while True:
            json_response1 = await self.webhub.get_giftlist_of_captain(roomid)
            print(json_response1)
            if not json_response1['data']['guard']:
                await asyncio.sleep(1)
            else:
                break
            
        list_available_raffleid = []
        # guard这里领取后，list对应会消失，其实就没有status了，这里是为了统一
        for j in json_response1['data']['guard']:
            id = j['id']
            status = j['status']
            if status == 1:
                # print('未参加')
                list_available_raffleid.append(((roomid, id), 200))
            elif status == 2:
                # print('过滤')
                pass
            else:
                print(json_response1)
            
        for tuple_values, max_wait in list_available_raffleid:
            # 一天之内均可领取，延迟2分钟无所谓
            Task().call_after('handle_1_captain_raffle', 0, tuple_values, time_range=max_wait)
                
    async def update(self, func, value):
        # print('hhhhhhhhhhhhhhhh', self.user_id, func)
        return (await getattr(self, func)(*value))
    
    
    
    
            
