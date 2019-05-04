from tasks.tv_raffle_handler import TvRaffleJoinTask
from tasks.guard_raffle_handler import GuardRafflJoinTask
from tasks.storm_raffle_handler import StormRaffleJoinTask
from tasks.live_daily_job import (
    RecvHeartGiftTask,
    OpenSilverBoxTask,
)


# 时间状态
class FreeStatus:
    @staticmethod
    def is_ok(_):
        return True


class JailStatus:
    LIMITED = [
        RecvHeartGiftTask.work,
        OpenSilverBoxTask.work,
        StormRaffleJoinTask.work,
        GuardRafflJoinTask.work,
        TvRaffleJoinTask.work
    ]
    
    @staticmethod
    def is_ok(func):
        return func not in JailStatus.LIMITED
        

class LoginStatus:
    @staticmethod
    def is_ok():
        # print('因为已经正常登陆')
        return True

                
class LogoutStatus:
    @staticmethod
    def is_ok():
        # print('因为未正常登陆')
        return False
        
        
class UserStatus:
    def __init__(self):
        self.work_status = FreeStatus
        self.log_status = LoginStatus
              
    def go_to_jail(self):
        # print('{入狱}')
        self.work_status = JailStatus
        
    def out_of_jail(self):
        # print('{自由}')
        self.work_status = FreeStatus
        
    def logout(self):
        # print('{未登陆}')
        self.log_status = LogoutStatus
        
    def login(self):
        # print('{已经登陆}')
        self.log_status = LoginStatus
        
    def get_status(self):
        work_status = '恭喜中奖' if self.work_status == JailStatus else '自由之身'
        yield work_status
    
    def check_status(self, func):
        return self.work_status.is_ok(func)
        
    def check_log_status(self):
        # print('正在检查', request)
        return self.log_status.is_ok()
