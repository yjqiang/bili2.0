import bili_statistics
import printer
import asyncio
import notifier
from cmd import Cmd
import getopt
from tasks.utils import UtilsTask
from tasks.custom import SendLatiaoTask, BuyLatiaoTask
from tasks.main_daily_job import JudgeCaseTask
          
              
class Biliconsole(Cmd):
    prompt = ''
    
    def __init__(self, loop, room_id, printer_danmu):
        self.loop = loop
        self.default_roomid = room_id
        self._printer_danmu = printer_danmu
        super().__init__()
    
    def guide_of_console(self):
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
        
        print('|１１　当前拥有的扭蛋币　　　　　　　|')
        print('|１２　开扭蛋币（一、十、百）　　　　|')
        print('|１３　直播间的长短号码的转化　　　　|')
        print('|１４　发送弹幕　　　　　　　　　　　|')
        print('|１５　切换监听的直播间　　　　　　　|')
        print('|１６　控制弹幕的开关　　　　　　　　|')
        
        print('|２１　赠指定总数的辣条到房间　　　　|')
        print('|２２　银瓜子全部购买辣条并送到房间　|')
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
                if opt_value is not None and opt_value.isdigit():
                    results.append(int(opt_value))
                else:
                    results.append(default_u)
                    # -2是一个灾难性的东西
                    # results.append(-2)
            elif opt_name == '-n':
                if opt_value is not None and opt_value.isdigit():
                    results.append(int(opt_value))
                else:
                    results.append(0)
            elif opt_name == '-p':
                if opt_value is not None and opt_value.isdigit():
                    room_id = int(opt_value)
                else:
                    room_id = self.default_roomid
                if set_roomid:
                    self.default_roomid = room_id
                results.append(self.fetch_real_roomid(room_id))
            else:
                results.append(opt_value)
        return results
                
    def do_1(self, arg):
        id, = self.parse(arg, '-u:')
        self.exec_func_threads(bili_statistics.coroutine_print_statistics, [id])
        
    def do_2(self, arg):
        id, = self.parse(arg, '-u:')
        self.exec_notifier_func_threads(id, UtilsTask.print_giftbags, [])
        
    def do_3(self, arg):
        id, = self.parse(arg, '-u:')
        self.exec_notifier_func_threads(id, UtilsTask.print_medals, [])
        
    def do_4(self, arg):
        id, = self.parse(arg, '-u:')
        self.exec_notifier_func_threads(id, UtilsTask.print_bilimain_tasks, [])
        
    def do_5(self, arg):
        id, = self.parse(arg, '-u:')
        self.exec_notifier_func_threads(id, UtilsTask.print_livebili_tasks, [])
    
    def do_6(self, arg):
        id, = self.parse(arg, '-u:')
        self.exec_notifier_func_threads(id, UtilsTask.print_mainbili_userinfo, [])
        
    def do_7(self, arg):
        id, = self.parse(arg, '-u:')
        self.exec_notifier_func_threads(id, UtilsTask.print_livebili_userinfo, [])
        
    def do_8(self, arg):
        id, = self.parse(arg, '-u:')
        self.exec_notifier_func_threads(id, JudgeCaseTask.print_judge_tasks, [])

    def do_11(self, arg):
        id, = self.parse(arg, '-u:')
        self.exec_notifier_func_threads(id, UtilsTask.print_capsule_info, [])
        
    def do_12(self, arg):
        id, num_opened = self.parse(arg, '-u:-n:')
        self.exec_notifier_func_threads(id, UtilsTask.open_capsule, [num_opened])
        
    def do_13(self, arg):
        real_roomid, = self.parse(arg, '-p:')
        self.exec_notifier_func_threads(-1, UtilsTask.get_real_roomid, [real_roomid])
                
    def do_14(self, arg):
        id, msg, real_roomid = self.parse(arg, '-u:-m:-p:')
        self.exec_notifier_func_threads(id, UtilsTask.send_danmu, [msg, real_roomid])
        
    def do_15(self, arg):
        real_roomid, = self.parse(arg, '-p:', set_roomid=True)
        
        self.exec_func_threads(self._printer_danmu.reset_roomid, [real_roomid])
        
    def do_16(self, arg):
        ctrl, = self.parse(arg, '-c:')
        if ctrl == 'T':
            printer.control_printer(True)
        else:
            printer.control_printer(False)
        
    def do_21(self, arg):
        real_roomid, num_max = self.parse(arg, '-p:-n:')
        self.exec_task_threads(0, SendLatiaoTask, 0, [real_roomid, num_max])
        
    def do_22(self, arg):
        id, real_roomid = self.parse(arg, '-u:-p:')
        self.exec_notifier_func_threads(id, BuyLatiaoTask.clean_latiao, [real_roomid])
            
    def fetch_real_roomid(self, room_id):
        real_roomid = [-1, UtilsTask.get_real_roomid, room_id]
        return real_roomid
        
    # threads指thread safe
    def exec_notifier_func_threads(self, *args):
        asyncio.run_coroutine_threadsafe(self.exec_notifier_func(*args), self.loop)
        
    def exec_func_threads(self, *args):
        asyncio.run_coroutine_threadsafe(self.exec_func(*args), self.loop)
        
    def exec_task_threads(self, *args):
        asyncio.run_coroutine_threadsafe(self.exec_task(*args), self.loop)
        
    # 这里args设置为list
    async def exec_notifier_func(self, id, func, args):
        for i, arg in enumerate(args):
            if isinstance(arg, list):
                args[i] = await notifier.exec_func(*arg)
        await notifier.exec_func(id, func, *args)

    async def exec_func(self, func, args):
        for i, arg in enumerate(args):
            if isinstance(arg, list):
                args[i] = await notifier.exec_func(*arg)
        await func(*args)
        
    async def exec_task(self, id, task, step, args):
        for i, arg in enumerate(args):
            if isinstance(arg, list):
                args[i] = await notifier.exec_func(*arg)
        notifier.exec_task(id, task, step, *args)
        
    
    
    
