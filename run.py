import sys
import signal
import threading
import asyncio

import aiohttp

import conf_loader
import notifier
import bili_sched
import printer
import bili_statistics
from utils import wrap_func_as_coroutine
from bili_console import BiliConsole
from user import User
from tasks.login import LoginTask
from tasks.live_daily_job import (
    HeartBeatTask,
    RecvHeartGiftTask,
    OpenSilverBoxTask,
    RecvDailyBagTask,
    SignTask,
    WatchTvTask,
    SignFansGroupsTask,
    SendGiftTask,
    ExchangeSilverCoinTask
)
from tasks.main_daily_job import (
    JudgeCaseTask,
    BiliMainTask,
    DahuiyuanTask
)
from tasks.manga_daily_job import (
    ShareComicTask,
    MangaSignTask,
)
from tasks.utils import UtilsTask
# 弹幕
from danmu.bili_danmu_monitor import DanmuPrinter, DanmuRaffleMonitor
from danmu.yj_monitor import TcpYjMonitorClient
from danmu import raffle_handler
# 实物抽奖
from substance.monitor_substance_raffle import SubstanceRaffleMonitor
from dyn.monitor_dyn_raffle import DynRaffleMonitor


loop = asyncio.get_event_loop()

dict_user = conf_loader.read_user()
dict_bili = conf_loader.read_bili()
dict_color = conf_loader.read_color()
dict_ctrl = conf_loader.read_ctrl()
dict_task = conf_loader.read_task()
printer.init_config(dict_color, dict_ctrl['print_control']['danmu'])

# user设置
users = []
global_task_control = dict_task['global_task_control']
custom_task_control = dict_task['custom_task_control']
global_task_arrangement = dict_task['global_task_arrangement']
custom_task_arrangement = dict_task['custom_task_arrangement']


for user_info in dict_user['users']:
    username = user_info['username']
    if username in custom_task_control:
        task_control = {**global_task_control, **custom_task_control[username]}
    else:
        task_control = global_task_control
    if username in custom_task_arrangement:
        task_arrangement = {**global_task_arrangement, **custom_task_arrangement[username]}
    else:
        task_arrangement = global_task_arrangement

    user = loop.run_until_complete(
        wrap_func_as_coroutine(User,
                               dict_user=user_info,
                               task_ctrl=task_control,
                               task_arrangement=task_arrangement,
                               dict_bili=dict_bili,
                               force_sleep=bili_sched.force_sleep))
    users.append(user)
notifier.init(users=users)


# 时间间隔为小时，同时每次休眠结束都会计时归零，重新从当前时间计算时间间隔
# 下面表示每隔多少小时执行一次
bili_sched.add_daily_jobs(HeartBeatTask, every_hours=6)
bili_sched.add_daily_jobs(RecvHeartGiftTask, every_hours=6)
bili_sched.add_daily_jobs(OpenSilverBoxTask, every_hours=6)
bili_sched.add_daily_jobs(RecvDailyBagTask, every_hours=3)
bili_sched.add_daily_jobs(SignTask, every_hours=6)
bili_sched.add_daily_jobs(WatchTvTask, every_hours=6)
bili_sched.add_daily_jobs(SignFansGroupsTask, every_hours=6)
bili_sched.add_daily_jobs(SendGiftTask, every_hours=2)
bili_sched.add_daily_jobs(ExchangeSilverCoinTask, every_hours=6)
bili_sched.add_daily_jobs(JudgeCaseTask, every_hours=0.75)
bili_sched.add_daily_jobs(BiliMainTask, every_hours=4)
bili_sched.add_daily_jobs(MangaSignTask, every_hours=6)
bili_sched.add_daily_jobs(ShareComicTask, every_hours=6)
bili_sched.add_daily_jobs(DahuiyuanTask, every_hours=6)

loop.run_until_complete(notifier.exec_task(LoginTask))

other_control = dict_ctrl['other_control']
area_ids = loop.run_until_complete(notifier.exec_func(UtilsTask.fetch_blive_areas))
area_duplicated = other_control['area_duplicated']
if area_duplicated:
    area_ids *= 2
bili_statistics.init(area_num=len(area_ids), area_duplicated=area_duplicated)
default_roomid = other_control['default_monitor_roomid']


# aiohttp sb session
async def init_monitors():
    yjmonitor_tcp_addr = other_control['yjmonitor_tcp_addr']
    yjmonitor_tcp_key = other_control['yjmonitor_tcp_key']

    raffle_danmu_areaids = area_ids
    printer_danmu_roomid = default_roomid
    yjmonitor_tcp_addr = yjmonitor_tcp_addr
    yjmonitor_tcp_key = yjmonitor_tcp_key
    session = aiohttp.ClientSession()

    _danmu_monitors = []

    for area_id in raffle_danmu_areaids:
        monitor = DanmuRaffleMonitor(
            room_id=0,
            area_id=area_id,
            session=session)
        _danmu_monitors.append(monitor)

    if yjmonitor_tcp_key:
        monitor = TcpYjMonitorClient(
            key=yjmonitor_tcp_key,
            url=yjmonitor_tcp_addr,
            area_id=0)
        _danmu_monitors.append(monitor)

    _danmu_printer = DanmuPrinter(
        room_id=printer_danmu_roomid,
        area_id=-1,
        session=session)

    if other_control['substance_raffle']:
        _danmu_monitors.append(SubstanceRaffleMonitor())
    if other_control['dyn_raffle']:
        _danmu_monitors.append(DynRaffleMonitor(
            should_join_immediately=other_control['join_dyn_raffle_at_once']))
    return _danmu_printer, _danmu_monitors
danmu_printer, monitors = loop.run_until_complete(init_monitors())
bili_sched.init(monitors=monitors, sleep_ranges=dict_ctrl['other_control']['sleep_ranges'])


# 初始化控制台
if sys.platform != 'linux' or signal.getsignal(signal.SIGHUP) == signal.SIG_DFL:
    console_thread = threading.Thread(
        target=BiliConsole(loop, default_roomid, danmu_printer).cmdloop)
    console_thread.start()
else:
    console_thread = None

tasks = [monitor.run() for monitor in monitors]
other_tasks = [
    bili_sched.run(),
    raffle_handler.run(),
    danmu_printer.run()
]
if other_tasks:
    loop.run_until_complete(asyncio.wait(tasks+other_tasks))
loop.run_forever()
if console_thread is not None:
    console_thread.join()
