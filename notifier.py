import asyncio
import random
from typing import Optional, List, Callable

import aiojobs

import bili_statistics
from user import User
from tasks.base_class import TaskType
from printer import info as print


class Users:
    __slots__ = ('_users', )

    def __init__(self, users: List[User]):
        self._users = users

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._users[key]
        return None

    @property
    def superuser(self) -> User:
        return self._users[0]

    def gets_with_restrict(self, index: int, task_name: str):
        for user in self.gets(index):
            if user.is_in_jail and task_name in (
                    'recv_heart_gift',
                    'open_silver_box',
                    'join_storm_raffle',
                    'join_guard_raffle',
                    'join_tv_raffle'):
                continue
            if task_name != 'null':  # null 就忽略过滤，直接参与
                if f'probability_{task_name}' in user.task_arrangement:  # 平均概率筛选
                    if not random.random() < user.task_arrangement[f'probability_{task_name}']:
                        continue
                if not bili_statistics.add2tasks_records(  # 每日次数筛选
                        user_id=user.id,
                        task_name=task_name,
                        max_time=user.task_arrangement.get(task_name, -1)):
                    continue
            yield user

    def gets(self, index: int):
        if index == -2:
            for user in self._users:
                yield user
            return
        # TODO: 废除，统一为0
        if index == -1:
            index = 0
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

    def init(self, users: List[User]):
        self._users = Users(users)

    # pause 和 resume 必须在同一个循环里面用，否则可能发生类似线程不安全的东西
    async def resume(self):
        if self._scheduler is None:
            self._scheduler = await aiojobs.create_scheduler()

    async def pause(self):
        if self._scheduler is not None and not self._scheduler.closed:
            scheduler = self._scheduler
            self._scheduler = None
            await scheduler.close()

    async def run_sched_func(self, user: User, func: Callable, *args, **kwargs):
        scheduler = self._scheduler
        if scheduler is not None and not scheduler.closed:
            await scheduler.spawn(user.exec_func(func, *args, **kwargs))

    # 这里是为了日常任务的check问题
    async def run_sched_func_with_return(self, user: User, func: Callable, *args, **kwargs):
        scheduler = self._scheduler
        if scheduler is not None and not scheduler.closed:
            return await user.exec_func(func, *args, **kwargs)

    def run_sched_func_bg(self, *args, **kwargs):
        self._loop.create_task(self.run_sched_func(*args, **kwargs))

    # 那些间隔性推送的，推送型的task禁止使用wait until all done功能
    async def exec_sched_task(self, task, *args, **kwargs):
        check_results = await self.run_sched_func_with_return(
            self._users.superuser, task.check, *args, **kwargs)
        print('check_results:', task, check_results)
        if check_results is None:
            return
        for user_id, delay_range, *args in check_results:
            if delay_range is not None:
                for user in self._users.gets_with_restrict(user_id, task.TASK_NAME):
                    delay = random.uniform(*delay_range)
                    self._loop.call_later(
                        delay, self.run_sched_func_bg, user, task.work, *args)

    @staticmethod
    async def run_forced_func(user: User, func: Callable, *args, **kwargs):
        return await user.exec_func(func, *args, **kwargs)

    def run_forced_func_bg(self, *args, **kwargs):
        self._loop.create_task(self.run_forced_func(*args, **kwargs))

    # 普通task,执行就完事了,不会受scheduler影响（不被cancel，一直执行到结束)
    async def exec_forced_task(self, task, *args, **kwargs):
        check_results = await self.run_forced_func(
            self._users.superuser, task.check, *args, **kwargs)
        print('check_results:', task, check_results)
        if check_results is None:
            return
        for user_id, delay_range, *args in check_results:
            if delay_range is not None:
                for user in self._users.gets_with_restrict(user_id, task.TASK_NAME):
                    delay = random.uniform(*delay_range)
                    self._loop.call_later(
                        delay, self.run_forced_func_bg, user, task.work, *args)
            else:  # 这里是特殊处理为None的时候，去依次执行，且wait untill all done
                result = None
                for user in self._users.gets_with_restrict(user_id, task.TASK_NAME):
                    if result is None:
                        result = await self.run_forced_func(
                            user, task.work, *args)
                    else:  # 不为None表示每个用户之间参数互传
                        result = await self.run_forced_func(
                            user, task.work, *args, result)
                return result

    async def exec_task(self, task, *args, **kwargs):
        if task.TASK_TYPE == TaskType.SCHED_TASK:
            return await self.exec_sched_task(task, *args, **kwargs)
        if task.TASK_TYPE == TaskType.FORCED_TASK:
            return await self.exec_forced_task(task, *args, **kwargs)

    async def exec_func(self, func: Callable, *args, **kwargs):
        return await self._users.superuser.exec_func(func, *args, **kwargs)

    def exec_task_no_wait(self, task, *args, **kwargs):
        self._loop.create_task(self.exec_task(task, *args, **kwargs))

    def get_users(self, user_id: int):
        return self._users.gets(user_id)


var_notifier = Notifier()


def init(*args, **kwargs):
    var_notifier.init(*args, **kwargs)


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


def get_users(user_id: int):
    return var_notifier.get_users(user_id)
