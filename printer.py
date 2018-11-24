import sys
import time
if sys.platform == 'ios':
    import console

        
class BasePrinter():
    def init_config(self, dic_color, print_control_danmu):
        self.dic_color = dic_color
        self.danmu_control = print_control_danmu
        
    def control_printer(self, danmu_control=None):
        if danmu_control is not None:
            self.danmu_control = danmu_control
            
    def timestamp(self):
        str_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        return str_time
        
    def info(self, list_msg, tag_time=False):
        if tag_time:
            print(f'[{self.timestamp()}]', end=' ')
        for msg in list_msg:
            print(msg)
            
    def warn(self, msg):
        print(msg, file=sys.stderr)
        with open('bili.log', 'a', encoding='utf-8') as f:
            f.write(f'{self.timestamp()} {msg}\n')
        
    def debug(self, msg):
        # if ConfigLoader().dic_user['print_control']['debug']:
        self.warn(msg)
            
    def error(self, msg):
        self.warn(msg)
        sys.exit(-1)
    
    
class PythonistaPrinter(BasePrinter):
            
    # "#969696"
    def hex_to_rgb_percent(self, hex_str):
        return tuple(int(n, 16)/255 for n in (hex_str[1:3], hex_str[3:5], hex_str[5:7]))
        
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

                
class NormalPrinter(BasePrinter):
        
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


def info(list_msg, tag_time=False):
    printer.info(list_msg, tag_time)


def warn(msg):
    printer.warn(msg)
        
        
def error(msg):
    printer.error(msg)
   
             
def debug(msg):
    printer.debug(msg)
  
      
def print_danmu(dic_msg, type='normal'):
    printer.print_danmu(dic_msg, type)
    
    
def control_printer(danmu_control=None, debug_control=None):
    printer.control_printer(danmu_control)
            
