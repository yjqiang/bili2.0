import json
from struct import Struct
from typing import Optional

from aiohttp import ClientSession

from printer import info as print
from .client import Client
from .conn import WsConn


class WsDanmuClient(Client):
    header_struct = Struct('>I2H2I')

    def __init__(
            self, room_id: int, area_id: int,
            session: Optional[ClientSession] = None, loop=None):
        heartbeat = 30.0
        conn = WsConn(
            url='wss://broadcastlv.chat.bilibili.com:443/sub',
            receive_timeout=heartbeat + 10,
            session=session)
        super().__init__(
            area_id=area_id,
            conn=conn,
            heartbeat=heartbeat,
            loop=loop)
        self._room_id = room_id

        self._bytes_heartbeat = self._encapsulate(opt=2, str_body='')
        self._funcs_task.append(self._send_heartbeat)

    @property
    def room_id(self):
        return self._room_id

    @property
    def _hello(self):
        str_enter = f'{{"uid":0,"roomid":{self._room_id},"protover":1,"platform":"web","clientver":"1.3.3"}}'
        bytes_enter = self._encapsulate(opt=7, str_body=str_enter)
        return bytes_enter

    def _encapsulate(self, opt, str_body, len_header=16, ver=1, seq=1):
        body = str_body.encode('utf-8')
        len_data = len(body) + len_header
        header = self.header_struct.pack(len_data, len_header, ver, opt, seq)
        return header + body

    async def _read_one(self) -> bool:
        datas = await self._conn.read_bytes()
        # 本函数对bytes进行相关操作，不特别声明，均为bytes
        if datas is None:
            return False
        data_l = 0
        len_datas = len(datas)
        while data_l != len_datas:
            # 每片data都分为header和body，data和data可能粘连
            # data_l == header_l && next_data_l == next_header_l
            # ||header_l...header_r|body_l...body_r||next_data_l...
            tuple_header = self.header_struct.unpack_from(datas[data_l:])
            len_data, len_header, _, opt, _ = tuple_header
            body_l = data_l + len_header
            next_data_l = data_l + len_data
            body = datas[body_l:next_data_l]
            # 人气值(或者在线人数或者类似)以及心跳
            if opt == 3:
                # num_watching, = struct.unpack('!I', body)
                pass
            # cmd
            elif opt == 5:
                if not self.handle_danmu(json.loads(body.decode('utf-8'))):
                    return False
            # 握手确认
            elif opt == 8:
                print(f'{self._area_id}号数据连接进入房间（{self._room_id}）')
            else:
                return False

            data_l = next_data_l
        return True

    def handle_danmu(self, data: dict) -> bool:
        return True

    async def reset_roomid(self, room_id):
        async with self._conn_lock:
            # not None是判断是否已经连接了的(重连过程中也可以处理)
            await self._conn.close()
            if self._task_main is not None:
                await self._task_main
            # 由于锁的存在，绝对不可能到达下一个的自动重连状态，这里是保证正确显示当前监控房间号
            self._room_id = room_id
            print(f'{self._area_id}号数据连接已经切换房间（{room_id}）')
