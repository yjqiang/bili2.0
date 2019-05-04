import asyncio
from datetime import datetime
from typing import Optional

import schedule

import notifier
from printer import info as print


class BiliSched:
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        if loop is None:
            self._loop = asyncio.get_event_loop()
        else:
            self._loop = loop
        self._running = True
        self._sched_daily_jobs = schedule.Scheduler()
        self._sched_shedule = schedule.Scheduler()

        self._monitors = []

    def init(self, monitors: list, sleep_ranges: list):
        self._monitors = monitors
        for sleep_time, wake_time in sleep_ranges:
            self._sched_shedule.every().day.at(sleep_time.strftime("%H:%M:%S")).do(self.sleeping)
            self._sched_shedule.every().day.at(wake_time.strftime("%H:%M:%S")).do(self.waking_up)

        # 如果在休眠期间，就关闭self._running
        cur_time = datetime.now().time()
        for sleep_time, wake_time in sleep_ranges:
            if sleep_time <= cur_time <= wake_time:
                self._running = False
                return

    # 这是日常任务装载
    def add_daily_jobs(self, task, every_hours: float, *args, **kwargs):
        self._sched_daily_jobs.every(every_hours).hours.do(
            notifier.exec_task_no_wait, task, *args, **kwargs)

    def sleeping(self):
        print('🌇去睡吧')
        self._running = False

    def waking_up(self):
        print('🌅起床啦')
        self._running = True

    async def resume(self):
        for i in self._monitors:
            i.resume()
        await notifier.resume()

    async def pause(self):
        for i in self._monitors:
            i.pause()
        await notifier.pause()

    def do_nothing(self):
        return

    @staticmethod
    def out_of_jail():
        for user in notifier.get_users(-2):
            user.out_of_jail()

    async def run(self):
        # 如果不装载任务，会挂在idle_seconds处
        self._sched_shedule.every().day.do(self.do_nothing)
        self._sched_daily_jobs.every().day.do(self.do_nothing)
        self._sched_daily_jobs.every(4).hours.do(self.out_of_jail)

        while True:
            self._sched_shedule.run_pending()
            if self._running:
                await self.resume()
                self._sched_daily_jobs.run_all()
                while True:
                    # print(self._sched_daily_jobs.jobs)
                    self._sched_daily_jobs.run_pending()
                    self._sched_shedule.run_pending()
                    if not self._running:
                        break
                    idle_seconds = min(self._sched_daily_jobs.idle_seconds, self._sched_shedule.idle_seconds)
                    print(f'Will sleep {idle_seconds}s，等待任务装载')
                    await asyncio.sleep(idle_seconds)
            await self.pause()
            idle_seconds = self._sched_shedule.idle_seconds
            print(f'Will sleep {idle_seconds}s, 等待唤醒')
            await asyncio.sleep(idle_seconds)


var_bili_sched = BiliSched()


def init(*args, **kwargs):
    var_bili_sched.init(*args, **kwargs)


def add_daily_jobs(task, every_hours: float, *args, **kwargs):
    var_bili_sched.add_daily_jobs(task, every_hours, *args, **kwargs)


async def run():
    await var_bili_sched.run()
