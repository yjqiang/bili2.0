import printer
from printer import Printer
from task import RaffleHandler
from super_user import SuperUser
import asyncio
import websockets
import struct
import json
import re
import sys


async def DanMuraffle(area_id, connect_roomid, dic):
    cmd = dic['cmd']
    # print(cmd)
    
    if cmd == 'PREPARING':
        printer.info([f'{area_id}号弹幕监控房间下播({connect_roomid})'], True)
        return False
    elif cmd == 'SYS_GIFT':
        if 'giftId' in dic:
            if dic['giftId'] == 39:
                pass
                '''
                printer.info(["节奏风暴"], True)
                temp = await bilibili.get_giftlist_of_storm(dic)
                check = len(temp['data'])
                if check != 0 and temp['data']['hasJoin'] != 1:
                    id = temp['data']['id']
                    json_response1 = await bilibili.get_gift_of_storm(id)
                    print(json_response1)
                else:
                    printer.info([dic, "请联系开发者"])
                '''
            else:
                text1 = dic['real_roomid']
                text2 = dic['url']
                printer.info([dic, "请联系开发者"])
                try:
                    giftId = dic['giftId']
                    printer.info(["检测到房间{:^9}的活动抽奖".format(text1)], True)
                    RaffleHandler().push2queue((giftId, text1, text2), 'handle_1_room_activity')
                    # Statistics.append2pushed_raffle('活动', area_id=area_id)
                            
                except:
                    printer.info([dic, "请联系开发者"])
                
        else:
            printer.info(['普通送礼提示', dic['msg_text']])
        return
    elif cmd == 'SYS_MSG':
        if 'real_roomid' in dic:
            real_roomid = dic['real_roomid']
            type_text = (dic['msg'].split(':?')[-1]).split('，')[0].replace('一个', '')
            printer.info([f'{area_id}号弹幕监控检测到{real_roomid:^9}的{type_text}'], True)
            RaffleHandler().push2queue((real_roomid,), 'handle_TV_raffle')
            # Statistics.append2pushed_raffle(type_text, area_id=area_id)
            
    elif cmd == 'GUARD_MSG':
        a = re.compile(r"(?<=在主播 )\S+(?= 的直播间开通了总督)")
        res = re.search(a, dic['msg'])
        if res is not None:
            name = str(res.group())
            printer.info([f'{area_id}号弹幕监控检测到{name:^9}的总督'], True)
            RaffleHandler().push2queue((name,), 'handle_captain_raffle')
            # Statistics.append2pushed_raffle('总督', area_id=area_id)
        
  
def printDanMu(dic):
    cmd = dic['cmd']
    # print(cmd)
    if cmd == 'DANMU_MSG':
        # print(dic)
        Printer().print_danmu(dic)
        return
                                                          

