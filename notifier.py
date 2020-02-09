import asyncio
import random
from typing import Optional, Callable

import aiojobs

import bili_statistics
from user import User
from tasks.base_class import TaskType, UniqueType, How2Call
from printer import info as print


class Users:
    __slots__ = ('_users', '_global_task_control', '_global_task_arrangement', '_dict_bili', '_force_sleep')

    def __init__(self,
                 global_task_control: dict, global_task_arrangement: dict,
                 dict_bili: dict, force_sleep: Callable):
        self._users = []
        self._global_task_control = global_task_control
        self._global_task_arrangement = global_task_arrangement
        self._dict_bili = dict_bili
        self._force_sleep = force_sleep

    @property
    def superuser(self) -> User:
        return self._users[0]

    def gets_with_restrict(self, index: int, task):
        task_name = task.TASK_NAME
        for user in self.gets(index):
            if user.is_in_jail and task_name in (
                    'recv_heart_gift',
                    'open_silver_box',
                    'join_storm_raffle',
                    'join_guard_raffle',
                    'join_tv_raffle',
                    'join_pk_raffle'
            ):
                continue
            if task_name != 'null':  # null 就忽略过滤，直接参与
                if f'probability_{task_name}' in user.task_arrangement:  # 平均概率筛选
                    if not random.random() < user.task_arrangement[f'probability_{task_name}']:
                        continue
                if not bili_statistics.add2max_time_task_checkers(  # 每日次数筛选
                        user_id=user.id,
                        task=task,
                        max_time=user.task_arrangement.get(task_name, -1)):
                    continue
            yield user

    # async 只是为了 User 里面的 aiohttp 的 session;即使切了也没啥吧，append 的时候不切换协程，对 notifier 运行中不会造成什么影响
    async def add_user(self, user_info: dict, custom_task_control: dict, custom_task_arrangement: dict):
        task_control = {**self._global_task_control, **custom_task_control}
        task_arrangement = {**self._global_task_arrangement, **custom_task_arrangement}

        user = User(
            dict_user=user_info,
            task_ctrl=task_control,
            task_arrangement=task_arrangement,
            dict_bili=self._dict_bili,
            force_sleep=self._force_sleep)
        self._users.append(user)

    def gets(self, index: int):
        if index == -2:
            for user in self._users:
                yield user
            return
        user = self._users[index]
        yield user


