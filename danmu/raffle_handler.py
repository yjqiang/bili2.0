import asyncio
import notifier


class RaffleHandler:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def run(self):
        while True:
            raffles = {await self.queue.get()}  # 过滤压缩使用 set
            await asyncio.sleep(2.5)
            while not self.queue.empty():
                raffles.add(self.queue.get_nowait())

            for task, *args in raffles:
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
