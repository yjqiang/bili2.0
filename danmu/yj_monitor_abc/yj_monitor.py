# https://github.com/yjqiang/YjMonitor
import json

from danmu_abc import TcpConn, Client

from .utils import Header, Pack
from printer import info as print
from printer import warn


class TcpDanmuClient(Client):
    __slots__ = ('_key', '_pack_heartbeat')

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
            loop=loop,
            logger_info=print)
        self._key = key

        self._pack_heartbeat = Pack.pack(str_body='')

    async def _one_hello(self) -> bool:
        dict_enter = {
            'code': 0,
            'type': 'ask',
            'data': {'key': self._key}
            }
        str_enter = json.dumps(dict_enter)
        return await self._conn.send_bytes(Pack.pack(str_body=str_enter))

    async def _one_heartbeat(self) -> bool:
        return await self._conn.send_bytes(self._pack_heartbeat)

    async def _one_read(self) -> bool:
        header = await self._conn.read_bytes(Header.raw_header_size)
        if header is None:
            return False

        len_body, = Header.unpack(header)

        # 心跳回复
        if not len_body:
            # print('heartbeat')
            return True

        json_body = await self._conn.read_json(len_body)
        if json_body is None:
            return False

        data_type = json_body['type']
        if data_type == 'raffle':
            if not self.handle_danmu(json_body['data']):
                return False
        # 握手确认
        elif data_type == 'entered':
            print(f'{self._area_id} 号数据连接确认建立连接（{self._key}）')
        elif data_type == 'error':
            warn(f'{self._area_id} 号数据连接发生致命错误{json_body}')
            self._closed = True  # 内部关闭，不再重连
            return False
        return True

    def handle_danmu(self, data: dict) -> bool:
        print(f'{self._area_id} 号数据连接:', data)
        return True

    async def run(self):
        await self.run_forever()
