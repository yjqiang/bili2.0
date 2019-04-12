# https://github.com/yjqiang/YjMonitor

import json
from struct import Struct
from typing import Optional

from aiohttp import ClientSession

from printer import info as print
from printer import warn
import bili_statistics
from .bili_danmu import WsDanmuClient
from .client import Client
from .conn import TcpConn
from tasks.guard_raffle_handler import GuardRaffleHandlerTask
from tasks.storm_raffle_handler import StormRaffleHandlerTask
from . import raffle_handler


class YjMonitorDanmu(WsDanmuClient):
    def __init__(
            self, room_id: int, area_id: int,
            session: Optional[ClientSession] = None, loop=None):
        super().__init__(
            room_id=room_id,
            area_id=area_id,
            session=session,
            loop=loop
        )
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
                        print(f'{self._area_id}号弹幕监控检测到{"0":^9}的节奏风暴(id: {raffle_id})')
                        # raffle_handler.exec_at_once(StormRaffleHandlerTask, 0, raffle_id)
                        bili_statistics.add2pushed_raffles('Yj协同节奏风暴', 2)
                result = self.__combine_piece(uid, msg)
                if result is None:
                    return True
                type, raffle_id, real_roomid = result
                if type == '+':
                    print(f'{self._area_id}号弹幕监控检测到{real_roomid:^9}的大航海(id: {raffle_id})')
                    raffle_handler.push2queue(GuardRaffleHandlerTask, real_roomid, raffle_id)
                    bili_statistics.add2pushed_raffles('Yj协同大航海', 2)
            except Exception:
                warn(f'Yj监控房间内可能有恶意干扰{uid}: {ori}')
        return True


class TcpYjMonitorClient(Client):
    header_struct = Struct('>I')

    def __init__(
            self, key: str, url: str, area_id: int, loop=None):
        heartbeat = 30.0
        conn = TcpConn(
            url=url,
            receive_timeout=heartbeat + 10)
        super().__init__(
            area_id=area_id,
            conn=conn,
            heartbeat=heartbeat,
            loop=loop)
        self._key = key

        self._bytes_heartbeat = self._encapsulate(str_body='')
        self._funcs_task.append(self._send_heartbeat)

    @property
    def _hello(self):
        dict_enter = {
            'code': 0,
            'type': 'ask',
            'data': {'key': self._key}
        }
        str_enter = json.dumps(dict_enter)
        bytes_enter = self._encapsulate(str_body=str_enter)
        return bytes_enter

    def _encapsulate(self, str_body):
        body = str_body.encode('utf-8')
        len_body = len(body)
        header = self.header_struct.pack(len_body)
        return header + body

    async def _read_datas(self):
        while True:
            header = await self._conn.read_bytes(4)
            # 本函数对bytes进行相关操作，不特别声明，均为bytes
            if header is None:
                return

            len_body, = self.header_struct.unpack_from(header)

            # 心跳回复
            if not len_body:
                print('yj,heartbeat')
                continue

            body = await self._conn.read_json(len_body)
            if body is None:
                return

            json_data = body

            data_type = json_data['type']
            if data_type == 'raffle':
                if not self.handle_danmu(json_data['data']):
                    return
            # 握手确认
            elif data_type == 'entered':
                print(f'{self._area_id}号数据连接确认建立连接（{self._key}）')
            elif data_type == 'error':
                print(f'{self._area_id}号数据连接发生致命错误{json_data}')
                return

    def handle_danmu(self, data: dict):
        raffle_type = data['raffle_type']
        if raffle_type == 'STORM':
            raffle_id = data['raffle_id']
            raffle_roomid = 0
            print(f'{self._area_id}号弹幕监控检测到{raffle_roomid:^9}的节奏风暴(id: {raffle_id})')
            # raffle_handler.exec_at_once(StormRaffleHandlerTask, 0, raffle_id)
            bili_statistics.add2pushed_raffles('Yj协同节奏风暴', 2)
        elif raffle_type == 'GUARD':
            raffle_id = data['raffle_id']
            raffle_roomid = data['room_id']
            print(f'{self._area_id}号弹幕监控检测到{raffle_roomid:^9}的大航海(id: {raffle_id})')
            raffle_handler.push2queue(GuardRaffleHandlerTask, raffle_roomid, raffle_id)
            bili_statistics.add2pushed_raffles('Yj协同大航海', 2)
        return True
