import time
import datetime
import asyncio
import random


def CurrentTime():
    currenttime = int(time.mktime(datetime.datetime.now().timetuple()))
    return currenttime


class Messenger():
    instance = None
    
    def __new__(cls, users=[], var_super_user=None, loop=None, is_need_queue=False):
        if not cls.instance:
            cls.instance = super(Messenger, cls).__new__(cls)            
            if is_need_queue:
                cls.instance.queue = asyncio.Queue()
            cls.instance.loop = loop
            cls.instance._observers = users
            cls.instance._var_super_user = var_super_user
            cls.instance.dict_user_status = dict()
            cls.instance.black_list = ['handle_1_room_activity', 'handle_1_room_TV', 'handle_1_activity_raffle', 'handle_1_TV_raffle', 'draw_lottery', 'open_silver_box', 'post_watching_history']
        return cls.instance

    def register(self, ob):
        print('register', ob)
        self._observers.append(ob)

    def remove(self, user_id):
        self.dict_user_status[user_id] = False
        
    def check_status(self, func, user_id):
        if func not in self.black_list:
            return True
        else:
            return self.dict_user_status.get(user_id, True)
            
    def print_blacklist(self):
        print('小黑屋状态:', self.dict_user_status)

    async def notify(self, func, value, id=None):
        # print('小黑屋状态:', self.dict_user_status)
        if id is None:
            list_tasks = []
            for i, user in enumerate(self._observers):
                if self.check_status(func, i):
                    task = asyncio.ensure_future(user.update(func, value))
                    list_tasks.append(task)
            if list_tasks:
                await asyncio.wait(list_tasks)
        elif id >= 0:
            user = self._observers[id]
            if self.check_status(func, id):
                return await user.update(func, value)
        else:
            user = self._var_super_user
            answer = await user.update(func, value)
            return answer
            
    def set_delay_times(self, time_range):
        return ((i, random.uniform(0, time_range)) for i in range(len(self._observers)))
            

# 被观测的
class RaffleHandler(Messenger):

    async def join_raffle(self):
        while True:
            raffle = await self.queue.get()
            await asyncio.sleep(4)
            list_raffle0 = [self.queue.get_nowait() for i in range(self.queue.qsize())]
            list_raffle0.append(raffle)
            list_raffle = list(set(list_raffle0))
            
            tasklist = []
            for i in list_raffle:
                task = asyncio.ensure_future(self.handle_1_roomid_raffle(i))
                tasklist.append(task)
            await asyncio.wait(tasklist)
        
    def push2queue(self,  value, func, id=None):
        self.queue.put_nowait((value, func, id))
        
    async def handle_TV_raffle(self, room_id):
        if (await self.notify('check_if_normal_room', (room_id,), -1)):
            Task().call_after('post_watching_history', 0, (room_id,), time_range=60)
            await self.notify('handle_1_room_TV', (room_id,), -1)
        
    async def handle_captain_raffle(self, user_name):
        room_id = await self.notify('find_live_user_roomid', (user_name,), -1)
        if (await self.notify('check_if_normal_room', (room_id,), -1)):
            Task().call_after('post_watching_history', 0, (room_id,), time_range=60)
            await self.notify('handle_1_room_captain', (room_id,), -1)
    
    async def handle_1_roomid_raffle(self, i):
        if i[1] in ['handle_TV_raffle', 'handle_captain_raffle']:
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
        # self.call_after('daily_task', 0, ('send_gift',), time_range=25)
        # self.call_after('daily_task', 0, ('auto_send_gift',), time_range=25)
        self.call_after('daily_task', 0, ('BiliMainTask',), time_range=25)
        self.call_after('daily_task', 0, ('judge',), time_range=25)
        self.call_after('daily_task', 0, ('open_silver_box',), time_range=25)
        self.call_after('daily_task', 0, ('heartbeat',), time_range=25)
                
    def excute_async(self, i):
        print('执行', i)
        asyncio.ensure_future(self.notify(*i))
                
    def call_after(self, func, delay, tuple_values, id=None, time_range=None):
        if time_range is None:
            value = (func, tuple_values, id)
            self.loop.call_later(delay, self.excute_async, value)
        else:
            for id, add_time in self.set_delay_times(time_range):
                value = (func, tuple_values, id)
                self.loop.call_later(delay + add_time, self.excute_async, value)
        
    def call_at(self, func, time_expected, tuple_values, id=None, time_range=None):
        current_time = CurrentTime()
        delay = time_expected - current_time
        self.call_after(func, delay, tuple_values, id=id, time_range=time_range)
        
    async def call_right_now(self, func, value, id=-1):
        # print(func, value)
        return (await self.notify(func, (value,), id))


