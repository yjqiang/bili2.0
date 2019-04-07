# https://github.com/yjqiang/YjMonitor

import struct
import sys
import json
import asyncio

import utils
import printer
import bili_statistics
from .base_danmu import BaseDanmu
from tasks.guard_raffle_handler import GuardRaffleHandlerTask
from tasks.storm_raffle_handler import StormRaffleHandlerTask
from . import raffle_handler


class YjMonitorDanmu(BaseDanmu):
    def __init__(self, room_id, area_id, client_session=None):
        super().__init__(room_id, area_id, client_session)
        keys = '阝飠牜饣卩卪厸厶厽孓宀巛巜彳廴彡彐忄扌攵氵灬爫犭疒癶礻糹纟罒罓耂虍訁覀兦亼亽亖亗吂卝匸皕旡玊尐幵朩囘囙囜囝囟囡団囤囥囦囧囨囩囪囫囬囮囯困囱囲図囵囶囷囸囹固囻囼图囿圀圁圂圃圄圅圆圇圉圊圌圍圎圏圐圑園圓圔圕圖圗團圙圚圛圜圝圞'
        self.__reverse_keys = {value: i for i, value in enumerate(keys)}
        self.__read = {}
    
    def __base2dec(self, str_num, base=110):
        result = 0
        for i in str_num:
            result = result * base + self.__reverse_keys[i]
        return result
    
    def __reverse(self, msg):
        msg = msg.replace('?', '')
        first = self.__reverse_keys.get(msg[0], -1)
        last = self.__reverse_keys.get(msg[-1], -1)
        
        # 校验
        if 0 <= first <= 109 and 0 <= last <= 109 and not (first + last - 109):
            type = msg[-2]
            msg_id, id = map(self.__base2dec, msg[:-2].split('.'))
            return msg_id, type, id
        return None
        
    def __combine_piece(self, uid, msg):
        # None/''
        if not msg:
            return None
        if uid not in self.__read:
            self.__read[uid] = {}
        user_danmus = self.__read[uid]
        msg_id, type, id = msg
        msg_id_wanted = (msg_id - 1) if (msg_id % 2) else (msg_id + 1)
        id_wanted = user_danmus.pop(msg_id_wanted, None)
        if id_wanted is not None:
            if msg_id % 2:
                return type, id_wanted, id
            else:
                return type, id, id_wanted
        else:
            user_danmus[msg_id] = id
            return None
        
    def handle_danmu(self, dict_danmu):
        cmd = dict_danmu['cmd']
        # print(cmd)
        if cmd == 'DANMU_MSG':
            info = dict_danmu['info']
            ori = info[1]
            uid = info[2][0]
            # print('测试', self.__read, ori)
            try:
                msg = self.__reverse(ori)
                if msg is not None:
                    msg_id, type, id = msg
                    if type == '~' and not msg_id % 2:
                        raffle_id = id
                        printer.info([f'{self._area_id}号弹幕监控检测到{"0":^9}的节奏风暴(id: {raffle_id})'], True)
                        # raffle_handler.exec_at_once(StormRaffleHandlerTask, 0, raffle_id)
                        bili_statistics.add2pushed_raffles('Yj协同节奏风暴', 2)
                result = self.__combine_piece(uid, msg)
                if result is None:
                    return True
                type, raffle_id, real_roomid = result
                if type == '+':
                    printer.info([f'{self._area_id}号弹幕监控检测到{real_roomid:^9}的大航海(id: {raffle_id})'], True)
                    raffle_handler.push2queue(GuardRaffleHandlerTask, real_roomid, raffle_id)
                    bili_statistics.add2pushed_raffles('Yj协同大航海', 2)
            except Exception:
                printer.warn(f'Yj监控房间内可能有恶意干扰{uid}: {ori}')
        return True
        

