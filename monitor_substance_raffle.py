import asyncio
import notifier
from tasks.substance_raffle_handler import SubstanceRaffleHandlerTask


class SubstanceRaffleMonitor:
    def __init__(self):
        self.curr_aid = None
        
    async def init_curr_aid(self):
        max_aid = 1000
        min_aid = 50
        while max_aid > min_aid:
            print(min_aid, max_aid)
            mid_aid = int((min_aid + max_aid + 1) / 2)
            code_mid = await notifier.exec_func(-1, SubstanceRaffleHandlerTask.check_code, mid_aid)
            if code_mid:
                code_mid1 = await notifier.exec_func(-1, SubstanceRaffleHandlerTask.check_code, mid_aid+1)
                code_mid2 = await notifier.exec_func(-1, SubstanceRaffleHandlerTask.check_code, mid_aid+2)
                if code_mid1 and code_mid2:
                    max_aid = mid_aid - 1
                else:
                    min_aid = mid_aid + 1
            else:
                min_aid = mid_aid
        print('最新实物抽奖id为', min_aid, max_aid)
        # 经过验证过，还是以防万一，防止翻车
        assert min_aid == max_aid
        self.curr_aid = min_aid
    
    # 已有curr_aid情况下，去自增这个值，目的是防止每次都要跑一次init_curr_aid
    async def is_latest_aid(self):
        old_curr_aid = self.curr_aid
        while True:
            aid = self.curr_aid
            code0 = await notifier.exec_func(-1, SubstanceRaffleHandlerTask.check_code, aid+1)
            if code0:
                code1 = await notifier.exec_func(-1, SubstanceRaffleHandlerTask.check_code, aid+2)
                code2 = await notifier.exec_func(-1, SubstanceRaffleHandlerTask.check_code, aid+3)
                # 最上面没更新，说明目前值最新了
                if code1 and code2:
                    break
                else:
                    if not code2:
                        self.curr_aid += 3
                    elif not code1:
                        self.curr_aid += 2
            else:
                self.curr_aid += 1
        return old_curr_aid == self.curr_aid, old_curr_aid
        
    async def run(self):
        if self.curr_aid is None:
            await self.init_curr_aid()
        aid = self.curr_aid
        for id in range(aid - 15, aid + 1):
            notifier.exec_task(-1, SubstanceRaffleHandlerTask, 0, id, delay_range=(0, 35))
        while True:
            is_latest, old_curr_aid = await self.is_latest_aid()
            if not is_latest:
                for id in range(old_curr_aid+1, self.curr_aid+1):
                    notifier.exec_task(-1, SubstanceRaffleHandlerTask, 0, id, delay_range=(0, 10))
            await asyncio.sleep(60)
            
            

