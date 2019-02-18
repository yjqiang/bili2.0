import utils
import printer
import notifier
import bili_statistics
from tasks.tv_raffle_handler import TvRaffleHandlerTask
from tasks.guard_raffle_handler import GuardRaffleHandlerTask
from tasks.storm_raffle_handler import StormRaffleHandlerTask
from tasks.utils import UtilsTask
import raffle_handler
import asyncio
import aiohttp
import struct
import json
import sys


class BaseDanmu():
    structer = struct.Struct('!I2H2I')

    def __init__(self, room_id, area_id, client_session=None):
        if client_session is None:
            self.client = aiohttp.ClientSession()
        else:
            self.client = client_session
        self.ws = None
        self._area_id = area_id
        self.room_id = room_id
        # 建立连接过程中难以处理重设置房间问题
        self.lock_for_reseting_roomid_manually = asyncio.Lock()
        self.task_main = None
        self._bytes_heartbeat = self._wrap_str(opt=2, body='')
    
    @property
    def room_id(self):
        return self._room_id
        
    @room_id.setter
    def room_id(self, room_id):
        self._room_id = room_id
        str_conn_room = f'{{"uid":0,"roomid":{room_id},"protover":1,"platform":"web","clientver":"1.3.3"}}'
        self._bytes_conn_room = self._wrap_str(opt=7, body=str_conn_room)
        
    def _wrap_str(self, opt, body, len_header=16, ver=1, seq=1):
        remain_data = body.encode('utf-8')
        len_data = len(remain_data) + len_header
        header = self.structer.pack(len_data, len_header, ver, opt, seq)
        data = header + remain_data
        return data

    async def _send_bytes(self, bytes_data):
        try:
            await self.ws.send_bytes(bytes_data)
        except asyncio.CancelledError:
            return False
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        return True

    async def _read_bytes(self):
        bytes_data = None
        try:
            # 如果调用aiohttp的bytes read，none的时候，会raise exception
            msg = await asyncio.wait_for(self.ws.receive(), timeout=35.0)
            bytes_data = msg.data
        except asyncio.TimeoutError:
            print('# 由于心跳包30s一次，但是发现35内没有收到任何包，说明已经悄悄失联了，主动断开')
            return None
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            print('请联系开发者')
            return None
        
        return bytes_data
        
    async def open(self):
        try:
            url = 'wss://broadcastlv.chat.bilibili.com:443/sub'
            self.ws = await asyncio.wait_for(self.client.ws_connect(url), timeout=3)
        except:
            print("# 连接无法建立，请检查本地网络状况")
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        printer.info([f'{self._area_id}号弹幕监控已连接b站服务器'], True)
        return (await self._send_bytes(self._bytes_conn_room))
        
    async def heart_beat(self):
        try:
            while True:
                if not (await self._send_bytes(self._bytes_heartbeat)):
                    return
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            pass
            
    async def read_datas(self):
        while True:
            datas = await self._read_bytes()
            # 本函数对bytes进行相关操作，不特别声明，均为bytes
            if datas is None:
                return
            data_l = 0
            len_datas = len(datas)
            while data_l != len_datas:
                # 每片data都分为header和body，data和data可能粘连
                # data_l == header_l && next_data_l = next_header_l
                # ||header_l...header_r|body_l...body_r||next_data_l...
                tuple_header = self.structer.unpack_from(datas[data_l:])
                len_data, len_header, ver, opt, seq = tuple_header
                body_l = data_l + len_header
                next_data_l = data_l + len_data
                body = datas[body_l:next_data_l]
                # 人气值(或者在线人数或者类似)以及心跳
                if opt == 3:
                    # UserCount, = struct.unpack('!I', remain_data)
                    # printer.debug(f'弹幕心跳检测{self._area_id}')
                    pass
                # cmd
                elif opt == 5:
                    if not self.handle_danmu(body):
                        return
                # 握手确认
                elif opt == 8:
                    printer.info([f'{self._area_id}号弹幕监控进入房间（{self._room_id}）'], True)
                else:
                    printer.warn(datas[data_l:next_data_l])

                data_l = next_data_l

    # 待确认
    async def close(self):
        try:
            await self.ws.close()
        except:
            print('请联系开发者', sys.exc_info()[0], sys.exc_info()[1])
        if not self.ws.closed:
            printer.info([f'请联系开发者  {self._area_id}号弹幕收尾模块状态{self.ws.closed}'], True)
                
    def handle_danmu(self, body):
        return True
        
    async def run_forever(self):
        time_now = 0
        while True:
            if utils.curr_time() - time_now <= 3:
                printer.info([f'网络波动，{self._area_id}号弹幕姬延迟3秒后重启'], True)
                await asyncio.sleep(3)
            printer.info([f'正在启动{self._area_id}号弹幕姬'], True)
            time_now = utils.curr_time()
            
            async with self.lock_for_reseting_roomid_manually:
                is_open = await self.open()
            if not is_open:
                continue
            self.task_main = asyncio.ensure_future(self.read_datas())
            task_heartbeat = asyncio.ensure_future(self.heart_beat())
            tasks = [self.task_main, task_heartbeat]
            _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            printer.info([f'{self._area_id}号弹幕姬异常或主动断开，正在处理剩余信息'], True)
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            await self.close()
            await asyncio.wait(pending)
            printer.info([f'{self._area_id}号弹幕姬退出，剩余任务处理完毕'], True)
            
    async def reconnect(self, room_id):
        async with self.lock_for_reseting_roomid_manually:
            # not None是判断是否已经连接了的(重连过程中也可以处理)
            if self.ws is not None:
                await self.close()
            if self.task_main is not None:
                await self.task_main
            # 由于锁的存在，绝对不可能到达下一个的自动重连状态，这里是保证正确显示当前监控房间号
            self.room_id = room_id
            printer.info([f'{self._area_id}号弹幕姬已经切换房间（{room_id}）'], True)
    
    
