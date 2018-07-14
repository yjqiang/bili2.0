import time
import datetime
import asyncio
import printer
# from super_user import SuperUser


def CurrentTime():
    currenttime = int(time.mktime(datetime.datetime.now().timetuple()))
    return currenttime


class Messenger():
    instance = None
    
    def __new__(cls, users=[], var_super_user=None):
        if not cls.instance:
            cls.instance = super(Messenger, cls).__new__(cls)
            cls.instance.queue = asyncio.PriorityQueue()
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
                if not ((i+1) % 100):
                    await asyncio.wait(list_tasks, return_when=asyncio.ALL_COMPLETED)
                    # await asyncio.sleep(1)
                    list_tasks = []
            if list_tasks:
                await asyncio.wait(list_tasks, return_when=asyncio.ALL_COMPLETED)
        elif id >= 0:
            user = self._observers[id]
            if self.check_status(func, id):
                return await user.update(func, value)
        else:
            user = self._var_super_user
            answer = await user.update(func, value)
            return answer
            

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
            
            for i, value in enumerate(list_raffle):
                # 总督预处理
                if isinstance(value[0][0], str):
                    value = list(value)
                    value[0] = [await self.notify('find_live_user_roomid', value[0], -1)]
                    list_raffle[i] = value
            tasklist = []
            for i in list_raffle:
                task = asyncio.ensure_future(self.handle_1_roomid_raffle(i))
                tasklist.append(task)
            await asyncio.wait(tasklist, return_when=asyncio.ALL_COMPLETED)
            await asyncio.sleep(0.5)
        
    def push2queue(self,  value, func, id=None):
        self.queue.put_nowait((value, func, id))
        return
    
    async def handle_1_roomid_raffle(self, i):
        if i[1] in ['handle_1_room_TV', 'handle_1_room_captain']:
            if (await self.notify('check_if_normal_room', i[0], -1)):
                await self.notify('post_watching_history', i[0])
                await self.notify(i[1], i[0], i[2])
        else:
            print('hhjjkskddrsfvsfdfvdfvvfdvdvdfdfffdfsvh', i)


class DelayRaffleHandler(Messenger):

    async def join_raffle(self):
        while True:
            i = await self.queue.get()
            currenttime = CurrentTime()
            sleeptime = i[0] - currenttime
            print('延迟抽奖智能睡眠', sleeptime)
            await asyncio.sleep(max(sleeptime, 0))
            # await i[2](*i[3])
            await self.notify(i[1], i[2], i[3])
            # await asyncio.sleep(1)
        
    def put2queue(self, func, time_expected, value, id=None):
        self.queue.put_nowait((time_expected, func, value, id))
        print('添加任务', time_expected, func, value)
        return
        
        
class Task(Messenger):
        
    async def init(self):
        await self.put2queue('sliver2coin', 0)
        await self.put2queue('doublegain_coin2silver', 0)
        await self.put2queue('DoSign', 0)
        await self.put2queue('Daily_bag', 0)
        await self.put2queue('Daily_Task', 0)
        await self.put2queue('link_sign', 0)
        # await self.put2queue('send_gift', 0)
        #await self.put2queue('auto_send_gift', 0)
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
            await asyncio.sleep(10)
                
    async def put2queue(self, func, delay, id=None):
        await self.queue.put((CurrentTime() + delay, func, id))
        # print('添加任务')
        return
        
    async def heartbeat(self):
        while True:
            printer.info([f'用户普通心跳以及实物抽奖检测开始'], True)
            await self.notify('heartbeat', ())
            # await self.notify('draw_lottery', ())
            for i in range(87, 95):
                answer = await self.notify('handle_1_room_substant', (i,), 0)
                if answer is None:
                    # print('结束')
                    break
            printer.info([f'用户普通心跳以及实物抽奖检测完成'], True)
            await asyncio.sleep(300)



