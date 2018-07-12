from web_hub import WebHub
# from messenger import DelayRaffleHandler
import asyncio
import time
import random
import printer
import webbrowser
from PIL import Image
from io import BytesIO
import re


class SuperUser():
    instance = None
        
    def __new__(cls):
        if not cls.instance:
            cls.instance = super(SuperUser, cls).__new__(cls)
            cls.instance.webhub = WebHub(-1, {}, {})
            cls.instance.user_id = -1
        return cls.instance

        
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
    
    
    
    
            
