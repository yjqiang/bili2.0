import asyncio
import notifier


class RaffleHandler:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def run(self):
        while True:
            list_raffle = [await self.queue.get()]
            await asyncio.sleep(2)
            while not self.queue.empty():
                list_raffle.append(self.queue.get_nowait())

            # 压缩与过滤
            list_raffle = list(set(list_raffle))
            # print('raffle_handler', list_raffle)
            for task, *args in list_raffle:
                notifier.exec_task_no_wait(task, *args)
        
    def push2queue(self, *args):
        self.queue.put_nowait(args)
        
    @staticmethod
    def exec_at_once(task, *args):
        notifier.exec_task_no_wait(task, *args)

                
var = RaffleHandler()


async def run():
    await var.run()
        

def push2queue(*args):
    var.push2queue(*args)

        
def exec_at_once(task, *args):
    var.exec_at_once(task, *args)
