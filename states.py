from datetime import datetime
import random
from task import Task
import printer
import asyncio


class BaseState():
    black_list = {
        'handle_1_activity_raffle': 2,
        'handle_1_TV_raffle': 2,
        'handle_1_substantial_raffle': 2,
        'handle_1_guard_raffle': 2,
        'open_silver_box': 1,
        'post_watching_history': 2,
        'fetch_heart_gift': 1
        }
    
    def check_status(self, func, value):
        pass

  
# 工作状态类
class DayState(BaseState):
    def check_status(self, func, value):
        # print("工作，精神百倍")
        return 0, None

 
# 睡眠状态
class NightState(BaseState):
    def check_status(self, func, value):
        # print("睡觉了")
        now = datetime.now()
        if func == 'daily_task':
            seconds = (3 - now.hour - 1) * 3600 + (60 - now.minute - 1) * 60 + (60 - now.second)
            sleeptime = seconds + random.uniform(0, 30)
            return 1, sleeptime
        else:
            return self.black_list.get(func, 0), None
            
            
class JailState(BaseState):
    def check_status(self, func, value):
        # print('因为进入了监狱')
        if func == 'daily_task':
            return self.black_list.get(value[0], 0), 1800
        else:
            return self.black_list.get(func, 0), 1800

   
class FreeState(BaseState):
    def check_status(self, func, value):
        # print('因为是个自由人')
        return 0, None
   
                     
class LoginState(BaseState):
    def check_status(self):
        # print('因为已经正常登陆')
        return True

                
class LogoutState(BaseState):
    def check_status(self):
        # print('因为未正常登陆')
        return False
        
                
class UserStates():
    state_night = NightState()
    state_day = DayState()
    state_jail = JailState()
    state_free = FreeState()
    state_login = LoginState()
    state_logout = LogoutState()
    
    def __init__(self, user_id, user_name):
        self.time_state = self.state_day
        self.work_state = self.state_free
        self.log_state = self.state_login
        self.user_id = user_id
        self.user_name = user_name
        self.delay_tasks = []
        self.delay_requests = []
                    
    def clean_delay_tasks(self):
        for func, values in self.delay_tasks:
            time_delay = random.uniform(0, 30)
            Task().call_after(func, time_delay, values, self.user_id)
        del self.delay_tasks[:]
        
    def clean_delay_requests(self):
        for future in self.delay_requests:
            future.set_result(True)
        del self.delay_requests[:]

    def go_to_bed(self):
        # print('{休眠}')
        self.time_state = self.state_night
        
    def wake_up(self):
        # print('{起床}')
        self.time_state = self.state_day
        self.clean_delay_tasks()
              
    def fall_in_jail(self):
        # print('{入狱}')
        self.work_state = self.state_jail
        
    def out_of_jail(self):
        # print('{自由}')
        self.work_state = self.state_free
        self.clean_delay_tasks()
        
    def logout(self):
        print('{未登陆}')
        self.log_state = self.state_logout
        
    def login(self):
        print('{已经登陆}')
        self.log_state = self.state_login
        self.clean_delay_requests()
        
    def printer_with_id(self, list_msg, tag_time=False):
        list_msg[0] += f'(用户id:{self.user_id}  用户名:{self.user_name})'
        printer.info(list_msg, tag_time)
        
    def print_state(self):
        work_state = '恭喜中奖' if self.work_state == self.state_jail else '未进入小黑屋'
        time_state = '白天工作' if self.time_state == self.state_day else '夜晚休眠'
        self.printer_with_id([f'{self.delay_tasks}'], True)
        return work_state, time_state
    
    def check_status(self, func, values):
        code, sleeptime = self.time_state.check_status(func, values)
        if code:
            # print(code, sleeptime)
            pass
        else:
            code, sleeptime = (self.work_state.check_status(func, values))
            # print(code, sleeptime)
          
        # print('+++++++++++++++++++++++')
        if code == 1:
            # self.printer_with_id([f'sleep模式, 推迟执行{func} {values}'], True)
            self.delay_tasks.append((func, values))
            return 1
        elif code == 2:
            # self.printer_with_id([f'drop模式, 不执行{func} {values}'], True)
            return 2
        return 0
        
    async def check_log_state(self, request):
        # print('正在检查', request)
        code = self.log_state.check_status()
        if not code:
            future = asyncio.Future()
            self.delay_requests.append(future)
            await future
        return code
