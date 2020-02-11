import json
from typing import Optional

from aiohttp import ClientSession
from danmu_abc import WsConn, Client

from printer import info as print
from danmu.bili_abc.utils import Pack, Opt


class WsDanmuClient(Client):
    __slots__ = ('_room_id', '_pack_heartbeat')

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
            loop=loop,
            logger_info=print
        )
        self._room_id = room_id

        self._pack_heartbeat = Pack.pack('', opt=Opt.HEARTBEAT, ver=1, seq=1)

    @property
    def room_id(self):
        return self._room_id

    async def _one_hello(self) -> bool:
        dict_enter = {
            'uid': 0,
            'roomid': self._room_id,
            'protover': 1,
            'platform': 'web',
            'clientver': '1.3.3'
        }
        str_enter = json.dumps(dict_enter)
        return await self._conn.send_bytes(Pack.pack(str_enter, opt=Opt.AUTH, ver=1, seq=1))

    async def _one_heartbeat(self) -> bool:
        return await self._conn.send_bytes(self._pack_heartbeat)

    async def _one_read(self) -> bool:
        packs = await self._conn.read_bytes()

        if packs is None:
            return False

        for opt, body in Pack.unpack(packs):
            if not self.parse_body(body, opt):
                return False
        return True

    def parse_body(self, body: bytes, opt: int) -> bool:
        # 人气值(或者在线人数或者类似)以及心跳
        if opt == Opt.HEARTBEAT_REPLY:
            pass
        # cmd
        elif opt == Opt.SEND_MSG_REPLY:
            if not self.handle_danmu(json.loads(body.decode('utf-8'))):
                return False
        # 握手确认
        elif opt == Opt.AUTH_REPLY:
            print(f'{self._area_id} 号数据连接进入房间（{self._room_id}）')
        else:
            print('?????', body)
            return False
        return True

    def handle_danmu(self, data: dict) -> bool:
        print(f'{self._area_id} 号数据连接:', data)
        return True

    async def reset_roomid(self, room_id):
        async with self._opening_lock:
            # not None是判断是否已经连接了的(重连过程中也可以处理)
            await self._job_close()
            if self._task_main is not None:
                await self._task_main
            # 由于锁的存在，绝对不可能到达下一个的自动重连状态，这里是保证正确显示当前监控房间号
            self._room_id = room_id
            print(f'{self._area_id} 号数据连接已经切换房间（{room_id}）')

    async def run(self):
        await self.run_forever()
