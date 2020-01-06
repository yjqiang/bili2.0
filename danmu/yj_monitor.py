# https://github.com/yjqiang/YjMonitor

import json
import asyncio
from struct import Struct

from printer import info as print
from printer import warn
import bili_statistics
from .client import Client
from .conn import TcpConn
from tasks.guard_raffle_handler import GuardRafflJoinTask
from tasks.storm_raffle_handler import StormRaffleJoinTask
from tasks.pk_raffle_handler import PkRaffleJoinTask
from tasks.tv_raffle_handler import TvRaffleJoinTask
from . import raffle_handler


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

    async def _read_one(self) -> bool:
        header = await self._conn.read_bytes(4)
        # 本函数对bytes进行相关操作，不特别声明，均为bytes
        if header is None:
            return False

        len_body, = self.header_struct.unpack_from(header)

        # 心跳回复
        if not len_body:
            return True

        body = await self._conn.read_json(len_body)
        if body is None:
            return False

        json_data = body

        data_type = json_data['type']
        if data_type == 'raffle':
            return self.handle_danmu(json_data['data'])
        # 握手确认
        elif data_type == 'entered':
            print(f'{self._area_id}号数据连接确认建立连接（{self._key}）')
        elif data_type == 'error':
            warn(f'{self._area_id}号数据连接发生致命错误{json_data}')
            await asyncio.sleep(1.0)
            return False
        return True

    def handle_danmu(self, data: dict):
        raffle_type = data['raffle_type']
        raffle_id = data['raffle_id']
        raffle_roomid = data['room_id']
        if raffle_type == 'STORM':
            print(f'{self._area_id}号数据连接检测到{raffle_roomid:^9}的节奏风暴(id: {raffle_id})')
            raffle_handler.exec_at_once(StormRaffleJoinTask, 0, raffle_id)
            bili_statistics.add2pushed_raffles('Yj协同节奏风暴', 2)
        elif raffle_type == 'GUARD':
            print(f'{self._area_id}号数据连接检测到{raffle_roomid:^9}的大航海(id: {raffle_id})')
            raffle_handler.push2queue(GuardRafflJoinTask, raffle_roomid, raffle_id)
            bili_statistics.add2pushed_raffles('Yj协同大航海', 2)
        elif raffle_type == 'PK':
            print(f'{self._area_id}号数据连接检测到{raffle_roomid:^9}的大乱斗(id: {raffle_id})')
            raffle_handler.push2queue(PkRaffleJoinTask, raffle_roomid)
            bili_statistics.add2pushed_raffles('Yj协同大乱斗', 2)
        elif raffle_type == 'TV':
            print(f'{self._area_id}号数据连接检测到{raffle_roomid:^9}的小电视(id: {raffle_id})')
            json_rsp = {
                'data': {
                    'gift': [data['other_raffle_data']]
                }
            }
            # dict 不可以用于 raffle_handler.py 的 set 机制
            raffle_handler.exec_at_once(TvRaffleJoinTask, raffle_roomid, json_rsp)
            bili_statistics.add2pushed_raffles('Yj协同小电视', 2)
        return True
