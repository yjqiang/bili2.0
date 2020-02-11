# https://github.com/yjqiang/YjMonitor

from printer import info as print
import bili_statistics
from danmu.yj_monitor_abc import yj_monitor
from tasks.guard_raffle_handler import GuardRafflJoinTask
from tasks.storm_raffle_handler import StormRaffleJoinTask
from tasks.pk_raffle_handler import PkRaffleJoinTask
from tasks.tv_raffle_handler import TvRaffleJoinTask
from . import raffle_handler


class TcpYjMonitorClient(yj_monitor.TcpDanmuClient):
    __slots__ = ()

    def handle_danmu(self, data: dict) -> bool:
        raffle_type = data['raffle_type']
        raffle_id = data['raffle_id']
        raffle_roomid = data['room_id']
        if raffle_type == 'STORM':
            print(f'{self._area_id} 号数据连接检测到{raffle_roomid:^9}的节奏风暴(id: {raffle_id})')
            raffle_handler.exec_at_once(StormRaffleJoinTask, 0, raffle_id)
            bili_statistics.add2pushed_raffles('Yj协同节奏风暴', 2)
        elif raffle_type == 'GUARD':
            print(f'{self._area_id} 号数据连接检测到{raffle_roomid:^9}的大航海(id: {raffle_id})')
            json_rsp = {
                'data': {
                    'guard': [data['other_raffle_data']]
                }
            }
            # dict 不可以用于 raffle_handler.py 的 set 机制
            raffle_handler.exec_at_once(GuardRafflJoinTask, raffle_roomid, json_rsp)
            bili_statistics.add2pushed_raffles('Yj协同大航海', 2)
        elif raffle_type == 'PK':
            print(f'{self._area_id} 号数据连接检测到{raffle_roomid:^9}的大乱斗(id: {raffle_id})')
            raffle_handler.push2queue(PkRaffleJoinTask, raffle_roomid)
            bili_statistics.add2pushed_raffles('Yj协同大乱斗', 2)
        elif raffle_type == 'TV':
            print(f'{self._area_id} 号数据连接检测到{raffle_roomid:^9}的小电视(id: {raffle_id})')
            json_rsp = {
                'data': {
                    'gift': [data['other_raffle_data']]
                }
            }
            # dict 不可以用于 raffle_handler.py 的 set 机制
            raffle_handler.exec_at_once(TvRaffleJoinTask, raffle_roomid, json_rsp)
            bili_statistics.add2pushed_raffles('Yj协同小电视', 2)
        return True
