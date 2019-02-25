import json
import asyncio
import aiohttp
import utils
import printer
import notifier
import bili_statistics
from danmu import BaseDanmu
from tasks.tv_raffle_handler import TvRaffleHandlerTask
from tasks.guard_raffle_handler import GuardRaffleHandlerTask
from tasks.storm_raffle_handler import StormRaffleHandlerTask
from tasks.utils import UtilsTask
import raffle_handler


class PrinterDanmu(BaseDanmu):
    def handle_danmu(self, body):
        dic = json.loads(body.decode('utf-8'))
        cmd = dic['cmd']
        if cmd == 'DANMU_MSG':
            printer.print_danmu(dic)
        return True
        

class RaffleDanmu(BaseDanmu):
    async def _check_area(self):
        try:
            while True:
                await asyncio.sleep(300)
                is_ok = await asyncio.shield(notifier.exec_func(-1, UtilsTask.is_ok_as_monitor, self._room_id, self._area_id))
                if not is_ok:
                    printer.info([f'{self._room_id}不再适合作为监控房间，即将切换'], True)
                    return
        except asyncio.CancelledError:
            pass
            
    def handle_danmu(self, body):
        dic = json.loads(body.decode('utf-8'))
        cmd = dic['cmd']
        
        if cmd == 'PREPARING':
            printer.info([f'{self._area_id}号弹幕监控房间下播({self._room_id})'], True)
            return False
    
        elif cmd == 'NOTICE_MSG':
            # 1 《第五人格》哔哩哔哩直播预选赛六强诞生！
            # 2 全区广播：<%user_name%>送给<%user_name%>1个嗨翻全城，快来抽奖吧
            # 3 <%user_name%> 在 <%user_name%> 的房间开通了总督并触发了抽奖，点击前往TA的房间去抽奖吧
            # 4 欢迎 <%总督 user_name%> 登船
            # 5 恭喜 <%user_name%> 获得大奖 <%23333x银瓜子%>, 感谢 <%user_name%> 的赠送
            # 6 <%user_name%> 在直播间 <%529%> 使用了 <%20%> 倍节奏风暴，大家快去跟风领取奖励吧！(只报20的)
            msg_type = dic['msg_type']
            msg_common = dic['msg_common']
            real_roomid = dic['real_roomid']
            msg_common = dic['msg_common'].replace(' ', '')
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
                printer.info([f'{self._area_id}号弹幕监控检测到{real_roomid:^9}的{raffle_name}'], True)
                raffle_handler.push2queue(TvRaffleHandlerTask, real_roomid)
                broadcast_type = 0 if broadcast == '全区' else 1
                bili_statistics.add2pushed_raffles(raffle_name, broadcast_type, raffle_num)
            elif msg_type == 3:
                raffle_name = msg_common.split('开通了')[-1][:2]
                printer.info([f'{self._area_id}号弹幕监控检测到{real_roomid:^9}的{raffle_name}'], True)
                raffle_handler.push2queue(GuardRaffleHandlerTask, real_roomid)
                broadcast_type = 0 if raffle_name == '总督' else 2
                bili_statistics.add2pushed_raffles(raffle_name, broadcast_type)
            elif msg_type == 6:
                raffle_name = '二十倍节奏风暴'
                printer.info([f'{self._area_id}号弹幕监控检测到{real_roomid:^9}的{raffle_name}'], True)
                # raffle_handler.push2queue(StormRaffleHandlerTask, real_roomid)
                bili_statistics.add2pushed_raffles(raffle_name)
        return True
        
    async def run_forever(self):
        self._waiting = asyncio.Future()
        time_now = 0
        while not self._closed:
            if utils.curr_time() - time_now <= 3:
                printer.info([f'网络波动，{self._area_id}号弹幕姬延迟3秒后重启'], True)
                await asyncio.sleep(3)
            printer.info([f'正在启动{self._area_id}号弹幕姬'], True)
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
            printer.info([f'{self._area_id}号弹幕姬异常或主动断开，正在处理剩余信息'], True)
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            if not task_checkarea.done():
                task_checkarea.cancel()
            await self._close_conn()
            await asyncio.wait(pending)
            printer.info([f'{self._area_id}号弹幕姬退出，剩余任务处理完毕'], True)
        self._waiting.set_result(True)

                                        
