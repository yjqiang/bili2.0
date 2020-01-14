import asyncio
import re
import argparse
from cmd import Cmd
from distutils.util import strtobool

import bili_statistics
import printer
import notifier
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


class ArgumentParserError(Exception):
    pass


class ThrowingArgumentParser(argparse.ArgumentParser):
    # https://github.com/python/cpython/blob/3.7/Lib/argparse.py
    def exit(self, status=0, message=None):
        raise ArgumentParserError(message)

    def error(self, message):
        raise ArgumentParserError(message)


class ConsoleCmd(Cmd):
    PARSE_RE = re.compile(r'(--\w{2,})/(-[A-Za-z]) {(int|str|bool|room_id)(?:\?(\S*|%\S+))?}')
    prompt = ''
    
    def __init__(self, loop: asyncio.AbstractEventLoop, room_id, printer_danmu):
        self.loop = loop
        self.default_roomid = room_id
        self._printer_danmu = printer_danmu

        # || 用于分割，其中首个是标号，后面是全是一个个参数
        # 参数格式是"--长指令/-短指令 {参数类型?默认值}"，其中默认值可以省略
        self.__parser_1 = self.compile_parser('1 || --user_id/-u {int?0}')
        self.__parser_2 = self.compile_parser('2 || --user_id/-u {int?0}')
        self.__parser_3 = self.compile_parser('3 || --user_id/-u {int?0}')
        self.__parser_4 = self.compile_parser('4 || --user_id/-u {int?0}')
        self.__parser_5 = self.compile_parser('5 || --user_id/-u {int?0}')
        self.__parser_6 = self.compile_parser('6 || --user_id/-u {int?0}')
        self.__parser_7 = self.compile_parser('7 || --user_id/-u {int?0}')
        self.__parser_8 = self.compile_parser('8 || --user_id/-u {int?0}')
        self.__parser_9 = self.compile_parser('9 || --user_id/-u {int?0}')

        self.__parser_11 = self.compile_parser('11 || --user_id/-u {int?0}')
        self.__parser_12 = self.compile_parser('12 || --user_id/-u {int?0} || --num/-n {int}')
        self.__parser_13 = self.compile_parser('13 || --room_id/-p {room_id?%default_roomid}')
        self.__parser_14 = self.compile_parser('14 || --user_id/-u {int?0} || --msg/-m {str}'
                                               ' || --room_id/-p {room_id?%default_roomid}')
        self.__parser_15 = self.compile_parser('15 || --room_id/-p {room_id?%default_roomid}')
        self.__parser_16 = self.compile_parser('16 || --ctrl/-c {bool}')

        self.__parser_21 = self.compile_parser('21 || --room_id/-p {room_id?%default_roomid}'
                                               ' || --num/-n {int}')
        self.__parser_22 = self.compile_parser('22 || --room_id/-p {room_id?%default_roomid}'
                                               ' || --num/-n {int}')
        self.__parser_23 = self.compile_parser('23 || --user_id/-u {int?0} || --coin_type/-c {str}'
                                               ' || --room_id/-p {room_id?%default_roomid}')

        super().__init__()

    def compile_parser(self, text: str) -> ThrowingArgumentParser:
        entries = [entry.strip() for entry in text.split('||')]
        result = ThrowingArgumentParser(prog=entries[0], add_help=False)
        for entry in entries[1:]:
            long_ctrl, short_ctrl, str_value_type, default = self.PARSE_RE.fullmatch(entry).groups()
            # print(f'{long_ctrl}, {short_ctrl}, {str_value_type}, {default}')
            if default is None:
                required = True
                help_msg = f'(必填: 类型 {str_value_type})'
            else:
                required = False
                help_msg = f'(可缺: 类型 {str_value_type} 默认 %(default)s)'

            if str_value_type == 'int':
                convert = self.str2int
            elif str_value_type == 'bool':
                convert = self.str2bool
            elif str_value_type == 'room_id':
                convert = self.str2room_id
            else:  # 其他的忽略，全部为str
                convert = str
            result.add_argument(long_ctrl, short_ctrl, required=required, help=help_msg, default=default, type=convert)
        return result

    @staticmethod
    def parse(arg: str, parser: ThrowingArgumentParser):
        try:
            result = parser.parse_args(arg.split())
            # print('parse_result', result, parser)
            return tuple(vars(result).values())
        except ArgumentParserError as e:
            print('解析错误', e)
            parser.print_help()
            raise

    @staticmethod
    def str2int(orig: str) -> int:
        return int(orig)

    @staticmethod
    def str2bool(orig: str) -> bool:
        return bool(strtobool(orig))

    def str2room_id(self, orig: str) -> FuncCore:
        if orig == '%default_roomid':
            return self.fetch_real_roomid(self.default_roomid)
        return self.fetch_real_roomid(self.str2int(orig))
    
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

    def onecmd(self, *args, **kwargs):
        try:
            return super().onecmd(*args, **kwargs)
        except ArgumentParserError:
            # print('test_onecmd', args, kwargs)
            pass

    def postcmd(self, stop, line):
        # print('test_post_cmd', stop, line)
        if line == 'EOF':
            return True
        # 永远不退出
        return None
                
    def do_1(self, arg):
        user_id, = self.parse(arg, self.__parser_1)
        self.exec_func_threads(
            FuncCore(bili_statistics.print_statistics, user_id))
        
    def do_2(self, arg):
        user_id, = self.parse(arg, self.__parser_2)
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintGiftbagsTask, 'cmd', user_id))
        
    def do_3(self, arg):
        user_id, = self.parse(arg, self.__parser_3)
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintMedalsTask, 'cmd', user_id))
        
    def do_4(self, arg):
        user_id, = self.parse(arg, self.__parser_4)
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintMainBiliDailyJobTask, 'cmd', user_id))
        
    def do_5(self, arg):
        user_id, = self.parse(arg, self.__parser_5)
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintLiveBiliDailyJobTask, 'cmd', user_id))
    
    def do_6(self, arg):
        user_id, = self.parse(arg, self.__parser_6)
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintMainBiliUserInfoTask, 'cmd', user_id))
        
    def do_7(self, arg):
        user_id, = self.parse(arg, self.__parser_7)
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintLiveBiliUserInfoTask, 'cmd', user_id))
        
    def do_8(self, arg):
        user_id, = self.parse(arg, self.__parser_8)
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintJudgeTask, 'cmd', user_id))

    def do_9(self, arg):
        user_id, = self.parse(arg, self.__parser_9)
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintUserStatusTask, 'cmd', user_id))

    def do_11(self, arg):
        user_id, = self.parse(arg, self.__parser_11)
        self.exec_func_threads(
            FuncCore(notifier.exec_task, PrintCapsuleTask, 'cmd', user_id))
        
    def do_12(self, arg):
        user_id, num_opened = self.parse(arg, self.__parser_12)
        self.exec_func_threads(
            FuncCore(notifier.exec_task, OpenCapsuleTask, 'cmd', user_id, num_opened))

    def do_13(self, arg):
        real_roomid, = self.parse(arg, self.__parser_13)
        self.exec_func_threads(
            FuncCore(notifier.exec_func, UtilsTask.get_real_roomid, real_roomid))
                
    def do_14(self, arg):
        user_id, msg, real_roomid = self.parse(arg, self.__parser_14)
        self.exec_func_threads(
            FuncCore(notifier.exec_task, SendDanmuTask, 'cmd', user_id, msg, real_roomid))
        
    def do_15(self, arg):
        real_roomid, = self.parse(arg, self.__parser_15)
        self.default_roomid = real_roomid

        self.exec_func_threads(
            FuncCore(self._printer_danmu.reset_roomid, real_roomid))
        
    def do_16(self, arg):
        ctrl, = self.parse(arg, self.__parser_16)
        self.exec_func_threads(
            FuncCore(printer.control_printer, ctrl))

    def do_21(self, arg):
        real_roomid, num_max = self.parse(arg, self.__parser_21)
        self.exec_func_threads(
            FuncCore(notifier.exec_task, SendLatiaoTask, 'cmd', real_roomid, num_max))
        
    def do_22(self, arg):
        real_roomid, num_wanted = self.parse(arg, self.__parser_22)
        self.exec_func_threads(
            FuncCore(notifier.exec_task, BuyLatiaoTask, 'cmd', real_roomid, num_wanted))
        
    def do_23(self, arg):
        user_id, coin_type, real_roomid = self.parse(arg, self.__parser_23)  # coin_type = 'silver' /  'metal'
        self.exec_func_threads(
            FuncCore(notifier.exec_task, BuyMedalTask, 'cmd', user_id, real_roomid, coin_type))
            
    @staticmethod
    def fetch_real_roomid(room_id):
        return FuncCore(notifier.exec_func, UtilsTask.get_real_roomid, room_id)

    # 直接执行，不需要user_id
    def exec_func_threads(self, func_core: FuncCore):
        asyncio.run_coroutine_threadsafe(self.exec_func(func_core), self.loop)

    @staticmethod
    async def exec_func(func_core: FuncCore):
        await func_core.exec()
