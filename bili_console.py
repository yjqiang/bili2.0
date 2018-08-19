
from connect import connect
from printer import Printer
import asyncio
from task import Messenger
from cmd import Cmd


def fetch_real_roomid(roomid):
    if roomid:
        real_roomid = [[roomid], 'check_room', -1]
    else:
        real_roomid = connect().roomid
    return real_roomid
          
              
class Biliconsole(Messenger, Cmd):
    
    def preloop(self):
        Cmd.__init__(self)
        self.prompt = ''
        
    def guide_of_console(self):
        print('___________________________')
        print('| 欢迎使用本控制台           |')
        print('|1 输出本次用户统计          |')
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
        # print('|14 查看小黑屋的状态         |')
        print('|15 检测参与正常的实物抽奖    |')
        print('|16 赠指定总数的辣条到房间    |')
        print('￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣')
        
    def default(self, line):
        self.guide_of_console()
        
    def emptyline(self):
        self.guide_of_console()
                
    def do_1(self, line):
        self.append2list_console([[], 'get_statistic', None])
        
    def do_2(self, line):
        self.append2list_console([[], 'fetch_bag_list', None])
        
    def do_3(self, line):
        self.append2list_console([[], 'fetch_medal', None])
        
    def do_4(self, line):
        self.append2list_console([[], 'fetch_user_info', None])
        
    def do_5(self, line):
        self.append2list_console([[], 'check_taskinfo', None])
    
    def do_6(self, line):
        self.append2list_console([[], 'TitleInfo', None])
        
    def do_7(self, line):
        msg = input('请输入要发送的信息:')
        roomid = input('请输入要发送的房间号:')
        real_roomid = fetch_real_roomid(roomid)
        self.append2list_console([[msg, real_roomid], 'send_danmu_msg_web'])
        
    def do_8(self, line):
        roomid = input('请输入要转化的房间号:')
        if not roomid:
            roomid = connect().roomid
        self.append2list_console([[roomid], 'check_room', -1])
        
    def do_9(self, line):
        roomid = input('请输入roomid')
        real_roomid = fetch_real_roomid(roomid)
        self.append2list_console([[real_roomid], connect().reconnect])
        
    def do_10(self, line):
        new_words = input('弹幕控制')
        if new_words == 'T':
            Printer().print_control_danmu = True
        else:
            Printer().print_control_danmu = False
            
    def do_11(self, line):
        roomid = input('请输入roomid')
        real_roomid = fetch_real_roomid(roomid)
        self.append2list_console([[real_roomid], 'fetch_liveuser_info', -1])

    def do_12(self, line):
        count = input('请输入要开的扭蛋数目(1或10或100)')
        self.append2list_console([[count], 'open_capsule'])
        
    def do_13(self, line):
        roomid = input('请输入roomid')
        real_roomid = fetch_real_roomid(roomid)
        self.append2list_console([[real_roomid], 'watch_living_video', -1])
        
    def do_15(self, line):
        self.append2list_console([[], 'handle_1_room_substant', -1])
        
    def do_16(self, line):
        roomid = input('请输入roomid')
        real_roomid = fetch_real_roomid(roomid)
        num_wanted = int(input('请输入辣条数目'))
        self.append2list_console([[real_roomid, num_wanted], self.send_latiao])
            
    def append2list_console(self, request):
        asyncio.run_coroutine_threadsafe(self.excute_async(request), self.loop)
        
    async def send_latiao(self, room_id, num_wanted):
        i = 0
        while True:
            num_wanted = await self.notify('send_latiao', (room_id, num_wanted), i)
            i += 1
            if num_wanted == 0:
                break
            await asyncio.sleep(1)
        
    async def excute_async(self, i):
        print('bili_console:', i)
        i.append(None)
        if isinstance(i, list):
            for j in range(len(i[0])):
                if isinstance(i[0][j], list):
                    print('检测')
                    # i[0][j] = await i[0][j][1](*(i[0][j][0])
                    i[0][j] = await self.notify(i[0][j][1], i[0][j][0], i[0][j][2])
            if isinstance(i[1], str):
                await self.notify(i[1], i[0], i[2])
            else:
                await i[1](*i[0])
        else:
            print('qqqqqqqqqqqqqqqq', i)
            await i()
        
        
    
    
    
