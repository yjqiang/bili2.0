import copy
import asyncio
import hashlib
import printer
import conf_loader
import exceptions
from web_session import WebSession
import bili_statistics
from user_status import UserStatus
from tasks.login import LoginTask


class User:
    def __init__(self, id, dict_user, task_ctrl, dict_bili, dyn_lottery_friends):
        self.id = id
        self.name = dict_user['username']
        self.password = dict_user['password']
        self.alias = dict_user.get('alias', self.name)
        self.task_ctrl = task_ctrl
        self.status = UserStatus(self)
        self._bililive_session = None
        self._login_session = None
        self._other_session = None
        # 每个user里面都分享了同一个dict，必须要隔离，否则更新cookie这些的时候会互相覆盖
        self.dict_bili = copy.deepcopy(dict_bili)
        self.app_params = f'actionKey={dict_bili["actionKey"]}&appkey={dict_bili["appkey"]}&build={dict_bili["build"]}&device={dict_bili["device"]}&mobi_app={dict_bili["mobi_app"]}&platform={dict_bili["platform"]}'
        self.update_login_data(dict_user)
        self.list_delay = []
        self.repost_del_lock = asyncio.Lock()  # 在follow与unfollow过程中必须保证安全(repost和del整个过程加锁)
        self.dyn_lottery_friends = dyn_lottery_friends  # list (uid, name)
        self.storm_lock = asyncio.Semaphore(1)  # 用于控制同时进行的风暴数目(注意是单个用户的)
        
    def update_login_data(self, login_data):
        for i, value in login_data.items():
            self.dict_bili[i] = value
            if i == 'cookie':
                self.dict_bili['pcheaders']['cookie'] = value
                self.dict_bili['appheaders']['cookie'] = value
        conf_loader.write_user(login_data, self.id)
        
    def is_online(self):
        return self.dict_bili['pcheaders']['cookie'] and self.dict_bili['appheaders']['cookie']
        
    @property
    def bililive_session(self):
        if self._bililive_session is None:
            self._bililive_session = WebSession()
        return self._bililive_session
        
    @property
    def login_session(self):
        if self._login_session is None:
            self._login_session = WebSession()
            # print('测试session')
        return self._login_session
        
    @property
    def other_session(self):
        if self._other_session is None:
            self._other_session = WebSession()
        return self._other_session
        
    def infos(
            self,
            list_objects,
            with_userid=True,
            **kwargs):
        if with_userid:
            printer.infos(
                list_objects,
                **kwargs,
                extra_info=f'用户id:{self.id} 名字:{self.alias}')
        else:
            printer.infos(list_objects, **kwargs)
            
    def info(
            self,
            *objects,
            with_userid=True,
            **kwargs):
        if with_userid:
            printer.info(
                *objects,
                **kwargs,
                extra_info=f'用户id:{self.id} 名字:{self.alias}')
        else:
            printer.info(*objects, **kwargs)
        
    def warn(self, *objects, **kwargs):
        printer.warn(
            *objects,
            **kwargs,
            extra_info=f'用户id:{self.id} 名字:{self.alias}')
        
    def calc_sign(self, str):
        str = f'{str}{self.dict_bili["app_secret"]}'
        hash = hashlib.md5()
        hash.update(str.encode('utf-8'))
        sign = hash.hexdigest()
        return sign
        
    async def get_statistic(self):
        self.status.print_status()
        bili_statistics.print_statistics(self.id)
        
    # 保证在线
    async def req_s(self, func, *args):
        while True:
            try:
                rsp = await func(*args)
                return rsp  # 如果正常，不用管是否登陆了(不少api不需要cookie)，直接return
            except exceptions.LogoutError:
                is_online_status = self.status.check_log_status()
                # 未登陆且未处理
                if is_online_status:
                    self.info([f'判定出现了登陆失败，且未处理'], True)
                    self.status.logout()
                    # login
                    await LoginTask.handle_login_status(self)
                    print(self.list_delay)
                    self.info([f'已经登陆了'], True)
                    self.status.login()
                    for future in self.list_delay:
                        future.set_result(True)
                    del self.list_delay[:]
                # 未登陆，但已处理
                else:
                    future = asyncio.Future()
                    self.list_delay.append(future)
                    await future
                    self.info([f'判定出现了登陆失败，已经处理'], True)

    async def accept(self, func, *args):
        code, sleeptime = self.status.check_status(func)
        if not code:
            return await func(self, *args)
        if code == 2:
            return None
        if code == 1:
            return (-1, (sleeptime, sleeptime+30), self.id, *args),
        
    def sleep(self):
        self.status.sleep()
        
    def wakeup(self):
        self.status.wakeup()
              
    def fall_in_jail(self):
        self.status.go_to_jail()
        self.info([f'抽奖脚本检测{self.id}为小黑屋'], True)
        
    def out_of_jail(self):
        self.status.out_of_jail()
        
    def print_state(self):
        return self.state.print_state()