class YjMonitorDanmu(BaseDanmu):
    def __init__(self, room_id, area_id, client_session=None):
        super().__init__(room_id, area_id, client_session)
        keys = '阝飠牜饣卩卪厸厶厽孓宀巛巜彳廴彡彐忄扌攵氵灬爫犭疒癶礻糹纟罒罓耂虍訁覀兦亼亽亖亗吂卝匸皕旡玊尐幵朩囘囙囜囝囟囡団囤囥囦囧囨囩囪囫囬囮囯困囱囲図囵囶囷囸囹固囻囼图囿圀圁圂圃圄圅圆圇圉圊圌圍圎圏圐圑園圓圔圕圖圗團圙圚圛圜圝圞'
        self.__reverse_keys = {value: i for i, value in enumerate(keys)}
        self.__read = {}
    
    def __base2dec(self, str_num, base=110):
        result = 0
        for i in str_num:
            result = result * base + self.__reverse_keys[i]
        return result
    
    def __reverse(self, msg):
        msg = msg.replace('?', '')
        first = self.__reverse_keys.get(msg[0], -1)
        last = self.__reverse_keys.get(msg[-1], -1)
        
        # 校验
        if 0 <= first <= 109 and 0 <= last <= 109 and not (first + last - 109):
            type = msg[-2]
            msg_id, id = map(self.__base2dec, msg[:-2].split('.'))
            return msg_id, type, id
        return None
        
    def __combine_piece(self, uid, msg):
        # None/''
        if not msg:
            return None
        if uid not in self.__read:
            self.__read[uid] = {}
        user_danmus = self.__read[uid]
        msg_id, type, id = msg
        msg_id_wanted = (msg_id - 1) if (msg_id % 2) else (msg_id + 1)
        id_wanted = user_danmus.pop(msg_id_wanted, None)
        if id_wanted is not None:
            if msg_id % 2:
                return type, id_wanted, id
            else:
                return type, id, id_wanted
        else:
            user_danmus[msg_id] = id
            return None
        
    def handle_danmu(self, body):
        dic = json.loads(body.decode('utf-8'))
        cmd = dic['cmd']
        # print(cmd)
        if cmd == 'DANMU_MSG':
            info = dic['info']
            ori = info[1]
            uid = info[2][0]
            # print('测试', self.__read, ori)
            try:
                msg = self.__reverse(ori)
                if msg is not None:
                    msg_id, type, id = msg
                    if type == '~' and not msg_id % 2:
                        raffle_id = id
                        printer.info([f'{self._area_id}号弹幕监控检测到{"0":^9}的节奏风暴(id: {raffle_id})'], True)
                        # raffle_handler.exec_at_once(StormRaffleHandlerTask, 0, raffle_id)
                        bili_statistics.add2pushed_raffles('Yj协同节奏风暴', 2)
                result = self.__combine_piece(uid, msg)
                if result is None:
                    return True
                type, raffle_id, real_roomid = result
                if type == '+':
                    printer.info([f'{self._area_id}号弹幕监控检测到{real_roomid:^9}的大航海(id: {raffle_id})'], True)
                    raffle_handler.push2queue(GuardRaffleHandlerTask, real_roomid, raffle_id)
                    bili_statistics.add2pushed_raffles('Yj协同大航海', 2)
            except Exception:
                printer.warn(f'Yj监控房间内可能有恶意干扰{uid}: {ori}')
        return True

    
async def run_danmu_monitor(
        raffle_danmu_areaids,
        yjmonitor_danmu_roomid,
        printer_danmu_roomid,
        future=None
        ):
    session = aiohttp.ClientSession()
    
    tasks = []
    for area_id in raffle_danmu_areaids:
        task = asyncio.ensure_future(
            RaffleDanmu(0, area_id, session).run_forever())
        tasks.append(task)
        
    if yjmonitor_danmu_roomid:
        task = asyncio.ensure_future(
            YjMonitorDanmu(yjmonitor_danmu_roomid, 0, session).run_forever())
        tasks.append(task)
    
    printer_danmu = PrinterDanmu(printer_danmu_roomid, -1, session)
    if future is not None:
        future.set_result(printer_danmu)
    task = asyncio.ensure_future(
            printer_danmu.run_forever())
    tasks.append(task)
    
    await asyncio.wait(tasks)
    
