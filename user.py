import copy
import asyncio
import hashlib
from itertools import count
from typing import Callable

import printer
import conf_loader
import exceptions
from web_session import WebSession
from tasks.login import LoginTask


class User:
    _ids = count(0)
    __slots__ = (
        'id', 'force_sleep', 'name', 'password', 'alias', 'task_ctrl',
        'task_arrangement', 'is_log_in', 'is_in_jail',

        'bililive_session', 'login_session', 'other_session',

        'dict_bili', 'app_params', 'list_delay', 'repost_del_lock',
        'dyn_lottery_friends', 'storm_lock', 'recording_tasks',
    )

    def __init__(
            self, dict_user: dict, task_ctrl: dict, task_arrangement: dict, dict_bili: dict, force_sleep: Callable):
        self.id = next(self._ids)
        self.force_sleep = force_sleep
        self.name = dict_user['username']
        self.password = dict_user['password']
        self.alias = dict_user.get('alias', self.name)
        self.task_ctrl = task_ctrl
        self.task_arrangement = task_arrangement
        self.is_log_in = True  # 登陆状态，cookie、token有效性
        self.is_in_jail = False  # 是否小黑屋

        self.bililive_session = WebSession()
        self.login_session = WebSession()
        self.other_session = WebSession()

        # 每个user里面都分享了同一个dict，必须要隔离，否则更新cookie这些的时候会互相覆盖
        self.dict_bili = copy.deepcopy(dict_bili)
        self.app_params = f'actionKey={dict_bili["actionKey"]}&' \
            f'appkey={dict_bili["appkey"]}&build={dict_bili["build"]}&' \
            f'device={dict_bili["device"]}&mobi_app={dict_bili["mobi_app"]}&' \
            f'platform={dict_bili["platform"]}'
        self.update_login_data(dict_user)
        self.list_delay = []
        self.repost_del_lock = asyncio.Lock()  # 在follow与unfollow过程中必须保证安全(repost和del整个过程加锁)
        dyn_lottery_friends = [(str(uid), name) for uid, name in task_ctrl['dyn_lottery_friends'].items()]
        self.dyn_lottery_friends = dyn_lottery_friends  # list (uid, name)
        self.storm_lock = asyncio.Semaphore(1)  # 用于控制同时进行的风暴数目(注意是单个用户的)
        self.recording_tasks = {}

    def update_login_data(self, login_data):
        for i, value in login_data.items():
            self.dict_bili[i] = value
            if i == 'cookie':
                self.dict_bili['pcheaders']['cookie'] = value
                self.dict_bili['appheaders']['cookie'] = value
        conf_loader.write_user(login_data, self.id)

    def is_online(self):
        return self.dict_bili['pcheaders']['cookie'] and self.dict_bili['appheaders']['cookie']

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

    def calc_sign(self, text):
        text = f'{text}{self.dict_bili["app_secret"]}'
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    # 保证在线
    async def req_s(self, func, *args):
        while True:
            try:
                rsp = await func(*args)
                return rsp  # 如果正常，不用管是否登陆了(不少api不需要cookie)，直接return
            except exceptions.LogoutError:
                # 未登陆且未处理
                if self.is_log_in:
                    self.info(f'判定出现了登陆失败，且未处理')
                    self.is_log_in = False
                    # login
                    await LoginTask.handle_login_status(self)
                    print(self.list_delay)
                    self.info(f'已经登陆了')
                    self.is_log_in = True
                    for future in self.list_delay:
                        future.set_result(True)
                    del self.list_delay[:]
                # 未登陆，但已处理
                else:
                    future = asyncio.Future()
                    self.list_delay.append(future)
                    await future
                    self.info(f'判定出现了登陆失败，已经处理')
            except exceptions.ForbiddenError:
                await asyncio.shield(self.force_sleep(3600))  # bili_sched.force_sleep
                await asyncio.sleep(3600)  # 有的function不受sched控制，主动sleep即可，不cancel原因是怕堵死一些协程

    def fall_in_jail(self):
        self.is_in_jail = True
        self.info(f'用户进入小黑屋')

    def out_of_jail(self):
        self.is_in_jail = False
        self.info(f'抽奖脚本尝试性设置用户已出小黑屋（如果实际没出还会再判定进去）')

    def print_status(self):
        self.info('当前用户的RECORDING_TAKS：', self.recording_tasks)
        jail_status = '恭喜中奖' if self.is_in_jail else '自由之身'
        self.info('当前用户的状态：', jail_status)
