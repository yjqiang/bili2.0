import asyncio
import aiohttp
import utils
import printer
import notifier
import bili_statistics
from .base_danmu import BaseDanmu
from .yj_monitor import YjMonitorDanmu, YjMonitorTcp
from tasks.tv_raffle_handler import TvRaffleHandlerTask
from tasks.guard_raffle_handler import GuardRaffleHandlerTask
from tasks.storm_raffle_handler import StormRaffleHandlerTask
from tasks.utils import UtilsTask
from . import raffle_handler


class PrinterDanmu(BaseDanmu):
    def handle_danmu(self, dict_danmu):
        cmd = dict_danmu['cmd']
        if cmd == 'DANMU_MSG':
            printer.print_danmu(dict_danmu)
        return True
        

class RaffleDanmu(BaseDanmu):
    async def _check_area(self):
        try:
            while True:
                await asyncio.sleep(300)
                is_ok = await asyncio.shield(notifier.exec_func(-1, UtilsTask.is_ok_as_monitor, self._room_id, self._area_id))
                if not is_ok:
                    printer.infos([f'{self._room_id}不再适合作为监控房间，即将切换'])
                    return
        except asyncio.CancelledError:
            pass
            
    def handle_danmu(self, dict_danmu):
        cmd = dict_danmu['cmd']
        
        if cmd == 'PREPARING':
            printer.infos([f'{self._area_id}号弹幕监控房间下播({self._room_id})'])
            return False
    
        elif cmd == 'NOTICE_MSG':
            # 1 《第五人格》哔哩哔哩直播预选赛六强诞生！
            # 2 全区广播：<%user_name%>送给<%user_name%>1个嗨翻全城，快来抽奖吧
            # 3 <%user_name%> 在 <%user_name%> 的房间开通了总督并触发了抽奖，点击前往TA的房间去抽奖吧
            # 4 欢迎 <%总督 user_name%> 登船
            # 5 恭喜 <%user_name%> 获得大奖 <%23333x银瓜子%>, 感谢 <%user_name%> 的赠送
            # 6 <%user_name%> 在直播间 <%529%> 使用了 <%20%> 倍节奏风暴，大家快去跟风领取奖励吧！(只报20的)
            msg_type = dict_danmu['msg_type']
            msg_common = dict_danmu['msg_common']
            real_roomid = dict_danmu['real_roomid']
            msg_common = dict_danmu['msg_common'].replace(' ', '')
            msg_common = msg_common.replace('”', '')
            msg_common = msg_common.replace('“', '')
            if msg_type == 2 or msg_type == 8:
                str_gift = msg_common.split('%>')[-1].split('，')[0]
                if '个' in str_gift:
                    raffle_num, raffle_name = str_gift.split('个')
                elif '了' in str_gift:
                    raffle_num = 1
                    raffle_name = str_gift.split('了')[-1]
                else:
                    raffle_num = 1
                    raffle_name = str_gift
                broadcast = msg_common.split('广播')[0]
                printer.infos([f'{self._area_id}号弹幕监控检测到{real_roomid:^9}的{raffle_name}'])
                raffle_handler.push2queue(TvRaffleHandlerTask, real_roomid)
                broadcast_type = 0 if broadcast == '全区' else 1
                bili_statistics.add2pushed_raffles(raffle_name, broadcast_type, raffle_num)
            elif msg_type == 3:
                raffle_name = msg_common.split('开通了')[-1][:2]
                printer.infos([f'{self._area_id}号弹幕监控检测到{real_roomid:^9}的{raffle_name}'])
                raffle_handler.push2queue(GuardRaffleHandlerTask, real_roomid)
                broadcast_type = 0 if raffle_name == '总督' else 2
                bili_statistics.add2pushed_raffles(raffle_name, broadcast_type)
            elif msg_type == 6:
                raffle_name = '二十倍节奏风暴'
                printer.infos([f'{self._area_id}号弹幕监控检测到{real_roomid:^9}的{raffle_name}'])
                # raffle_handler.push2queue(StormRaffleHandlerTask, real_roomid)
                bili_statistics.add2pushed_raffles(raffle_name)
        return True
        
    async def run_forever(self):
        self._waiting = self._loop.create_future()
        time_now = 0
        while not self._closed:
            if utils.curr_time() - time_now <= 3:
                printer.infos([f'网络波动，{self._area_id}号弹幕姬延迟3秒后重启'])
                await asyncio.sleep(3)
            printer.infos([f'正在启动{self._area_id}号弹幕姬'])
            time_now = utils.curr_time()
            
            async with self._conn_lock:
                if self._closed:
                    break
                self._room_id = await notifier.exec_func(
                    -1, UtilsTask.get_room_by_area,
                    self._area_id, self._room_id)
                if not await self._open_conn():
                    continue
                
                self._task_main = asyncio.ensure_future(self._read_datas())
                task_heartbeat = asyncio.ensure_future(self._heart_beat())
                task_checkarea = asyncio.ensure_future(self._check_area())
            tasks = [self._task_main, task_heartbeat, task_checkarea]
            _, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED)
            printer.infos([f'{self._area_id}号弹幕姬异常或主动断开，正在处理剩余信息'])
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            if not task_checkarea.done():
                task_checkarea.cancel()
            await self._close_conn()
            await asyncio.wait(pending)
            printer.infos([f'{self._area_id}号弹幕姬退出，剩余任务处理完毕'])
        self._waiting.set_result(True)

                        
async def run_danmu_monitor(
        raffle_danmu_areaids,
        yjmonitor_danmu_roomid,
        printer_danmu_roomid,
        yjmonitor_tcp_addr,
        yjmonitor_tcp_key,
        future=None
        ):
    session = aiohttp.ClientSession()
    
    tasks = []
    tasks.append(asyncio.ensure_future(raffle_handler.run()))
    for area_id in raffle_danmu_areaids:
        task = asyncio.ensure_future(
            RaffleDanmu(0, area_id, session).run_forever())
        tasks.append(task)
        
    if yjmonitor_danmu_roomid:
        task = asyncio.ensure_future(
            YjMonitorDanmu(yjmonitor_danmu_roomid, 0, session).run_forever())
        tasks.append(task)
    elif yjmonitor_tcp_key:
        task = asyncio.ensure_future(
            YjMonitorTcp(yjmonitor_tcp_addr, 0, yjmonitor_tcp_key).run_forever())
        tasks.append(task)
    
    printer_danmu = PrinterDanmu(printer_danmu_roomid, -1, session)
    if future is not None:
        future.set_result(printer_danmu)
    task = asyncio.ensure_future(
            printer_danmu.run_forever())
    tasks.append(task)
    
    await asyncio.wait(tasks)
    