class bilibiliClient():
    
    __slots__ = ('ws', 'connected', 'roomid', 'raffle_handle', 'area_id')

    def __init__(self, roomid=None, area_id=None):
        self.ws = None
        self.connected = False
        if area_id == 0:
            self.roomid = roomid
            self.area_id = 0
            self.raffle_handle = False
        else:
            self.roomid = roomid
            self.area_id = area_id
            self.raffle_handle = True

    # 待确认
    async def close_connection(self):
        try:
            await self.ws.close()
        except:
            print('请联系开发者', sys.exc_info()[0], sys.exc_info()[1])
        self.connected = False
        
    async def CheckArea(self):
        while self.connected:
            area_id = await SuperUser().FetchRoomArea(self.roomid)
            if area_id != self.area_id:
                printer.info([f'{self.roomid}更换分区{self.area_id}为{area_id}，即将切换房间'], True)
                return
            await asyncio.sleep(300)
        
    async def connectServer(self):
        try:
            self.ws = await websockets.connect('wss://broadcastlv.chat.bilibili.com/sub', timeout=3)
        except:
            print("# 连接无法建立，请检查本地网络状况")
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        printer.info([f'{self.area_id}号弹幕监控已连接b站服务器'], True)
        body = f'{{"uid":0,"roomid":{self.roomid},"protover":1,"platform":"web","clientver":"1.3.3"}}'
        if (await self.SendSocketData(opt=7, body=body)):
            self.connected = True
            return True
        else:
            return False

    async def HeartbeatLoop(self):
        printer.info([f'{self.area_id}号弹幕监控开始心跳（心跳间隔30s，后续不再提示）'], True)
        while self.connected:
            if not (await self.SendSocketData(opt=2, body='')):
                self.connected = False
                return
            await asyncio.sleep(30)

    async def SendSocketData(self, opt, body, len_header=16, ver=1, seq=1):
        remain_data = body.encode('utf-8')
        len_data = len(remain_data) + len_header
        header = struct.pack('!I2H2I', len_data, len_header, ver, opt, seq)
        data = header + remain_data
        try:
            await self.ws.send(data)
        except websockets.exceptions.ConnectionClosed:
            print("# 主动关闭或者远端主动关闭.")
            await self.ws.close()
            self.connected = False
            return False
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            self.connected = False
            return False
        return True

    async def ReadSocketData(self):
        bytes_data = None
        try:
            bytes_data = await asyncio.wait_for(self.ws.recv(), timeout=35.0)
        except asyncio.TimeoutError:
            print('# 由于心跳包30s一次，但是发现35内没有收到任何包，说明已经悄悄失联了，主动断开')
            await self.ws.close()
            self.connected = False
            return None
        except websockets.exceptions.ConnectionClosed:
            print("# 主动关闭或者远端主动关闭")
            await self.ws.close()
            await self.ws.close()
            self.connected = False
            return None
        except:
            # websockets.exceptions.ConnectionClosed'>
            print(sys.exc_info()[0], sys.exc_info()[1])
            print('请联系开发者')
            await self.ws.close()
            self.connected = False
            return None
        # print(tmp)
           
        # print('测试0', bytes_data)
        return bytes_data
    
    async def ReceiveMessageLoop(self):
        if self.raffle_handle:
            while self.connected:
                bytes_datas = await self.ReadSocketData()
                if bytes_datas is None:
                    break
                len_read = 0
                len_bytes_datas = len(bytes_datas)
                while len_read != len_bytes_datas:
                    state = None
                    split_header = struct.unpack('!I2H2I', bytes_datas[len_read:16+len_read])
                    len_data, len_header, ver, opt, seq = split_header
                    remain_data = bytes_datas[len_read+16:len_read+len_data]
                    # 人气值/心跳 3s间隔
                    if opt == 3:
                        # self._UserCount, = struct.unpack('!I', remain_data)
                        pass
                    # cmd
                    elif opt == 5:
                        messages = remain_data.decode('utf-8')
                        dic = json.loads(messages)
                        state = await DanMuraffle(self.area_id, self.roomid, dic)
                    # 握手确认
                    elif opt == 8:
                        printer.info([f'{self.area_id}号弹幕监控进入房间（{self.roomid}）'], True)
                    else:
                        self.connected = False
                        printer.warn(bytes_datas[len_read:len_read + len_data])
                                
                    if state is not None and not state:
                        return
                    len_read += len_data
                    
        else:
            while self.connected:
                bytes_datas = await self.ReadSocketData()
                if bytes_datas is None:
                    break
                len_read = 0
                len_bytes_datas = len(bytes_datas)
                while len_read != len_bytes_datas:
                    state = None
                    split_header = struct.unpack('!I2H2I', bytes_datas[len_read:16+len_read])
                    len_data, len_header, ver, opt, seq = split_header
                    remain_data = bytes_datas[len_read+16:len_read+len_data]
                    # 人气值/心跳 3s间隔
                    if opt == 3:
                        # self._UserCount, = struct.unpack('!I', remain_data)
                        pass
                    # cmd
                    elif opt == 5:
                        messages = remain_data.decode('utf-8')
                        dic = json.loads(messages)
                        state = printDanMu(dic)
                    # 握手确认
                    elif opt == 8:
                        printer.info([f'{self.area_id}号弹幕监控进入房间（{self.roomid}）'], True)
                    else:
                        self.connected = False
                        printer.warn(bytes_datas[len_read:len_read + len_data])
                                
                    if state is not None and not state:
                        return
                    len_read += len_data
                  
                    
                    
               
    