class DanmuPrinter(BaseDanmu):
    def handle_danmu(self, body):
        dic = json.loads(body.decode('utf-8'))
        cmd = dic['cmd']
        if cmd == 'DANMU_MSG':
            printer.print_danmu(dic)
        return True
        

class DanmuRaffleHandler(BaseDanmu):
    async def check_area(self):
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
                raffle_handler.push2queue(StormRaffleHandlerTask, real_roomid)
                bili_statistics.add2pushed_raffles(raffle_name)
        return True
        
    async def run_forever(self):
        time_now = 0
        while True:
            if utils.curr_time() - time_now <= 3:
                printer.info([f'网络波动，{self._area_id}号弹幕姬延迟3秒后重启'], True)
                await asyncio.sleep(3)
            self.room_id = await notifier.exec_func(-1, UtilsTask.get_room_by_area, self._area_id)
            printer.info([f'正在启动{self._area_id}号弹幕姬'], True)
            time_now = utils.curr_time()
            async with self.lock_for_reseting_roomid_manually:
                is_open = await self.open()
            if not is_open:
                continue
            task_main = asyncio.ensure_future(self.read_datas())
            task_heartbeat = asyncio.ensure_future(self.heart_beat())
            task_checkarea = asyncio.ensure_future(self.check_area())
            tasks = [task_main, task_heartbeat, task_checkarea]
            _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            printer.info([f'{self._area_id}号弹幕姬异常或主动断开，正在处理剩余信息'], True)
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            if not task_checkarea.done():
                task_checkarea.cancel()
            await self.close()
            await asyncio.wait(pending)
            printer.info([f'{self._area_id}号弹幕姬退出，剩余任务处理完毕'], True)
        
    async def reconnect(self, room_id):
        print('该监控类型不提供主动切换房间功能')

                                        
class YjMonitorHandler(BaseDanmu):
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
            try:
                msg = self.__reverse(ori)
                if msg is not None:
                    msg_id, type, id = msg
                    if type == '~' and not msg_id % 2:
                        raffle_id = id
                        printer.info([f'{self._area_id}号弹幕监控检测到{"0":^9}的节奏风暴(id: {raffle_id})'], True)
                        raffle_handler.exec_at_once(StormRaffleHandlerTask, 0, raffle_id)
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

    

