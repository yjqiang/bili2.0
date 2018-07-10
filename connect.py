import asyncio
from bilibiliCilent import bilibiliClient
from super_user import SuperUser
import datetime
import time



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
        while True:
            print('# 正在启动直播监控弹幕姬')
            time_start = int(CurrentTime())
            self.danmuji = bilibiliClient(self.roomid, 0)
            connect_results = await self.danmuji.connectServer()
            # print(connect_results)
            if not connect_results:
                continue
            task_main = asyncio.ensure_future(self.danmuji.ReceiveMessageLoop())
            task_heartbeat = asyncio.ensure_future(self.danmuji.HeartbeatLoop())
            finished, pending = await asyncio.wait([task_main, task_heartbeat], return_when=asyncio.FIRST_COMPLETED)
            print('# 弹幕姬异常或主动断开，处理完剩余信息后重连')
            self.danmuji.connected = False
            time_end = int(CurrentTime())
            if not task_heartbeat.done():
                task_heartbeat.cancel()
                await self.danmuji.close_connection()
                print('# 弹幕主程序退出，立即取消心跳模块')
            else:
                await asyncio.wait(pending)
                print('# 弹幕心跳模块退出，主程序剩余任务处理完毕')
            if time_end - time_start < 5:
                print('# 当前网络不稳定，为避免频繁不必要尝试，将自动在5秒后重试')
                await asyncio.sleep(5)
    
    async def reconnect(self, roomid):
        self.roomid = roomid
        print('已经切换roomid')
        if self.danmuji is not None:
            await self.danmuji.close_connection()
        
        
class RaffleConnect():
    def __init__(self, areaid):
        self.danmuji = None
        self.roomid = None
        self.areaid = areaid
        
    async def run(self):
        while True:
            self.roomid = await SuperUser().get_one(self.areaid)
            print('# 正在启动抽奖监控弹幕姬')
            time_start = int(CurrentTime())
            self.danmuji = bilibiliClient(self.roomid, self.areaid)
            connect_results = await self.danmuji.connectServer()
            # print(connect_results)
            if not connect_results:
                continue
            task_main = asyncio.ensure_future(self.danmuji.ReceiveMessageLoop())
            task_heartbeat = asyncio.ensure_future(self.danmuji.HeartbeatLoop())
            task_checkarea = asyncio.ensure_future(self.danmuji.CheckArea())
            finished, pending = await asyncio.wait([task_main, task_heartbeat, task_checkarea], return_when=asyncio.FIRST_COMPLETED)
            print('# 弹幕姬异常或主动断开，处理完剩余信息后重连')
            self.danmuji.connected = False
            time_end = int(CurrentTime())
            if not task_heartbeat.done():
                task_heartbeat.cancel()
                await self.danmuji.close_connection()
                print('# 弹幕主程序退出，立即取消心跳模块')
            else:
                await asyncio.wait(pending)
                print('# 弹幕心跳模块退出，主程序剩余任务处理完毕')
            if time_end - time_start < 5:
                print('# 当前网络不稳定，为避免频繁不必要尝试，将自动在5秒后重试')
                await asyncio.sleep(5)
            
            

        
                    
