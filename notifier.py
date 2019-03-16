# 总控制中心,外界调用task的入口
import asyncio
from typing import Optional
from random import uniform


class Notifier:
    def set_values(self, loop):
        self._loop = loop
        
    def set_users(self, list_users):
        # -2表示广播, -1表示super_user, >0表示普通
        self.users = list_users
        self.super_userid = 0
        
    # id >=0, -1
    async def notify(self, id, func, *args):
        if id == -1:
            id = self.super_userid
        if 0 <= id < len(self.users):
            result = await self.users[id].accept(func, *args)
            return result
        return None
        
    async def notify_all(self, func, *args):
        for user in self.users:
            result = await user.accept(func, *args)
            # print('notify_all 结果', result)
        return result
        
    # delay_range 是一个tuple,里面是左右区间
    # 接受id -2/-1/>=0, 输出id >=0
    def __set_delay(self, delay_range, id):
        if delay_range is None:
            delay_range = 0, 0
        if id == -2:
            return tuple((i, uniform(*delay_range)) for i in range(len(self.users)))
        if id == -1:
            id = self.super_userid
        return (id, uniform(*delay_range)),
    
    # 接受id >=0
    async def __exec_one_step(self, id, task, step, future: Optional[asyncio.Future], *args):
        # print('当前请求', task, id, step, args)
        func = task.target(step)
        assert func is not None
        results = await self.notify(id, func, *args)
        # results为()或None,就terminate,不管是否到头，这里的设计是user的拒绝执行的功能
        # 返回必须是tuple/list！
        # print('结果返回', results)
        if future is None:
            if results is None:
                return
            for new_step, *result in results:
                # user的延迟执行功能实现
                if new_step == -1:
                    new_step = step
                # print(f'本step结果:{result} 下一步:{new_step}')
                delay, new_uid, *args = result
                self.call_after(delay, new_uid, task, new_step, False, *args)
            return

        if results is None:
            future.set_result([])
            return
        new_futures = []
        for new_step, *result in results:
            # user的延迟执行功能实现
            if new_step == -1:
                new_step = step
            # print(f'本step结果:{result} 下一步:{new_step}')
            delay, new_uid, *args = result
            new_futures += (self.call_after(delay, new_uid, task, new_step, True, *args))
        # print('!!!!!', func, id, args, new_futures)
        future.set_result(new_futures)  # 这里就是下一步的所有future监控list
        
    def __exec_bg(self, *args):
        asyncio.ensure_future(self.__exec_one_step(*args))
                
    # 接受uid -2/-1/>=0
    def call_after(self, delay_range, id, task, step, with_future: bool, *args):
        if not with_future:
            for new_id, delay in self.__set_delay(delay_range, id):
                # 这里用callafter api把notify送到queue里面立刻退出,所以不会爆
                self._loop.call_later(delay, self.__exec_bg, new_id, task, step, None, *args)
            return None
        futures = []
        for new_id, delay in self.__set_delay(delay_range, id):
            # 这里用callafter api把notify送到queue里面立刻退出,所以不会爆
            future = self._loop.create_future()
            self._loop.call_later(delay, self.__exec_bg, new_id, task, step, future, *args)
            futures.append(future)
        return futures
                

var = Notifier()


def set_values(loop):
    var.set_values(loop)


def set_users(users):
    var.set_users(users)

# 一种真task,不需要返回值的(task里面多个函数)
# 一种伪task,需要立刻返回(task可以认为里面就一个函数)


# 不会返回值, task
def exec_task(id, task, step, *args, delay_range=None):
    # print('测试task', id, task, step, *args, delay_range)
    var.call_after(delay_range, id, task, step, False, *args)


async def exec_task_awaitable(id, task, step, *args, delay_range=None):
    list_futures = [var.call_after(delay_range, id, task, step, True, *args)]

    while list_futures:
        new_list_futures = []
        for futures in list_futures:
            if futures:  # 万一futures是[]
                # print(futures)
                new_list_futures += await asyncio.gather(*futures)
                # print('结果', new_list_futures)
        list_futures = new_list_futures

    print('Done')


# 伪task
async def exec_func(id, func, *args):
    if id == -2:
        result = await var.notify_all(func, *args)
    else:
        result = await var.notify(id, func, *args)
    return result
