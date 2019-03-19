import asyncio
import struct
import sys
import json
import aiohttp
import utils
import printer


class BaseDanmu:
    structer = struct.Struct('!I2H2I')

    def __init__(self, room_id, area_id, session=None, loop=None):
        if session is None:
            self._is_sharing_session = False
            self._session = aiohttp.ClientSession()
        else:
            self._is_sharing_session = True
            self._session = session
        self._ws = None
        
        if loop is not None:
            self._loop = loop
        else:
            self._loop = asyncio.get_event_loop()
        
        self._area_id = area_id
        self._room_id = room_id
        # 建立连接过程中难以处理重设置房间或断线等问题
        self._conn_lock = asyncio.Lock()
        self._task_main = None
        self._waiting = None
        self._closed = False
        self._bytes_heartbeat = self._encapsulate(opt=2, str_body='')
    
    @property
    def room_id(self):
        return self._room_id
        
    # 命名取自网络协议中的数据封装
    def _encapsulate(self, opt, str_body, len_header=16, ver=1, seq=1):
        body = str_body.encode('utf-8')
        len_data = len(body) + len_header
        header = self.structer.pack(len_data, len_header, ver, opt, seq)
        return header + body

    async def _send_bytes(self, bytes_data):
        try:
            await self._ws.send_bytes(bytes_data)
        except asyncio.CancelledError:
            return False
        except:
            print(sys.exc_info()[0])
            return False
        return True

    async def _read_bytes(self):
        try:
            # 如果调用aiohttp的bytes read，none的时候，会raise exception
            # timeout目的是b站30s间隔的心跳包会有确认返回，如果没了，当然就是gg
            msg = await asyncio.wait_for(self._ws.receive(), timeout=35)
            bytes_data = msg.data
        except asyncio.TimeoutError:
            print('# 由于心跳包30s一次，但是发现35内没有收到任何包，说明已经悄悄失联了，主动断开')
            return None
        except:
            print(sys.exc_info()[0])
            return None
        
        return bytes_data
        
    async def _open_conn(self):
        try:
            url = 'wss://broadcastlv.chat.bilibili.com:443/sub'
            self._ws = await asyncio.wait_for(
                self._session.ws_connect(url), timeout=3)
        except asyncio.TimeoutError:
            print('连接超时')
            return False
        except:
            print("连接无法建立，请检查本地网络状况")
            print(sys.exc_info()[0])
            return False
        printer.info([f'{self._area_id}号弹幕监控已连接b站服务器'], True)
        
        str_enter = f'{{"uid":0,"roomid":{self._room_id},"protover":1,"platform":"web","clientver":"1.3.3"}}'
        bytes_enter = self._encapsulate(opt=7, str_body=str_enter)
        return await self._send_bytes(bytes_enter)
        
    # 看了一下api，这玩意儿应该除了cancel其余都是暴力处理的，不会raise
    async def _close_conn(self):
        await self._ws.close()
        
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
            datas = await self._read_bytes()
            # 本函数对bytes进行相关操作，不特别声明，均为bytes
            if datas is None:
                return
            data_l = 0
            len_datas = len(datas)
            while data_l != len_datas:
                # 每片data都分为header和body，data和data可能粘连
                # data_l == header_l && next_data_l == next_header_l
                # ||header_l...header_r|body_l...body_r||next_data_l...
                tuple_header = self.structer.unpack_from(datas[data_l:])
                len_data, len_header, _, opt, _ = tuple_header
                body_l = data_l + len_header
                next_data_l = data_l + len_data
                body = datas[body_l:next_data_l]
                # 人气值(或者在线人数或者类似)以及心跳
                if opt == 3:
                    # num_watching, = struct.unpack('!I', body)
                    # print(f'弹幕心跳检测{self._area_id}')
                    pass
                # cmd
                elif opt == 5:
                    if not self.handle_danmu(json.loads(body.decode('utf-8'))):
                        return
                # 握手确认
                elif opt == 8:
                    printer.info(
                        [f'{self._area_id}号弹幕监控进入房间（{self._room_id}）'], True)
                else:
                    printer.warn(f'弹幕数据错误:{datas}')
                    return

                data_l = next_data_l
                
    def handle_danmu(self, body):
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
            await asyncio.wait(pending)
            printer.info([f'{self._area_id}号弹幕姬退出，剩余任务处理完毕'], True)
        self._waiting.set_result(True)
            
    async def reset_roomid(self, room_id):
        async with self._conn_lock:
            # not None是判断是否已经连接了的(重连过程中也可以处理)
            if self._ws is not None:
                await self._close_conn()
            if self._task_main is not None:
                await self._task_main
            # 由于锁的存在，绝对不可能到达下一个的自动重连状态，这里是保证正确显示当前监控房间号
            self._room_id = room_id
            printer.info([f'{self._area_id}号弹幕姬已经切换房间（{room_id}）'], True)
            
    async def close(self):
        if not self._closed:
            self._closed = True
            async with self._conn_lock:
                if self._ws is not None:
                    await self._close_conn()
            if self._waiting is not None:
                await self._waiting
            if not self._is_sharing_session:
                await self._session.close()
            return True
        else:
            return False

