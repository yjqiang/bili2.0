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
        return cls.instance

    def register(self, ob):
        print('register', ob)
        self._observers.append(ob)

    def remove(self, ob):
        self._observers.remove(ob)

    async def notify(self, func, value, id=None):
        if id is None:
            tasks = [asyncio.ensure_future(ob.update(func, value)) for ob in self._observers]
            await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
        else:
            await self._observers[id].update(func, value)
            

# 被观测的
class RaffleHandler(Messenger):

    async def join_raffle(self):
        while True:
            raffle = await self.queue.get()
            await asyncio.sleep(5)
            list_raffle0 = [self.queue.get_nowait() for i in range(self.queue.qsize())]
            list_raffle0.append(raffle)
            list_raffle = list(set(list_raffle0))
                
            # print('过滤完毕')
            # if len(list_raffle) != len(list_raffle0):
            print('过滤机制起作用', list_raffle)
            
            tasklist = []
            for i in list_raffle:
                task = asyncio.ensure_future(self.notify(i[1], i[0]))
                tasklist.append(task)
            await asyncio.wait(tasklist, return_when=asyncio.ALL_COMPLETED)
        
    def push2queue(self,  value, func):
        self.queue.put_nowait((value, func))
        # print('appended')
        return


class DelayRaffleHandler(Messenger):

    async def join_raffle(self):
        while True:
            i = await self.queue.get()
            print(i)
            currenttime = CurrentTime()
            sleeptime = i[0] - currenttime
            print('智能睡眠', sleeptime)
            await asyncio.sleep(max(sleeptime, 0))
            # await i[2](*i[3])
            await self.notify(i[1], i[2], i[3])
        
    def put2queue(self, func, time_expected, value, id=None):
        self.queue.put_nowait((time_expected, func, value, id))
        # print('添加任务', time_expected, func.__name__, func, value)
        return
        
        
class Task(Messenger):
    instance = None
    
    def __new__(cls, user=[]):
        if not cls.instance:
            cls.instance = super(Task, cls).__new__(cls)
            cls.instance._observers = user
            cls.instance.queue = asyncio.PriorityQueue()
        return cls.instance
        
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
        
    async def run(self):
        await self.init()
        while True:
            raffle = await self.queue.get()
            wanted_time = raffle[0]
            sleeptime = max(wanted_time - CurrentTime(), 0)
            print('智能睡眠', sleeptime)
            await asyncio.sleep(sleeptime)
            list_raffle0 = []
            for i in range(self.queue.qsize()):
                job = self.queue.get_nowait()
                if job[0] > CurrentTime() + 2:
                    await self.put2queue(job[1], job[0]-CurrentTime(), job[2])
                    break
                else:
                    list_raffle0.append(job)
            list_raffle0.append(raffle)
            list_raffle = list(set(list_raffle0))
                
            # print('过滤完毕')
            # if len(list_raffle) != len(list_raffle0):
            print(list_raffle)
            
            
            
            
            tasklist = []
            for i in list_raffle:
                task = asyncio.ensure_future(self.notify(i[1], (), i[2]))
                tasklist.append(task)
            await asyncio.wait(tasklist, return_when=asyncio.ALL_COMPLETED)
            print('ffffdjjjdcgcdhtdtdchtrhtcrcrthctrhhctrctrhctrhcrhtctrhcrthchtrhct')
                
    async def put2queue(self, func, delay, id=None):
        await self.queue.put((CurrentTime() + delay, func, id))
        # print('添加任务')
        return
        
    async def heartbeat(self):
        while True:
            await asyncio.sleep(300)
            await self.notify('heartbeat', ())
            await self.notify('draw_lottery', ())



