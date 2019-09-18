import asyncio
from typing import Optional

from .conn import Conn
from printer import info as print


class Client:
    def __init__(
            self, area_id: int, conn: Conn, heartbeat: float = 30.0, loop: Optional[asyncio.AbstractEventLoop] = None):
        if loop is not None:
            self._loop = loop
        else:
            self._loop = asyncio.get_event_loop()

        self._area_id = area_id
        self._conn = conn

        # 建立连接过程中难以处理重设置房间或断线等问题
        self._conn_lock = asyncio.Lock()
        self._task_main = None
        self._waiting_end: Optional[asyncio.Future] = None
        self._waiting_pause: Optional[asyncio.Future] = None
        self._closed = False

        self._bytes_heartbeat = b''
        self._heartbeat = heartbeat

        self._func_main_task = self._read_datas
        # 除了main_task
        self._funcs_task = []

    @property
    def _hello(self):
        return b''

    # 建立连接并且发生初始化信息
    async def _open(self):
        if await self._conn.open():
            return await self._conn.send_bytes(self._hello)
        return False

    # 关闭当前连接，client不管
    async def _close(self):
        await self._conn.close()

    # 心跳
    async def _send_heartbeat(self):
        try:
            while True:
                if not await self._conn.send_bytes(self._bytes_heartbeat):
                    return
                await asyncio.sleep(self._heartbeat)
        except asyncio.CancelledError:
            return

    # 循环读取
    async def _read_datas(self):
        while self._waiting_pause is None:
            if not await self._read_one():
                return

    # 读一次数据（完整数据包括头尾）
    async def _read_one(self) -> bool:
        return True

    async def _prepare_client(self) -> bool:
        return True

    async def run(self):
        self._waiting_end = self._loop.create_future()
        while not self._closed:
            print(f'正在启动{self._area_id}号数据连接')
            if self._waiting_pause is not None:
                print(f'暂停启动{self._area_id}号数据连接，等待RESUME指令')
                await self._waiting_pause
            async with self._conn_lock:
                if self._closed or not await self._prepare_client():
                    print(f'{self._area_id}号数据连接确认收到关闭信号，正在处理')
                    break
                if not await self._open():
                    continue

                tasks = [self._loop.create_task(i()) for i in self._funcs_task]
                self._task_main = self._loop.create_task(self._func_main_task())
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
        self._waiting_end.set_result(True)

    def pause(self):
        if self._waiting_pause is None:
            self._waiting_pause = self._loop.create_future()

    def resume(self):
        if self._waiting_pause is not None:
            self._waiting_pause.set_result(True)
            self._waiting_pause = None

    async def close(self):
        if not self._closed:
            self._closed = True
            async with self._conn_lock:
                await self._close()
            if self._waiting_end is not None:
                await self._waiting_end
            await self._conn.clean()
            return True
        return False
