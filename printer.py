try:
    import console
except ImportError:
    pass
import webcolors
import time
import codecs


# "#969696"
def hex_to_rgb_percent(hex_str):
    color = webcolors.hex_to_rgb_percent(hex_str)
    # print([float(i.strip('%'))/100.0 for i in color])
    return [float(i.strip('%'))/100.0 for i in color]
 

def level(str):
    if str == "user":
        return 0
    if str == "debug":
        return 1


def timestamp(tag_time):
    if tag_time:
        str_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        print(f'[{str_time}]', end=' ')
        return str_time
    else:
        # print('    ', end='')
        pass


def info(list_msg, tag_time=False):
    timestamp(tag_time)
    for msg in list_msg:
        print(msg)
        

def warn(msg):
    with codecs.open(r'bili.log', 'a', encoding='utf-8') as f:
        f.write(f'{timestamp(True)} {msg}\n')
    print(msg)

        
def error(msg):
    print(msg)
    

class Printer():
    instance = None

    def __new__(cls, dic_color=None, print_control_danmu=None, platform_platform=None):
        if not cls.instance:
            cls.instance = super(Printer, cls).__new__(cls)
            cls.instance.dic_color = dic_color
            cls.instance.platform_platform = platform_platform
            cls.instance.print_control_danmu = print_control_danmu
            if (platform_platform == 'ios_pythonista'):
                cls.instance.danmu_print = cls.instance.concole_print
            else:
                cls.instance.danmu_print = cls.instance.normal_print
        return cls.instance
        
    def concole_print(self, msg, color):
        for i, j in zip(msg, color):
            console.set_color(*j)
            print(i, end='')
        print()
        console.set_color()
            
    def normal_print(self, msg, color):
        print(''.join(msg))
             
    # 弹幕 礼物 。。。。type
    def print_danmu(self, dic_msg, type='normal'):
        if not self.print_control_danmu:
            return
        list_msg, list_color = self.print_danmu_msg(dic_msg)
        self.danmu_print(list_msg, list_color)
    
    def print_danmu_msg(self, dic):
        info = dic['info']
        # tmp = dic['info'][2][1] + ':' + dic['info'][1]
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
                list_color.append(self.dic_color['fans-level']['fl' + str(info[3][0])])
                list_msg.append(info[3][1] + '|' + str(info[3][0]) + ' ')
            # 等级
            if not info[5]:
                list_color.append(self.dic_color['user-level']['ul' + str(info[4][0])])
                list_msg.append('UL' + str(info[4][0]) + ' ')
        try:
            if info[2][7]:
                list_color.append(hex_to_rgb_percent(info[2][7]))
                list_msg.append(info[2][1] + ':')
            else:
                list_msg.append(info[2][1] + ':')
                list_color.append(self.dic_color['others']['default_name'])
            # print(info)
        except:
            print("# 小电视降临本直播间")
            list_msg.append(info[2][1] + ':')
            list_color.append(self.dic_color['others']['default_name'])
            
        list_msg.append(info[1])
        list_color.append([])
        return list_msg, list_color
            

        
        
        