class Notifier:
    __slots__ = ('_loop', '_users', '_scheduler',)

    def __init__(self, loop=None):
        if loop is None:
            self._loop = asyncio.get_event_loop()
        else:
            self._loop = loop
        self._users: Optional[Users] = None
        self._scheduler: Optional[aiojobs.Scheduler] = None

    def init(self, users: Users):
        self._users = users

    async def add_user(self, **kwargs):
        await self._users.add_user(**kwargs)

    # pause 和 resume 必须在同一个循环里面用，否则可能发生类似线程不安全的东西
    async def resume(self):
        if self._scheduler is None:
            self._scheduler = await aiojobs.create_scheduler()

    async def pause(self):
        if self._scheduler is not None and not self._scheduler.closed:
            scheduler = self._scheduler
            self._scheduler = None
            await scheduler.close()

    @staticmethod
    async def _unique_work(user: User, task, func: Callable, *args, **kwargs):
        if bili_statistics.start_unique_task(user.id, task):
            try:
                result = await func(user, *args, **kwargs)
                bili_statistics.done_unique_task(user.id, task)
                return result
            except asyncio.CancelledError:
                print(f'CONFIRMED CANCEL {user} {func}')
                bili_statistics.cancel_unique_task(user.id, task)
        else:
            print(f'重复推送{func} {user.id}（此为debug信息忽略即可）')
        return None

    @staticmethod
    async def _multi_work(user: User, _, func: Callable, *args, **kwargs):
        try:
            return await func(user, *args, **kwargs)
        except asyncio.CancelledError:
            print(f'CONFIRMED CANCEL {user} {func}')
            return None

    async def run_sched_func(self, func: Callable, *args, **kwargs):
        scheduler = self._scheduler
        if scheduler is not None and not scheduler.closed:
            await scheduler.spawn(func(*args, **kwargs))

    # 这里是为了日常任务的check问题
    async def run_sched_func_with_return(self, func: Callable, *args, **kwargs):
        scheduler = self._scheduler
        if scheduler is not None and not scheduler.closed:
            return await func(*args, **kwargs)

    def run_sched_func_bg(self, *args, **kwargs):
        self._loop.create_task(self.run_sched_func(*args, **kwargs))

    @staticmethod
    async def run_forced_func(func: Callable, *args, **kwargs):
        return await func(*args, **kwargs)

    def run_forced_func_bg(self, *args, **kwargs):
        self._loop.create_task(self.run_forced_func(*args, **kwargs))

    async def _dont_wait(self, task,
                         handle_work: Callable,
                         handle_unique: Callable,
                         func_work: Callable,
                         check_results,
                         _):
        for user_id, delay_range, *args in check_results:
            for user in self._users.gets_with_restrict(user_id, task):
                delay = random.uniform(*delay_range)
                self._loop.call_later(
                    delay, handle_work, handle_unique, user, task, func_work, *args)

    async def _wait(self, task,
                    handle_work: Callable,
                    handle_unique: Callable,
                    func_work: Callable,
                    check_results,
                    return_results: bool):
        if not return_results:
            for user_id, _, *args in check_results:
                for user in self._users.gets_with_restrict(user_id, task):
                    await handle_work(handle_unique, user, task, func_work, *args)
            return None

        results = []
        for user_id, _, *args in check_results:
            for user in self._users.gets_with_restrict(user_id, task):
                results.append(await handle_work(handle_unique, user, task, func_work, *args))
        return results

    async def _wait_and_pass(self, task,
                             handle_work: Callable,
                             handle_unique: Callable,
                             func_work: Callable,
                             check_results,
                             return_results: bool):
        if not return_results:
            for user_id, _, *args in check_results:
                result = args
                for user in self._users.gets_with_restrict(user_id, task):
                    result = await handle_work(handle_unique, user, task, func_work, *result)
            return None

        results = []
        for user_id, _, *args in check_results:
            result = args
            for user in self._users.gets_with_restrict(user_id, task):
                result = await handle_work(handle_unique, user, task, func_work, *(result[-1]))
                results.append(result[:-1])
        return results

    '''
    设有 task 参数传入。是传一个类，而不是实例对象！
    class Task:
        async def check()

        async def 工作函数()  # work / webconsole_work / cmdconsole_work
    '''

    # handle_check notifier 执行 task.check 函数时的包裹函数
    # handle_works notifier 执行 task 的"工作函数"时的包裹函数
    # handle_work 执行具体每个 user 的"工作函数"时外层包裹函数，WAIT WAIT_AND_PASS 时无效,一定是forced的
    # handle_unique 执行具体每个 user 的"工作函数时"时内层包裹函数  _unique_work / _multi_work
    # func_work "工作函数" eg: task.work
    async def exec_task(self, task, *args, **kwargs):
        handle_check = None
        handle_works = None
        handle_work = None
        func_work = None
        handle_unique = None
        need_results = None

        if task.TASK_TYPE == TaskType.SCHED:
            handle_check = self.run_sched_func_with_return
            func_work = task.work
            need_results = False
        elif task.TASK_TYPE == TaskType.FORCED:
            handle_check = self.run_forced_func
            func_work = task.work
            need_results = False
        elif task.TASK_TYPE == TaskType.CONSOLE:
            handle_check = self.run_forced_func
            ctrl, *args = args  # 此时ctrl隐含在args中
            if ctrl == 'web':
                func_work = task.web_console_work
                need_results = True
            elif ctrl == 'cmd':
                func_work = task.cmd_console_work
                need_results = False

        if task.HOW2CALL == How2Call.DONT_WAIT:
            handle_works = self._dont_wait
            if task.TASK_TYPE == TaskType.SCHED:
                handle_work = self.run_sched_func_bg
            else:
                handle_work = self.run_forced_func_bg
        elif task.HOW2CALL == How2Call.WAIT:
            handle_works = self._wait
            handle_work = self.run_forced_func
        elif task.HOW2CALL == How2Call.WAIT_AND_PASS:
            handle_works = self._wait_and_pass
            handle_work = self.run_forced_func

        if task.UNIQUE_TYPE == UniqueType.MULTI:
            handle_unique = self._multi_work
        elif task.UNIQUE_TYPE == UniqueType.UNIQUE:
            handle_unique = self._unique_work

        check_results = await handle_check(task.check, self._users.superuser, *args, **kwargs)
        print('check_results:', task, check_results)
        if check_results is not None:
            return await handle_works(task, handle_work, handle_unique, func_work, check_results, need_results)

    async def exec_func(self, func: Callable, *args, **kwargs):
        return await func(self._users.superuser, *args, **kwargs)

    def exec_task_no_wait(self, task, *args, **kwargs):
        self._loop.create_task(self.exec_task(task, *args, **kwargs))

    def get_users(self, user_id: int):
        return self._users.gets(user_id)


var_notifier = Notifier()


def init(**kwargs):
    var_notifier.init(**kwargs)


async def exec_task(task, *args, **kwargs):
    return await var_notifier.exec_task(task, *args, **kwargs)


def exec_task_no_wait(task, *args, **kwargs):
    var_notifier.exec_task_no_wait(task, *args, **kwargs)


async def exec_func(func: Callable, *args, **kwargs):
    return await var_notifier.exec_func(func, *args, **kwargs)


async def pause():
    await var_notifier.pause()


async def resume():
    await var_notifier.resume()


async def add_user(**kwargs):
    await var_notifier.add_user(**kwargs)


def get_users(user_id: int):
    return var_notifier.get_users(user_id)
