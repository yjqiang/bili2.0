from datetime import datetime
from tasks.tv_raffle_handler import TvRaffleHandlerTask
from tasks.guard_raffle_handler import GuardRaffleHandlerTask
from tasks.live_daily_job import (
    HeartBeatTask,
    RecvHeartGiftTask,
    OpenSilverBoxTask,
    RecvDailyBagTask,
    SignTask,
    WatchTvTask,
    SignFansGroupsTask,
    SendGiftTask,
    ExchangeSilverCoinTask,
)
from tasks.main_daily_job import (
    JudgeCaseTask,
    BiliMainTask
)

# 1 延迟操作，返回一个参考延迟范围
# 2 放弃操作


# 时间状态
class FreeStatus:
    @staticmethod
    def check_status(func):
        # print('是个自由人')
        return 0, None


class JailStatus:
    dict_jail_status = {
        RecvHeartGiftTask.recv_heartgift: 1,
        OpenSilverBoxTask.open_silver_box: 1,
        
        TvRaffleHandlerTask.join: 2,
        GuardRaffleHandlerTask.join: 2,
    }
    
    @staticmethod
    def check_status(func):
        # print('进了监狱')
        strategy = JailStatus.dict_jail_status.get(func, 0)
        if strategy == 1:
            return strategy, 1800
        return strategy, None
                        

# 工作状态类
class DayStatus:
    @staticmethod
    def check_status(func):
        # print("工作，精神百倍")
        return 0, None

 
class NightStatus:
    dict_night_status = {
        HeartBeatTask.heart_beat: 1,
        RecvHeartGiftTask.recv_heartgift: 1,
        OpenSilverBoxTask.open_silver_box: 1,
        RecvDailyBagTask.recv_dailybag: 1,
        SignTask.sign: 1,
        WatchTvTask.watch_tv: 1,
        SignFansGroupsTask.sign_groups: 1,
        SendGiftTask.send_gift: 1,
        ExchangeSilverCoinTask.silver2coin: 1,
        JudgeCaseTask.judge: 1,
        BiliMainTask.finish_bilimain_tasks: 1,
        
        TvRaffleHandlerTask.check: 2,
        GuardRaffleHandlerTask.check: 2,
    }
    
    @staticmethod
    def check_status(func):
        # print("睡觉了")
        strategy = NightStatus.dict_night_status.get(func, 0)
        if strategy == 1:
            now = datetime.now()
            # 7点时候
            sleeptime = (7 - now.hour - 1) * 3600 + (59 - now.minute) * 60 + 60 - now.second
            return 1, sleeptime
        return strategy, None
        

class LoginStatus:
    @staticmethod
    def check_status():
        # print('因为已经正常登陆')
        return True

                
class LogoutStatus:
    @staticmethod
    def check_status():
        # print('因为未正常登陆')
        return False
        
        
class UserStatus:
    def __init__(self, user):
        self.time_status = DayStatus
        self.work_status = FreeStatus
        self.log_status = LoginStatus
        self.user = user

    def sleep(self):
        # print('{休眠}')
        self.time_status = NightStatus
        
    def wakeup(self):
        # print('{起床}')
        self.time_status = DayStatus
              
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
        
    def print_status(self):
        work_status = '恭喜中奖' if self.work_status == JailStatus else '自由之身'
        time_status = '白天工作' if self.time_status == DayStatus else '夜晚休眠'
        self.user.infos([f'小黑屋状态: {work_status}'])
        self.user.infos([f'工作状态: {time_status}'])
    
    def check_status(self, func):
        code, sleeptime = self.time_status.check_status(func)
        # print('初次code', code)
        if not code:
            code, sleeptime = self.work_status.check_status(func)
            # print(code, sleeptime)
        return code, sleeptime
        
    def check_log_status(self):
        # print('正在检查', request)
        code = self.log_status.check_status()
        return code
