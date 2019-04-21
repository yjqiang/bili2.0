import asyncio

from printer import info as print
from .conn import Conn


class Client:
    def __init__(
            self, area_id: int, conn: Conn, heartbeat: float = 30.0, loop=None):
        if loop is not None:
            self._loop = loop
        else:
            self._loop = asyncio.get_event_loop()
         
        self._area_id = area_id
        self._conn = conn
            
        # 建立连接过程中难以处理重设置房间或断线等问题
        self._conn_lock = asyncio.Lock()
        self._task_main = None
        self._waiting = None
        self._closed = False
        
        self._bytes_heartbeat = b''
        self._heartbeat = heartbeat
        
        self._func_main_task = self._read_datas
        # 除了main_task
        self._funcs_task = []
    
    @property
    def _hello(self):
        return b''
        
    async def _open(self):
        if await self._conn.open():
            return await self._conn.send_bytes(self._hello)
        return False
        
    async def _close(self):
        await self._conn.close()
        
    async def _send_heartbeat(self):
        try:
            while True:
                if not await self._conn.send_bytes(self._bytes_heartbeat):
                    return
                await asyncio.sleep(self._heartbeat)
        except asyncio.CancelledError:
            return

    async def _prepare_client(self):
        pass
            
    async def _read_datas(self):
        while True:
            pass
                        
    async def run_forever(self):
        self._waiting = self._loop.create_future()
        while not self._closed:
            print(f'正在启动{self._area_id}号数据连接')
            
            async with self._conn_lock:
                if self._closed:
                    break

                await self._prepare_client()
                if not await self._open():
                    continue
                
                tasks = [asyncio.ensure_future(i()) for i in self._funcs_task]
                self._task_main = asyncio.ensure_future(self._func_main_task())
                tasks.append(self._task_main)
                
            _, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED)
            print(f'{self._area_id}号数据连接异常或主动断开，正在处理剩余信息')
            for i in tasks:
                if i != self._task_main and not i.done():
                    i.cancel()
            await self._close()
            if pending:
                await asyncio.wait(pending)
            print(f'{self._area_id}号数据连接退出，剩余任务处理完毕')
        self._waiting.set_result(True)
            
    async def close(self):
        if not self._closed:
            self._closed = True
            async with self._conn_lock:
                await self._close()
            if self._waiting is not None:
                await self._waiting
            await self._conn.clean()
            return True
        else:
            return False
