from config_loader import ConfigLoader
from task import RaffleHandler, Task, StateTask
from webhub.web_hub import WebHub, HostWebHub
import os
import sys
from bili_user.user import User
import asyncio
import printer
import connect
import bili_console
import threading
import bili_stats
from cdn import Host
from bili_user.super_user import SuperUser

if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()
fileDir = os.path.dirname(os.path.realpath('__file__'))
file_color = f'{fileDir}/config/color.toml'
file_user = f'{fileDir}/config/user.toml'
file_bili = f'{fileDir}/config/bili.toml'
file_ip = f'{fileDir}/config/ips.toml'
cfg = ConfigLoader(file_color, file_user, file_bili, file_ip)

dict_user = cfg.read_user()
dict_bili = cfg.read_bili()
dict_color = cfg.read_color()
dict_ip = cfg.read_ip()
printer.init_config(dict_color, dict_user['print_control']['danmu'])

users = []
task_control = dict_user['task_control']
if len(dict_user['users']) < 10:
    for i, user_info in enumerate(dict_user['users']):
        webhub = WebHub(i, user_info, dict_bili)
        users.append(User(i, user_info, webhub, task_control))
else:
    host = Host(dict_ip['list_ips'])
    loop.run_until_complete(host.proxies_filter())
    for i, user_info in enumerate(dict_user['users']):
        webhub = HostWebHub(i, user_info, dict_bili, host)
        users.append(User(i, user_info, webhub, task_control))

danmu_connection = connect.connect(dict_user['other_control']['default_monitor_roomid'])
list_raffle_connection = [connect.RaffleConnect(i) for i in range(1, 5)]
bili_stats.init_area_num(4)
list_raffle_connection_task = [i.run() for i in list_raffle_connection]
yjconnection = connect.YjConnection(dict_user['other_control']['raffle_minitor_roomid'])

var_super_user = SuperUser(users[0].webhub)
raffle = RaffleHandler(users, var_super_user, loop, True)
normal_task = Task(users, var_super_user, loop)
state_task = StateTask(users, var_super_user, loop)

loop.run_until_complete(asyncio.wait([normal_task.call_one_by_one('handle_login_status', ())]))

var_console = bili_console.Biliconsole(users, var_super_user, loop)
console_thread = threading.Thread(target=var_console.cmdloop)
console_thread.start()
normal_task.init()

tasks = [
    raffle.join_raffle(),
    danmu_connection.run(),
    state_task.run_workstate(),
    state_task.run_timestate(),
    yjconnection.run()
]


loop.run_until_complete(asyncio.wait(tasks + list_raffle_connection_task))
console_thread.join()
