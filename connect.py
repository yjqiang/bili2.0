import asyncio
from bilibiliCilent import bilibiliClient
from task import Task
import datetime
import time
import printer


def CurrentTime():
    currenttime = int(time.mktime(datetime.datetime.now().timetuple()))
    return currenttime


class connect():
    __slots__ = ('danmuji', 'roomid')
    instance = None
    
    def __new__(cls, roomid=None):
        if not cls.instance:
            cls.instance = super(connect, cls).__new__(cls)
            cls.instance.danmuji = None
            cls.instance.roomid = roomid
        return cls.instance
        
    async def run(self):
        self.danmuji = bilibiliClient(self.roomid, 0)
        while True:
            print('# 正在启动直播监控弹幕姬')
            time_start = int(CurrentTime())
            connect_results = await self.danmuji.connectServer()
            # print(connect_results)
            if not connect_results:
                continue
            task_main = asyncio.ensure_future(self.danmuji.ReceiveMessageLoop())
            task_heartbeat = asyncio.ensure_future(self.danmuji.HeartbeatLoop())
            finished, pending = await asyncio.wait([task_main, task_heartbeat], return_when=asyncio.FIRST_COMPLETED)
            print('主弹幕姬异常或主动断开，正在处理剩余信息')
            time_end = int(CurrentTime())
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            task_terminate = asyncio.ensure_future(self.danmuji.close_connection())
            await asyncio.wait(pending)
            await asyncio.wait([task_terminate])
            printer.info(['主弹幕姬退出，剩余任务处理完毕'], True)
            if time_end - time_start < 5:
                print('# 当前网络不稳定，为避免频繁不必要尝试，将自动在5秒后重试')
                await asyncio.sleep(5)
    
    async def reconnect(self, roomid):
        self.roomid = roomid
        print('已经切换roomid')
        if self.danmuji is not None:
            self.danmuji.roomid = roomid
            await self.danmuji.close_connection()
        
        
class RaffleConnect():
    def __init__(self, areaid):
        self.danmuji = None
        self.roomid = None
        self.areaid = areaid
        
    async def run(self):
        self.danmuji = bilibiliClient(self.roomid, self.areaid)
        while True:
            self.danmuji.roomid = await Task().call_right_now('get_one', self.areaid)
            printer.info(['# 正在启动抽奖监控弹幕姬'], True)
            time_start = int(CurrentTime())
            connect_results = await self.danmuji.connectServer()
            # print(connect_results)
            if not connect_results:
                continue
            task_main = asyncio.ensure_future(self.danmuji.ReceiveMessageLoop())
            task_heartbeat = asyncio.ensure_future(self.danmuji.HeartbeatLoop())
            task_checkarea = asyncio.ensure_future(self.danmuji.CheckArea())
            finished, pending = await asyncio.wait([task_main, task_heartbeat, task_checkarea], return_when=asyncio.FIRST_COMPLETED)
            printer.info([f'{self.areaid}号弹幕姬异常或主动断开，正在处理剩余信息'], True)
            time_end = int(CurrentTime())
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            if not task_checkarea.done():
                task_checkarea.cancel()
            task_terminate = asyncio.ensure_future(self.danmuji.close_connection())
            await asyncio.wait(pending)
            await asyncio.wait([task_terminate])
            printer.info([f'{self.areaid}号弹幕姬退出，剩余任务处理完毕'], True)
            if time_end - time_start < 5:
                print('# 当前网络不稳定，为避免频繁不必要尝试，将自动在5秒后重试')
                await asyncio.sleep(5)
            
            

        
                    