class YjMonitorTcp:
    structer = struct.Struct('!I')

    def __init__(self, addr: dict, area_id, key, loop=None):
        # addr['host'] 格式为 '127.0.0.1'或者url，addr['port'] 为int端口号
        self._host = addr['host']
        self._port = addr['port']
        self._key = key
        if loop is not None:
            self._loop = loop
        else:
            self._loop = asyncio.get_event_loop()
            
        self._area_id = area_id
        
        # 建立连接过程中难以处理重设置房间或断线等问题
        self._conn_lock = asyncio.Lock()
        self._task_main = None
        self._waiting = None
        self._closed = False
        self._bytes_heartbeat = self._encapsulate(str_body='')
        
    def _encapsulate(self, str_body):
        body = str_body.encode('utf-8')
        len_body = len(body)
        header = self.structer.pack(len_body)
        return header + body

    async def _send_bytes(self, bytes_data):
        try:
            self._writer.write(bytes_data)
            await self._writer.drain()
        except asyncio.CancelledError:
            return False
        except:
            print(sys.exc_info()[0])
            return False
        return True

    async def _read_bytes(self, n):
        if n <= 0:
            return b''
        try:
            bytes_data = await asyncio.wait_for(
                self._reader.readexactly(n), timeout=40)
        except asyncio.TimeoutError:
            print('# 由于心跳包30s一次，但是发现35内没有收到任何包，说明已经悄悄失联了，主动断开')
            return None
        except:
            print(sys.exc_info()[0])
            return None
                
        return bytes_data
        
    async def _open_conn(self):
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=5)
        except asyncio.TimeoutError:
            print('连接超时')
            return False
        except:
            print("连接无法建立，请检查本地网络状况")
            print(sys.exc_info()[0])
            return False
        printer.info([f'{self._area_id}号弹幕监控已连接推送服务器'], True)
    
        dict_enter = {
            'code': 0,
            'type': 'ask',
            'data': {'key': self._key}
            }
        str_enter = json.dumps(dict_enter)
        bytes_enter = self._encapsulate(str_body=str_enter)
        
        return await self._send_bytes(bytes_enter)
        
    async def _close_conn(self):
        self._writer.close()
        # py3.7 才有（妈的你们真的磨叽）
        # await self._writer.wait_closed()
        
    async def _heart_beat(self):
        try:
            while True:
                if not await self._send_bytes(self._bytes_heartbeat):
                    return
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            return
            
    async def _read_datas(self):
        while True:
            header = await self._read_bytes(4)
            if header is None:
                return
            
            # 每片data都分为header和body，data和data可能粘连
            # data_l == header_l && next_data_l == next_header_l
            # ||header_l...header_r|body_l...body_r||next_data_l...
            len_body, = self.structer.unpack_from(header)
            
            body = await self._read_bytes(len_body)
            if body is None:
                return
            
            if not body:
                continue
            json_data = json.loads(body.decode('utf-8'))
            # 人气值(或者在线人数或者类似)以及心跳
            data_type = json_data['type']
            if data_type == 'raffle':
                if not self.handle_danmu(json_data['data']):
                    return
            # 握手确认
            elif data_type == 'entered':
                printer.info(
                        [f'{self._area_id}号推送监控确认连接'], True)
            elif data_type == 'error':
                printer.warn(f'发生致命错误{json_data}')
                await asyncio.sleep(3)
                
    def handle_danmu(self, data):
        raffle_type = data['raffle_type']
        if raffle_type == 'STORM':
            raffle_id = data['raffle_id']
            raffle_roomid = 0
            printer.info([f'{self._area_id}号弹幕监控检测到{"0":^9}的节奏风暴(id: {raffle_id})'], True)
            # raffle_handler.exec_at_once(StormRaffleHandlerTask, 0, raffle_id)
            bili_statistics.add2pushed_raffles('Yj协同节奏风暴', 2)
        elif raffle_type == 'GUARD':
            raffle_id = data['raffle_id']
            raffle_roomid = data['room_id']
            printer.info([f'{self._area_id}号弹幕监控检测到{raffle_roomid:^9}的大航海(id: {raffle_id})'], True)
            raffle_handler.push2queue(GuardRaffleHandlerTask, raffle_roomid, raffle_id)
            bili_statistics.add2pushed_raffles('Yj协同大航海', 2)
        return True
        
    async def run_forever(self):
        self._waiting = self._loop.create_future()
        time_now = 0
        while not self._closed:
            if utils.curr_time() - time_now <= 3:
                printer.info([f'网络波动，{self._area_id}号弹幕姬延迟3秒后重启'], True)
                await asyncio.sleep(3)
            printer.info([f'正在启动{self._area_id}号弹幕姬'], True)
            time_now = utils.curr_time()
            
            async with self._conn_lock:
                if self._closed:
                    break
                if not await self._open_conn():
                    continue
                self._task_main = asyncio.ensure_future(self._read_datas())
                task_heartbeat = asyncio.ensure_future(self._heart_beat())
            tasks = [self._task_main, task_heartbeat]
            _, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED)
            printer.info([f'{self._area_id}号弹幕姬异常或主动断开，正在处理剩余信息'], True)
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            await self._close_conn()
            if pending:
                await asyncio.wait(pending)
            printer.info([f'{self._area_id}号弹幕姬退出，剩余任务处理完毕'], True)
        self._waiting.set_result(True)
            
    async def close(self):
        if not self._closed:
            self._closed = True
            async with self._conn_lock:
                if self._writer is not None:
                    await self._close_conn()
            if self._waiting is not None:
                await self._waiting
            return True
        else:
            return False

