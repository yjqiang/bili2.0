import asyncio
import danmu
import time
import printer


def CurrentTime():
    currenttime = int(time.time())
    return currenttime


class connect():
    __slots__ = ('danmuji', 'room_id', 'area_id')
    instance = None
    
    def __new__(cls, room_id=None):
        if not cls.instance:
            cls.instance = super(connect, cls).__new__(cls)
            cls.instance.danmuji = None
            cls.instance.room_id = room_id
            cls.instance.area_id = -1
        return cls.instance
        
    async def run(self):
        self.danmuji = danmu.DanmuPrinter(self.room_id, self.area_id)
        time_now = 0
        while True:
            if int(CurrentTime()) - time_now <= 3:
                printer.info(['当前网络不稳定，弹幕监控将自动延迟3秒后重启'], True)
                await asyncio.sleep(3)
            printer.info(['正在启动直播监控弹幕姬'], True)
            time_now = int(CurrentTime())
            connect_results = await self.danmuji.open()
            if not connect_results:
                continue
            task_main = asyncio.ensure_future(self.danmuji.read_datas())
            task_heartbeat = asyncio.ensure_future(self.danmuji.heart_beat())
            tasks = [task_main, task_heartbeat]
            finished, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            printer.info(['主弹幕姬异常或主动断开，正在处理剩余信息'], True)
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            await self.danmuji.close()
            await asyncio.wait(pending)
            printer.info(['主弹幕姬退出，剩余任务处理完毕'], True)
    
    async def reconnect(self, room_id):
        self.room_id = room_id
        print('已经切换room_id')
        if self.danmuji is not None:
            self.danmuji.room_id = room_id
            await self.danmuji.close()
        
        
class RaffleConnect():
    def __init__(self, areaid):
        self.danmuji = None
        self.room_id = None
        self.areaid = areaid
        
    async def run(self):
        self.danmuji = danmu.DanmuRaffleHandler(self.room_id, self.areaid)
        time_now = 0
        while True:
            if int(CurrentTime()) - time_now <= 3:
                printer.info(['当前网络不稳定，弹幕监控将自动延迟3秒后重启'], True)
                await asyncio.sleep(3)
            await self.danmuji.reset_roomid()

            printer.info(['正在启动抽奖监控弹幕姬'], True)
            time_now = int(CurrentTime())
            connect_results = await self.danmuji.open()
            if not connect_results:
                continue
            task_main = asyncio.ensure_future(self.danmuji.read_datas())
            task_heartbeat = asyncio.ensure_future(self.danmuji.heart_beat())
            task_checkarea = asyncio.ensure_future(self.danmuji.check_area())
            tasks = [task_main, task_heartbeat, task_checkarea]
            finished, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            printer.info([f'{self.areaid}号弹幕姬异常或主动断开，正在处理剩余信息'], True)
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            if not task_checkarea.done():
                task_checkarea.cancel()
            await self.danmuji.close()
            await asyncio.wait(pending)
            printer.info([f'{self.areaid}号弹幕姬退出，剩余任务处理完毕'], True)

                                
class YjConnection():
    def __init__(self, room_id):
        self.danmuji = None
        self.room_id = room_id
        self.areaid = 0
        
    async def run(self):
        if not self.room_id:
            return
        self.danmuji = danmu.YjMonitorHandler(self.room_id, self.areaid)
        time_now = 0
        while True:
            if int(CurrentTime()) - time_now <= 3:
                printer.info(['当前网络不稳定，弹幕监控将自动延迟3秒后重启'], True)
                await asyncio.sleep(3)
            printer.info(['正在启动Yj监控弹幕姬'], True)
            time_now = int(CurrentTime())
            connect_results = await self.danmuji.open()
            if not connect_results:
                continue
            task_main = asyncio.ensure_future(self.danmuji.read_datas())
            task_heartbeat = asyncio.ensure_future(self.danmuji.heart_beat())
            tasks = [task_main, task_heartbeat]
            finished, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            printer.info(['Yj弹幕姬异常或主动断开，正在处理剩余信息'], True)
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            await self.danmuji.close()
            await asyncio.wait(pending)
            printer.info(['Yj弹幕姬退出，剩余任务处理完毕'], True)
            
            

        
                    
