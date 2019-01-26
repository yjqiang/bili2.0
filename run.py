import sys
import threading
import asyncio
from os import path
import connect
import conf_loader
import notifier
import raffle_handler
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
from monitor_substance_raffle import SubstanceRaffleMonitor

root_path = path.dirname(path.realpath('__file__'))
conf_loader.set_path(root_path)

if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()
        
dict_user = conf_loader.read_user()
dict_bili = conf_loader.read_bili()
dict_color = conf_loader.read_color()
printer.init_config(dict_color, dict_user['print_control']['danmu'])
area_ids = dict_user['other_control']['area_ids']

users = []
task_control = dict_user['task_control']
for i, user_info in enumerate(dict_user['users']):
    users.append(User(i, user_info, task_control, dict_bili))


notifier.set_values(loop)
notifier.set_users(users)
bili_statistics.init_area_num(len(area_ids))
    

    
loop.run_until_complete(asyncio.wait([notifier.exec_func(-2, LoginTask.handle_login_status)]))

# users[1].fall_in_jail()

console_thread = threading.Thread(target=Biliconsole(loop).cmdloop)
console_thread.start()

danmu_tasks = [connect.RaffleConnect(i).run() for i in area_ids]

yj_danmu_roomid = dict_user['other_control']['raffle_minitor_roomid']
danmu_tasks.append(connect.YjConnection(yj_danmu_roomid).run())

default_monitor_roomid = dict_user['other_control']['default_monitor_roomid']
connect.init_danmu_roomid(default_monitor_roomid)
danmu_tasks.append(connect.run_danmu())


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
    raffle_handler.run(),
    # SubstanceRaffleMonitor().run()
    ]

loop.run_until_complete(asyncio.wait(other_tasks+danmu_tasks))
console_thread.join()

