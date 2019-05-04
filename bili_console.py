import bili_statistics
import printer
import asyncio
from typing import Optional
import notifier
from cmd import Cmd
import getopt
from tasks.utils import UtilsTask
from tasks.bili_console import (
    PrintGiftbagsTask,
    PrintMedalsTask,
    PrintMainBiliDailyJobTask,
    PrintLiveBiliDailyJobTask,
    PrintMainBiliUserInfoTask,
    PrintLiveBiliUserInfoTask,
    PrintJudgeTask,
    PrintCapsuleTask,
    OpenCapsuleTask,
    SendDanmuTask,
    PrintUserStatusTask
)
from tasks.custom import SendLatiaoTask, BuyLatiaoTask, BuyMedalTask


class FuncCore:
    def __init__(self, function, *args):
        self.function = function
        self.args = args

    async def exec(self):
        args = list(self.args)
        # 递归
        for i, arg in enumerate(args):
            if isinstance(arg, FuncCore):
                args[i] = await arg.exec()
        if asyncio.iscoroutinefunction(self.function):
            return await self.function(*args)
        return self.function(*args)


def convert2int(orig) -> Optional[int]:
    try:
        return int(orig)
    except (ValueError, TypeError):
        return None


class BiliConsole(Cmd):
    prompt = ''
    
    def __init__(self, loop: asyncio.AbstractEventLoop, room_id, printer_danmu):
        self.loop = loop
        self.default_roomid = room_id
        self._printer_danmu = printer_danmu
        super().__init__()
    
    @staticmethod
    def guide_of_console():
        print(' ＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿ ')
        print('|　　　欢迎使用本控制台　　　　　　　|')
        print('|　１　输出本次统计数据　　　　　　　|')
        print('|　２　查看目前拥有礼物的统计　　　　|')
        print('|　３　查看持有勋章状态　　　　　　　|')
        print('|　４　检查主站今日任务的情况　　　　|')
        print('|　５　检查直播分站今日任务的情况　　|')
        print('|　６　获取主站个人的基本信息　　　　|')
        print('|　７　获取直播分站个人的基本信息　　|')
        print('|　８　检查风纪委今日自动投票的情况　|')
        print('|　９　检查脚本判断的用户小黑屋情况　|')
        
        print('|１１　当前拥有的扭蛋币　　　　　　　|')
        print('|１２　开扭蛋币（一、十、百）　　　　|')
        print('|１３　直播间的长短号码的转化　　　　|')
        print('|１４　发送弹幕　　　　　　　　　　　|')
        print('|１５　切换监听的直播间　　　　　　　|')
        print('|１６　控制弹幕的开关　　　　　　　　|')
        
        print('|２１　赠指定总数的辣条到房间　　　　|')
        print('|２２　银瓜子全部购买辣条并送到房间　|')
        print('|２３　购买勋章（使用银瓜子或者硬币）|')
        print(' ￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣ ')
        
    def default(self, line):
        self.guide_of_console()
        
    def emptyline(self):
        self.guide_of_console()
        
    # pattern = '-u:-p:' u(user_id):0,1…;n(num);p(point)指roomid(烂命名因为-r不合适)
    def parse(self, arg, pattern, default_u=0, set_roomid=False):
        args = arg.split()
        try:
            opts, args = getopt.getopt(args, pattern)
        except getopt.GetoptError:
            return []
        dict_results = {opt_name: opt_value for opt_name, opt_value in opts}
        
        opt_names = pattern.split(':')[:-1]
        results = []
        for opt_name in opt_names:
            opt_value = dict_results.get(opt_name)
            if opt_name == '-u':
                int_value = convert2int(opt_value)
                if int_value is not None:
                    results.append(int_value)
                else:
                    results.append(default_u)
                    # -2是一个灾难性的东西
                    # results.append(-2)
            elif opt_name == '-n':
                int_value = convert2int(opt_value)
                if int_value is not None:
                    results.append(int_value)
                else:
                    results.append(0)
            elif opt_name == '-p':
                int_value = convert2int(opt_value)
                if int_value is not None:
                    room_id = int_value
                else:
                    room_id = self.default_roomid
                if set_roomid:
                    self.default_roomid = room_id
                results.append(self.fetch_real_roomid(room_id))
            else:
                results.append(opt_value)
        return results
                
    def do_1(self, arg):
        user_id, = self.parse(arg, '-u:')
        self.exec_func_threads(
            FuncCore(bili_statistics.print_statistics, user_id))
        
    def do_2(self, arg):
        user_id, = self.parse(arg, '-u:')
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintGiftbagsTask, user_id))
        
    def do_3(self, arg):
        user_id, = self.parse(arg, '-u:')
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintMedalsTask, user_id))
        
    def do_4(self, arg):
        user_id, = self.parse(arg, '-u:')
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintMainBiliDailyJobTask, user_id))
        
    def do_5(self, arg):
        user_id, = self.parse(arg, '-u:')
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintLiveBiliDailyJobTask, user_id))
    
    def do_6(self, arg):
        user_id, = self.parse(arg, '-u:')
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintMainBiliUserInfoTask, user_id))
        
    def do_7(self, arg):
        user_id, = self.parse(arg, '-u:')
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintLiveBiliUserInfoTask, user_id))
        
    def do_8(self, arg):
        user_id, = self.parse(arg, '-u:')
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintJudgeTask, user_id))

    def do_9(self, arg):
        user_id, = self.parse(arg, '-u:')
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintUserStatusTask, user_id))

    def do_11(self, arg):
        user_id, = self.parse(arg, '-u:')
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintCapsuleTask, user_id))
        
    def do_12(self, arg):
        user_id, num_opened = self.parse(arg, '-u:-n:')
        self.exec_func_threads(
            FuncCore(notifier.exec_task, OpenCapsuleTask, user_id, num_opened))

    def do_13(self, arg):
        real_roomid, = self.parse(arg, '-p:')
        self.exec_func_threads(
            FuncCore(notifier.exec_func, UtilsTask.get_real_roomid, real_roomid))
                
    def do_14(self, arg):
        user_id, msg, real_roomid = self.parse(arg, '-u:-m:-p:')
        self.exec_func_threads(
            FuncCore(notifier.exec_task, SendDanmuTask, user_id, msg, real_roomid))
        
    def do_15(self, arg):
        real_roomid, = self.parse(arg, '-p:', set_roomid=True)

        self.exec_func_threads(
            FuncCore(self._printer_danmu.reset_roomid, real_roomid))
        
    def do_16(self, arg):
        ctrl, = self.parse(arg, '-c:')
        if ctrl == 'T':
            self.exec_func_threads(
                FuncCore(printer.control_printer, True))
        else:
            self.exec_func_threads(
                FuncCore(printer.control_printer, False))

    def do_21(self, arg):
        real_roomid, num_max = self.parse(arg, '-p:-n:')
        self.exec_func_threads(
            FuncCore(notifier.exec_task, SendLatiaoTask, real_roomid, num_max))
        
    def do_22(self, arg):
        real_roomid, num_wanted = self.parse(arg, '-p:-n:')
        self.exec_func_threads(
            FuncCore(notifier.exec_task, BuyLatiaoTask, real_roomid, num_wanted))
        
    def do_23(self, arg):
        user_id, coin_type, real_roomid = self.parse(arg, '-u:-c:-p:')  # coin_type = 'silver' /  'metal'
        self.exec_func_threads(
            FuncCore(notifier.exec_task, BuyMedalTask, user_id, real_roomid, coin_type))
            
    @staticmethod
    def fetch_real_roomid(room_id):
        return FuncCore(notifier.exec_func, UtilsTask.get_real_roomid, room_id)

    # 直接执行，不需要user_id
    def exec_func_threads(self, func_core: FuncCore):
        asyncio.run_coroutine_threadsafe(self.exec_func(func_core), self.loop)

    @staticmethod
    async def exec_func(func_core: FuncCore):
        await func_core.exec()
