import sys
import time
from typing import Optional
from collections import defaultdict
if sys.platform == 'ios':
    import console

        
class BiliLogger():
    # 格式化数据
    @staticmethod
    def format(
            *objects,
            extra_info: Optional[str] = None,
            need_timestamp: bool = True):
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())\
            if need_timestamp else '>'
        extra_info = f' ({extra_info})' if extra_info is not None else ''
        if objects:
            first_value, *others = objects
            others = [f'# {i}' for i in others]
            return (f'{timestamp} {first_value}{extra_info}', *others)
        return f'{timestamp} NULL{extra_info}',

    def infos(
            self,
            list_objects,
            **kwargs):
        self.info(*list_objects, **kwargs)

    def info(
            self,
            *objects,
            extra_info: Optional[str] = None,
            need_timestamp: bool = True):
        texts = self.format(
            *objects,
            extra_info=extra_info,
            need_timestamp=need_timestamp)
        for i in texts:
            print(i)

    def warn(
            self,
            *objects,
            extra_info: Optional[str] = None):
        texts = self.format(
            *objects,
            extra_info=extra_info,
            need_timestamp=True)
        for i in texts:
            print(i, file=sys.stderr)
        
        with open('bili.log', 'a', encoding='utf-8') as f:
            for i in texts:
                f.write(f'{i}\n')

    def debug(
            self,
            *objects,
            **kwargs):
        self.warn(*objects, **kwargs)

    def error(
            self,
            *objects,
            **kwargs):
        self.warn(*objects, **kwargs)
        sys.exit(-1)
    
    
class PythonistaPrinter(BiliLogger):
    def __init__(self):
        self.dic_color = {
            'user-level': defaultdict(list),
            'fans-level': defaultdict(list),
            'others': defaultdict(list)
        }
        self.danmu_control = False
    
    def init_config(self, dic_color, print_control_danmu):
        self.dic_color = dic_color
        self.danmu_control = print_control_danmu
        
    def control_printer(self, danmu_control=None):
        if danmu_control is not None:
            self.danmu_control = danmu_control
            
    # "#969696"
    @staticmethod
    def hex_to_rgb_percent(hex_str):
        return tuple(
            int(n, 16)/255 for n in (hex_str[1:3], hex_str[3:5], hex_str[5:7]))
        
    # 弹幕 礼物 。。。。type
    def print_danmu(self, dic_msg, type='normal'):
        if not self.danmu_control:
            return
        info = dic_msg['info']

        list_msg = []
        list_color = []
        if info[7] == 3:
            # print('舰', end=' ')
            list_msg.append('⚓️ ')
            list_color.append([])
        else:
            if info[2][3] == 1:
                if info[2][4] == 0:
                    list_msg.append('爷 ')
                    list_color.append(self.dic_color['others']['vip'])
                else:
                    list_msg.append('爷 ')
                    list_color.append(self.dic_color['others']['svip'])
            if info[2][2] == 1:
                list_msg.append('房管 ')
                list_color.append(self.dic_color['others']['admin'])
                
            # 勋章
            if info[3]:
                list_color.append(self.dic_color['fans-level'][f'fl{info[3][0]}'])
                list_msg.append(f'{info[3][1]}|{info[3][0]} ')
            # 等级
            if not info[5]:
                list_color.append(self.dic_color['user-level'][f'ul{info[4][0]}'])
                list_msg.append(f'UL{info[4][0]} ')
        try:
            if info[2][7]:
                list_color.append(self.hex_to_rgb_percent(info[2][7]))
                list_msg.append(info[2][1] + ':')
            else:
                list_msg.append(info[2][1] + ':')
                list_color.append(self.dic_color['others']['default_name'])
        except:
            print("# 小电视降临本直播间")
            list_msg.append(info[2][1] + ':')
            list_color.append(self.dic_color['others']['default_name'])
            
        list_msg.append(info[1])
        list_color.append([])
        for i, j in zip(list_msg, list_color):
            console.set_color(*j)
            print(i, end='')
        print()
        console.set_color()

                
class NormalPrinter(BiliLogger):
    def __init__(self):
        self.danmu_control = False
    
    def init_config(self, _, print_control_danmu):
        self.danmu_control = print_control_danmu
        
    def control_printer(self, danmu_control=None):
        if danmu_control is not None:
            self.danmu_control = danmu_control
        
    def print_danmu(self, dic_msg, type='normal'):
        if not self.danmu_control:
            return
        info = dic_msg['info']

        list_msg = []
        if info[7] == 3:
            # print('舰', end=' ')
            list_msg.append('⚓️ ')
        else:
            if info[2][3] == 1:
                if info[2][4] == 0:
                    list_msg.append('爷 ')
                else:
                    list_msg.append('爷 ')
            if info[2][2] == 1:
                list_msg.append('房管 ')
                
            # 勋章
            if info[3]:
                list_msg.append(f'{info[3][1]}|{info[3][0]} ')
            # 等级
            if not info[5]:
                list_msg.append(f'UL{info[4][0]} ')
        try:
            if info[2][7]:
                list_msg.append(info[2][1] + ':')
            else:
                list_msg.append(info[2][1] + ':')
        except:
            print("# 小电视降临本直播间")
            list_msg.append(info[2][1] + ':')
            
        list_msg.append(info[1])
        print(''.join(list_msg))

  
if (sys.platform == 'ios'):
    printer = PythonistaPrinter()
else:
    printer = NormalPrinter()


def init_config(dic_color, print_control_danmu):
    printer.init_config(dic_color, print_control_danmu)

 
def print_danmu(dic_msg, type='normal'):
    printer.print_danmu(dic_msg, type)
    
    
def control_printer(danmu_control=None, debug_control=None):
    printer.control_printer(danmu_control)

            
def info(*objects, **kwargs):
    printer.info(*objects, **kwargs)


def infos(list_objects, **kwargs):
    printer.infos(list_objects, **kwargs)


def warn(*objects, **kwargs):
    printer.warn(*objects, **kwargs)


def error(*objects, **kwargs):
    printer.error(*objects, **kwargs)


def debug(*objects, **kwargs):
    printer.debug(*objects, **kwargs)
