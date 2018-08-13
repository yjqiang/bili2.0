
from connect import connect
from printer import Printer
import asyncio
from task import Messenger, Task


def guide_of_console():
    print('___________________________')
    print('| 欢迎使用本控制台           |')
    print('|1 输出本次的抽奖结果统计     |')
    print('|2 查看目前拥有礼物的统计     |')
    print('|3 查看持有勋章状态          |')
    print('|4 获取直播个人的基本信息     |')
    print('|5 检查今日任务的完成情况     |')

    print('|7 模拟电脑网页端发送弹幕     |')
    print('|8 直播间的长短号码的转化     |')
    print('|9  切换监听的直播间         |')
    print('|10 T或F控制弹幕的开关       |')
    print('|11 房间号码查看主播         |')
    # print('|12 当前拥有的扭蛋币         |')
    print('|12 开扭蛋币(只能1，10，100) |')
    print('|14 查看小黑屋的状态         |')
    print('|15 检测参与正常的实物抽奖    |')
    print('￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣')
    

def fetch_real_roomid(roomid):
    if roomid:
        real_roomid = [['check_room', roomid], Task().call_right_now]
    else:
        real_roomid = connect().roomid
    return real_roomid
  
      
def preprocess_send_danmu_msg_web():
    msg = input('请输入要发送的信息:')
    roomid = input('请输入要发送的房间号:')
    real_roomid = fetch_real_roomid(roomid)
    Biliconsole.append2list_console([[msg, real_roomid], 'send_danmu_msg_web'])


def preprocess_check_room():
    roomid = input('请输入要转化的房间号:')
    if not roomid:
        roomid = connect().roomid
    Biliconsole.append2list_console([['check_room', roomid], Task().call_right_now])
    
    
def preprocess_change_danmuji_roomid():
    roomid = input('请输入roomid')
    real_roomid = fetch_real_roomid(roomid)
    Biliconsole.append2list_console([[real_roomid], connect().reconnect])


def change_printer_dic_user():
    new_words = input('弹幕控制')
    if new_words == 'T':
        Printer().print_control_danmu = True
    else:
        Printer().print_control_danmu = False
        
        
def preprocess_fetch_liveuser_info():
    roomid = input('请输入roomid')
    real_roomid = fetch_real_roomid(roomid)
    Biliconsole.append2list_console([['fetch_liveuser_info', real_roomid], Task().call_right_now])

        
def preprocess_open_capsule():
    count = input('请输入要开的扭蛋数目(1或10或100)')
    Biliconsole.append2list_console([[count], 'open_capsule'])


def process_watch_living_video():
    roomid = input('请输入roomid')
    real_roomid = fetch_real_roomid(roomid)
    Biliconsole.append2list_console([['watch_living_video', real_roomid], Task().call_right_now])
    return

        
def preprocess_send_gift():
    roomid = input('请输入roomid')
    real_roomid = fetch_real_roomid(roomid)
    num_wanted = int(input('请输入辣条数目'))
    Biliconsole.append2list_console([[real_roomid, num_wanted], Task().send_latiao])


def return_error():
    print('命令无法识别，请重新输入(提示输入h/help查看详细)')
  
              
class Biliconsole(Messenger):
        
    def controler(self):
        options = {
            '1': 'get_statistic',                  # all # async
            '2': 'fetch_bag_list',                 # all # async
            '3': 'fetch_medal',                    # all # async
            '4': 'fetch_user_info',                # all # async
            '5': 'check_taskinfo',                 # all # async
            '6': 'TitleInfo',                      # all # async
            '7': preprocess_send_danmu_msg_web,  # input async  # str
            '8': preprocess_check_room,          # input async
            '9': preprocess_change_danmuji_roomid,  # input async
            '10': change_printer_dic_user,
            '11': preprocess_fetch_liveuser_info,
            '12': preprocess_open_capsule,
            '13': process_watch_living_video,  # input async
            '14': Task().print_blacklist,
            '15': 'handle_1_room_substant',
            '16': preprocess_send_gift,
            'help': guide_of_console,
            'h': guide_of_console
        }
        while True:
            x = input('')
            if x in ['1', '2', '3', '4', '5', '6']:
                answer = options.get(x, return_error)
                self.append2list_console([[], answer, None])
            elif x == '15':
                answer = options.get(x, return_error)
                self.append2list_console([[], answer, -1])
            else:
                options.get(x, return_error)()
            
    @staticmethod
    def append2list_console(request):
        inst = Biliconsole.instance
        asyncio.run_coroutine_threadsafe(inst.excute_async(request), inst.loop)
        
    async def excute_async(self, i):
        print('00000000000000000000', i)
        i.append(None)
        if isinstance(i, list):
            for j in range(len(i[0])):
                if isinstance(i[0][j], list):
                    print('检测')
                    i[0][j] = await i[0][j][1](*(i[0][j][0]))
            if isinstance(i[1], str):
                await self.notify(i[1], i[0], i[2])
            else:
                await i[1](*i[0])
        else:
            print('qqqqqqqqqqqqqqqq', i)
            await i()
        
        
    
    
    
