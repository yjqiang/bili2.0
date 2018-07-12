import time
import datetime
import asyncio
# from user import User


def CurrentTime():
    currenttime = int(time.mktime(datetime.datetime.now().timetuple()))
    return currenttime


class Messenger():
    instance = None
    
    def __new__(cls, users=[]):
        if not cls.instance:
            cls.instance = super(Messenger, cls).__new__(cls)
            cls.instance.queue = asyncio.PriorityQueue()
            cls.instance._observers = users
            cls.instance.dict_user_status = dict()
            cls.instance.black_list = ['handle_1_room_activity', 'handle_1_room_TV', 'handle_1_activity_raffle', 'handle_1_TV_raffle', 'draw_lottery', 'open_silver_box']
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
        

    async def notify(self, func, value, id=None):
        print('小黑屋状态:', self.dict_user_status)
        if id is None:
            list_tasks = []
            for i, user in enumerate(self._observers):
                if self.check_status(func, i):
                    task = asyncio.ensure_future(user.update(func, value))
                    list_tasks.append(task)
                if not ((i+1) % 30):
                    await asyncio.wait(list_tasks, return_when=asyncio.ALL_COMPLETED)
                    await asyncio.sleep(1)
                    list_tasks = []
            if list_tasks:
                await asyncio.wait(list_tasks, return_when=asyncio.ALL_COMPLETED)
        else:
            user = self._observers[id]
            if self.check_status(func, id):
                await user.update(func, value)
            

# 被观测的
class RaffleHandler(Messenger):

    async def join_raffle(self):
        while True:
            raffle = await self.queue.get()
            await asyncio.sleep(1.5)
            list_raffle0 = [self.queue.get_nowait() for i in range(self.queue.qsize())]
            list_raffle0.append(raffle)
            list_raffle = list(set(list_raffle0))
                
            # print('过滤完毕')
            # if len(list_raffle) != len(list_raffle0):
            print('过滤机制起作用', list_raffle)
            
            for i in list_raffle:
                i = list(i)
                i[0] = list(i[0])
                for j in range(len(i[0])):
                    if isinstance(i[0][j], tuple):
                        print('检测', i)
                        # i[0] = list(i[0])
                        i[0][j] = await i[0][j][1](*(i[0][j][0]))
            
            tasklist = []
            for i in list_raffle:
                task = asyncio.ensure_future(self.notify(i[1], i[0]))
                tasklist.append(task)
            await asyncio.wait(tasklist, return_when=asyncio.ALL_COMPLETED)
            await asyncio.sleep(0.5)
        
    def push2queue(self,  value, func):
        self.queue.put_nowait((value, func))
        return


class DelayRaffleHandler(Messenger):

    async def join_raffle(self):
        while True:
            i = await self.queue.get()
            currenttime = CurrentTime()
            sleeptime = i[0] - currenttime
            print('智能睡眠', sleeptime)
            await asyncio.sleep(max(sleeptime, 0))
            # await i[2](*i[3])
            await self.notify(i[1], i[2], i[3])
            # await asyncio.sleep(1)
        
    def put2queue(self, func, time_expected, value, id=None):
        self.queue.put_nowait((time_expected, func, value, id))
        # print('添加任务', time_expected, func.__name__, func, value)
        return
        
        
class Task(Messenger):
        
    async def init(self):
        await self.put2queue('sliver2coin', 0)
        await self.put2queue('doublegain_coin2silver', 0)
        await self.put2queue('DoSign', 0)
        await self.put2queue('Daily_bag', 0)
        await self.put2queue('Daily_Task', 0)
        await self.put2queue('link_sign', 0)
        await self.put2queue('send_gift', 0)
        await self.put2queue('auto_send_gift', 0)
        await self.put2queue('BiliMainTask', 0)
        await self.put2queue('judge', 0)
        await self.put2queue('open_silver_box', 0)
        
    async def run(self):
        await self.init()
        while True:
            raffle = await self.queue.get()
            wanted_time = raffle[0]
            sleeptime = max(wanted_time - CurrentTime(), 0)
            print('智能睡眠', sleeptime)
            await asyncio.sleep(sleeptime)
            
            await self.notify(raffle[1], (), raffle[2])
            
            print('---------------------------------------')
            await asyncio.sleep(1)
                
    async def put2queue(self, func, delay, id=None):
        await self.queue.put((CurrentTime() + delay, func, id))
        # print('添加任务')
        return
        
    async def heartbeat(self):
        while True:
            await self.notify('heartbeat', ())
            await self.notify('draw_lottery', ())
            await asyncio.sleep(300)



