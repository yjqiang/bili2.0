import time
import asyncio
import random
from datetime import datetime


def CurrentTime():
    currenttime = int(time.time())
    return currenttime


class Singleton(type):
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Messenger(metaclass=Singleton):
    def __init__(self, users=None, var_super_user=None, loop=None, is_need_queue=False):
        if is_need_queue:
            self.queue = asyncio.Queue()
        self.loop = loop
        self._observers = users
        self._var_super_user = var_super_user

    async def call(self, func, value, id=None):
        # print('小黑屋状态:', self.dict_user_status)
        if id is None:
            list_tasks = []
            for i, user in enumerate(self._observers):
                task = asyncio.ensure_future(user.update(func, value))
                list_tasks.append(task)
            if list_tasks:
                await asyncio.wait(list_tasks)
        elif id >= 0:
            if id >= len(self._observers):
                return 0
            user = self._observers[id]
            return await user.update(func, value)
        else:
            user = self._var_super_user
            answer = await user.update(func, value)
            return answer
            
    def call_backgroud(self, i):
        print('执行', i)
        asyncio.ensure_future(self.call(*i))
                
    def call_after(self, func, delay, tuple_values, id=None, time_range=None):
        if time_range is None:
            value = (func, tuple_values, id)
            self.loop.call_later(delay, self.call_backgroud, value)
        else:
            for id, add_time in self.set_delay_times(time_range):
                value = (func, tuple_values, id)
                self.loop.call_later(delay + add_time, self.call_backgroud, value)
        
    def call_at(self, func, time_expected, tuple_values, id=None, time_range=None):
        current_time = CurrentTime()
        delay = time_expected - current_time
        self.call_after(func, delay, tuple_values, id=id, time_range=time_range)
            
    def set_delay_times(self, time_range):
        return ((i, random.uniform(0, time_range)) for i in range(len(self._observers)))
            

# 被观测的
class RaffleHandler(Messenger):

    async def join_raffle(self):
        while True:
            raffle = await self.queue.get()
            await asyncio.sleep(3)
            list_raffle0 = [self.queue.get_nowait() for i in range(self.queue.qsize())]
            list_raffle0.append(raffle)
            list_raffle = list(set(list_raffle0))
            
            tasklist = []
            for i in list_raffle:
                task = asyncio.ensure_future(self.handle_1_roomid_raffle(i))
                tasklist.append(task)
            await asyncio.wait(tasklist)
        
    def push2queue(self, value, func, id=None):
        self.queue.put_nowait((value, func, id))
        
    async def handle_TV_raffle(self, room_id):
        if (await self.call('check_if_normal_room', (room_id,), -1)):
            self.call_after('post_watching_history', 0, (room_id,), time_range=60)
            await self.call('handle_1_room_TV', (room_id,), -1)
        
    async def handle_guard_raffle(self, room_id):
        if (await self.call('check_if_normal_room', (room_id,), -1)):
            self.call_after('post_watching_history', 0, (room_id,), time_range=60)
            await self.call('handle_1_room_guard', (room_id,), -1)
    
    async def handle_1_roomid_raffle(self, i):
        if i[1] in ['handle_TV_raffle', 'handle_guard_raffle']:
            await getattr(self, i[1])(*i[0])
        else:
            print('hhjjkskddrsfvsfdfvdfvvfdvdvdfdfffdfsvh', i)
        
        
class Task(Messenger):
        
    def init(self):
        self.call_after('daily_task', 0, ('sliver2coin',), time_range=25)
        self.call_after('daily_task', 0, ('doublegain_coin2silver',), time_range=25)
        self.call_after('daily_task', 0, ('DoSign',), time_range=25)
        self.call_after('daily_task', 0, ('Daily_bag',), time_range=25)
        self.call_after('daily_task', 0, ('Daily_Task',), time_range=25)
        self.call_after('daily_task', 0, ('link_sign',), time_range=25)
        # self.call_after('daily_task', 0, ('auto_send_gift',), time_range=25)
        self.call_after('daily_task', 0, ('BiliMainTask',), time_range=25)
        self.call_after('daily_task', 0, ('judge',), time_range=25)
        self.call_after('daily_task', 0, ('open_silver_box',), time_range=25)
        self.call_after('daily_task', 0, ('heartbeat',), time_range=25)
        self.call_after('daily_task', 0, ('fetch_heart_gift',), time_range=25)
        
    async def call_right_now(self, func, value, id=-1):
        # print(func, value)
        return (await self.call(func, (value,), id))
        
        
class StateTask(Messenger):
    def wake_up_all(self):
        for user in (self._observers):
            user.wake_up()
            
    def release_all(self):
        for user in (self._observers):
            user.out_of_jail()
            
    def sleep_all(self):
        for user in (self._observers):
            user.go_to_bed()
            
    async def run_workstate(self):
        while True:
            await asyncio.sleep(4 * 3600)
            # await asyncio.sleep(120)
            self.release_all()
            
    async def run_timestate(self):
        while True:
            sleeptime = 0
            now = datetime.now()
            if now.hour * 60 + now.minute < 180:
                self.sleep_all()
                seconds = (3 - now.hour - 1) * 3600 + (60 - now.minute - 1) * 60 + (60 - now.second)
                # 防止时间卡得过死
                sleeptime = seconds + random.uniform(60, 90)
                sleeptime = max(0, seconds)
            else:
                self.wake_up_all()
                seconds = (24 - now.hour - 1) * 3600 + (60 - now.minute - 1) * 60 + (60 - now.second)
                sleeptime = seconds + random.uniform(60, 90)
            await asyncio.sleep(sleeptime)
            


