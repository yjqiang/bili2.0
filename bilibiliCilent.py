import printer
from printer import Printer
from task import RaffleHandler
from task import Task
import asyncio
import aiohttp
import struct
import json
import sys


class BaseDanmu():
    
    __slots__ = ('ws', 'roomid', 'area_id', 'session')
    structer = struct.Struct('!I2H2I')

    def __init__(self, roomid=None, area_id=None):
        self.session = aiohttp.ClientSession()
        self.ws = None
        self.roomid = roomid
        self.area_id = area_id

    # 待确认
    async def close_connection(self):
        try:
            await self.ws.close()
        except:
            print('请联系开发者', sys.exc_info()[0], sys.exc_info()[1])
        printer.info([f'{self.area_id}号弹幕收尾模块状态{self.ws.closed}'], True)
        
    async def CheckArea(self):
        try:
            while True:
                area_id = await asyncio.shield(Task().call_right_now('FetchRoomArea', self.roomid))
                if area_id != self.area_id:
                    printer.info([f'{self.roomid}更换分区{self.area_id}为{area_id}，即将切换房间'], True)
                    return
                await asyncio.sleep(300)
        except asyncio.CancelledError:
            printer.info([f'{self.area_id}号弹幕监控分区检测模块主动取消'], True)
        
    async def connectServer(self):
        try:
            url = 'wss://broadcastlv.chat.bilibili.com/sub'
            self.ws = await asyncio.wait_for(self.session.ws_connect(url), timeout=3)
        except:
            print("# 连接无法建立，请检查本地网络状况")
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        printer.info([f'{self.area_id}号弹幕监控已连接b站服务器'], True)
        body = f'{{"uid":0,"roomid":{self.roomid},"protover":1,"platform":"web","clientver":"1.3.3"}}'
        return (await self.SendSocketData(opt=7, body=body))

    async def HeartbeatLoop(self):
        printer.info([f'{self.area_id}号弹幕监控开始心跳（心跳间隔30s，后续不再提示）'], True)
        try:
            while True:
                if not (await self.SendSocketData(opt=2, body='')):
                    return
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            printer.info([f'{self.area_id}号弹幕监控心跳模块主动取消'], True)

    async def SendSocketData(self, opt, body, len_header=16, ver=1, seq=1):
        remain_data = body.encode('utf-8')
        len_data = len(remain_data) + len_header
        header = self.structer.pack(len_data, len_header, ver, opt, seq)
        data = header + remain_data
        try:
            await self.ws.send_bytes(data)
        except asyncio.CancelledError:
            printer.info([f'{self.area_id}号弹幕监控发送模块主动取消'], True)
            return False
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        return True

    async def ReadSocketData(self):
        bytes_data = None
        try:
            msg = await asyncio.wait_for(self.ws.receive(), timeout=35.0)
            bytes_data = msg.data
        except asyncio.TimeoutError:
            print('# 由于心跳包30s一次，但是发现35内没有收到任何包，说明已经悄悄失联了，主动断开')
            return None
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            print('请联系开发者')
            return None
        
        return bytes_data
    
    async def ReceiveMessageLoop(self):
        while True:
            bytes_datas = await self.ReadSocketData()
            if bytes_datas is None:
                break
            len_read = 0
            len_bytes_datas = len(bytes_datas)
            while len_read != len_bytes_datas:
                state = None
                split_header = self.structer.unpack(bytes_datas[len_read:16+len_read])
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
                    state = self.handle_danmu(dic)
                # 握手确认
                elif opt == 8:
                    printer.info([f'{self.area_id}号弹幕监控进入房间（{self.roomid}）'], True)
                else:
                    printer.warn(bytes_datas[len_read:len_read + len_data])
                            
                if state is not None and not state:
                    return
                len_read += len_data
                
    def handle_danmu(self, dic):
        return True
    
    
class DanmuPrinter(BaseDanmu):
    def handle_danmu(self, dic):
        cmd = dic['cmd']
        # print(cmd)
        if cmd == 'DANMU_MSG':
            # print(dic)
            Printer().print_danmu(dic)
            return True


class DanmuRaffleHandler(BaseDanmu):
    def handle_danmu(self, dic):
        cmd = dic['cmd']
        
        if cmd == 'PREPARING':
            printer.info([f'{self.area_id}号弹幕监控房间下播({self.roomid})'], True)
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
                printer.info([f'{self.area_id}号弹幕监控检测到{real_roomid:^9}的{type_text}'], True)
                RaffleHandler().push2queue((real_roomid,), 'handle_TV_raffle')
                
        elif cmd == 'GUARD_MSG':
            if 'buy_type' in dic and dic['buy_type'] == 1:
                print(dic)
                roomid = dic['roomid']
                printer.info([f'{self.area_id}号弹幕监控检测到{roomid:^9}的总督'], True)
                RaffleHandler().push2queue((roomid,), 'handle_guard_raffle')
            if 'buy_type' in dic and dic['buy_type'] != 1:
                print(dic)
                printer.info([f'{self.area_id}号弹幕监控检测到{self.roomid:^9}的提督/舰长'], True)
                RaffleHandler().push2queue((self.roomid,), 'handle_guard_raffle')
                  
                    
class YjMonitorHandler(BaseDanmu):
    def handle_danmu(self, dic):
        cmd = dic['cmd']
        print(cmd)
        if cmd == 'DANMU_MSG':
            msg = dic['info'][1]
            if '-' in msg:
                list_word = msg.split('-')
                try:
                    roomid = int(list_word[0])
                    raffleid = int(list_word[1])
                    printer.info([f'弹幕监控检测到{roomid:^9}的提督/舰长{raffleid}'], True)
                    Task().call_after('handle_1_guard_raffle', 0, (roomid, raffleid), id=None, time_range=60)
                except ValueError:
                    print(msg)
            Printer().print_danmu(dic)                    
               
    

