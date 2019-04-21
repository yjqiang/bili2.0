import sys
import signal
import threading
import asyncio
from os import path
import conf_loader
import notifier
import bili_statistics
from bili_console import Biliconsole
import printer
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
    ExchangeSilverCoinTask,
)
from tasks.main_daily_job import (
    JudgeCaseTask,
    BiliMainTask
    
)
from danmu import monitor_danmu_raffle
from dyn.monitor_dyn_raffle import DynRaffleMonitor
from substance.monitor_substance_raffle import SubstanceRaffleMonitor

root_path = path.dirname(path.realpath(__file__))
conf_loader.set_path(root_path)

loop = asyncio.get_event_loop()
        
dict_user = conf_loader.read_user()
dict_bili = conf_loader.read_bili()
dict_color = conf_loader.read_color()
dict_ctrl = conf_loader.read_ctrl()
printer.init_config(dict_color, dict_ctrl['print_control']['danmu'])

users = []
task_control = dict_ctrl['task_control']
dyn_lottery_friends = [(str(uid), name) for uid, name in dict_ctrl['dyn_raffle']['dyn_lottery_friends'].items()]
for i, user_info in enumerate(dict_user['users']):
    users.append(User(i, user_info, task_control, dict_bili, dyn_lottery_friends))
notifier.set_values(loop)
notifier.set_users(users)
    
loop.run_until_complete(notifier.exec_func(-2, LoginTask.handle_login_status))

other_control = dict_ctrl['other_control']
area_ids = other_control['area_ids']
bili_statistics.init_area_num(len(area_ids))
default_roomid = other_control['default_monitor_roomid']

async def get_printer_danmu():
    future = asyncio.Future()
    yjmonitor_danmu_roomid = other_control['yjmonitor_danmu_roomid']
    yjmonitor_tcp_addr = other_control['yjmonitor_tcp_addr']
    yjmonitor_tcp_key = other_control['yjmonitor_tcp_key']
    asyncio.ensure_future(monitor_danmu_raffle.run_danmu_monitor(
            raffle_danmu_areaids=area_ids,
            yjmonitor_danmu_roomid=yjmonitor_danmu_roomid,
            printer_danmu_roomid=default_roomid,
            yjmonitor_tcp_addr=yjmonitor_tcp_addr,
            yjmonitor_tcp_key=yjmonitor_tcp_key,
            future=future))
    await future
    return future.result()

printer_danmu = loop.run_until_complete(get_printer_danmu())

if sys.platform != 'linux' or signal.getsignal(signal.SIGHUP) == signal.SIG_DFL:
    console_thread = threading.Thread(
        target=Biliconsole(loop, default_roomid, printer_danmu).cmdloop)
    console_thread.start()
else:
    console_thread = None


notifier.exec_task(-2, HeartBeatTask, 0, delay_range=(0, 5))
notifier.exec_task(-2, RecvHeartGiftTask, 0, delay_range=(0, 5))
notifier.exec_task(-2, OpenSilverBoxTask, 0, delay_range=(0, 5))
notifier.exec_task(-2, RecvDailyBagTask, 0, delay_range=(0, 5))
notifier.exec_task(-2, SignTask, 0, delay_range=(0, 5))
notifier.exec_task(-2, WatchTvTask, 0, delay_range=(0, 5))
notifier.exec_task(-2, SignFansGroupsTask, 0, delay_range=(0, 5))
notifier.exec_task(-2, SendGiftTask, 0, delay_range=(0, 5))
notifier.exec_task(-2, ExchangeSilverCoinTask, 0, delay_range=(0, 5))
notifier.exec_task(-2, JudgeCaseTask, 0, delay_range=(0, 5))
notifier.exec_task(-2, BiliMainTask, 0, delay_range=(0, 5))


other_tasks = [  
    SubstanceRaffleMonitor().run(),
    # DynRaffleMonitor(should_join_immediately=True).run(),
    ]
if other_tasks:
    loop.run_until_complete(asyncio.wait(other_tasks))
loop.run_forever()
if console_thread is not None:
    console_thread.join()

