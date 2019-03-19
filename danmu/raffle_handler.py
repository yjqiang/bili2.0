import asyncio
import notifier


class RaffleHandler:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def run(self):
        while True:
            raffle0 = await self.queue.get()
            await asyncio.sleep(2)
            list_raffle = [self.queue.get_nowait() for i in range(self.queue.qsize())]
            list_raffle.append(raffle0)
            # 后期考虑如何更好的压缩
            list_raffle = list(set(list_raffle))
            # print('raffle_handler', list_raffle)
            for task, *args in list_raffle:
                notifier.exec_task(-1, task, 0, *args, delay_range=(0, 2))
        
    def push2queue(self, *args):
        self.queue.put_nowait(args)
        
    def exec_at_once(self, task, *args):
        notifier.exec_task(-1, task, 0, *args, delay_range=(0, 0))

                
var = RaffleHandler()
    
async def run():
    await var.run()
        

def push2queue(*args):
    var.push2queue(*args)

        
def exec_at_once(task, *args):
    var.exec_at_once(task, *args)
    
    
