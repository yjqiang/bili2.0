import asyncio
from states import UserStates
from statistic import Statistics
import printer
from config_loader import ConfigLoader


class BaseUser:
    def __init__(self, user_id, dict_user, web_hub, task_control):
        self.webhub = web_hub
        self.statistics = Statistics()
        self.user_id = user_id
        self.user_name = dict_user['username']
        self.user_password = dict_user['password']
        self.task_control = task_control
        self.state = UserStates(user_id, self.user_name)
        
    def printer_with_id(self, list_msg, tag_time=False):
        list_msg[0] += f'(用户id:{self.user_id}  用户名:{self.user_name})'
        printer.info(list_msg, tag_time)
        
    def write_user(self, dict_new):
        self.webhub.set_status(dict_new)
        ConfigLoader().write_user(dict_new, self.user_id)
        
    async def get_statistic(self):
        await asyncio.sleep(0)
        work_state, time_state = self.print_state()
        self.printer_with_id([f'小黑屋状态: {work_state}'], True)
        self.printer_with_id([f'工作状态: {time_state}'], True)
        self.statistics.getlist()
        self.statistics.getresult()
        
    async def online_request(self, func, *args):
        rsp = await func(*args)
        code = await self.state.check_log_state(func)
        # print(rsp)
        # 未登陆且未处理
        if rsp == 3 and code:
            self.printer_with_id([f'判定出现了登陆失败，且未处理'], True)
            self.state.logout()
            # login
            await self.handle_login_status()
            # await asyncio.sleep(10)
            print(self.state.delay_requests)
            self.printer_with_id([f'已经登陆了'], True)
            self.state.login()
            rsp = await func(*args)
        # 未登陆，但已处理
        elif not code:
            self.printer_with_id([f'判定出现了登陆失败，已经处理'], True)
            rsp = await func(*args)
        return rsp
        
    async def update(self, func, values):
        status = self.check_status(func, values)
        if not status:
            return await getattr(self, func)(*values)
        
    def go_to_bed(self):
        self.state.go_to_bed()
        
    def wake_up(self):
        self.state.wake_up()
              
    def fall_in_jail(self):
        self.state.fall_in_jail()
        self.printer_with_id([f'抽奖脚本检测{self.user_id}为小黑屋'], True)
        
    def out_of_jail(self):
        self.state.out_of_jail()
        
    def print_state(self):
        return self.state.print_state()
        
    def check_status(self, func, values):
        return self.state.check_status(func, values)
