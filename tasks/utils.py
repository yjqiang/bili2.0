import random
from operator import itemgetter
import printer
from reqs.utils import UtilsReq
import utils


class UtilsTask:
    @staticmethod
    async def enter_room(user, room_id):
        if not room_id:
            return
        await user.req_s(UtilsReq.post_watching_history, user, room_id)
    
    async def is_normal_room(user, roomid):
        if not roomid:
            return True
        json_response = await user.req_s(UtilsReq.init_room, user, roomid)
        if not json_response['code']:
            data = json_response['data']
            param1 = data['is_hidden']
            param2 = data['is_locked']
            param3 = data['encrypted']
            if any((param1, param2, param3)):
                printer.info([f'抽奖脚本检测到房间{roomid:^9}为异常房间'], True)
                return False
            else:
                printer.info([f'抽奖脚本检测到房间{roomid:^9}为正常房间'], True)
                return True
                
    @staticmethod
    async def check_room_state(user, roomid):
        json_rsp = await user.req_s(UtilsReq.init_room, user, roomid)
        return json_rsp['data']['live_status']
    
    @staticmethod
    async def get_room_by_area(user, areaid):
        # 1 娱乐分区, 2 游戏分区, 3 手游分区, 4 绘画分区
        if areaid == 1:
            roomid = 23058
            state = await UtilsTask.check_room_state(user, roomid)
            if state == 1:
                printer.info([f'{areaid}号弹幕监控选择房间（{roomid}）'], True)
                return roomid
                
        while True:
            json_rsp = await user.req_s(UtilsReq.get_rooms_by_area, user, areaid)
            data = json_rsp['data']
            roomid = random.choice(data)['roomid']
            state = await UtilsTask.check_room_state(user, roomid)
            if state == 1:
                printer.info([f'{areaid}号弹幕监控选择房间（{roomid}）'], True)
                return roomid
                
    @staticmethod
    async def is_ok_as_monitor(user, room_id, area_id):
        json_response = await user.req_s(UtilsReq.init_room, user, room_id)
        data = json_response['data']
        is_hidden = data['is_hidden']
        is_locked = data['is_locked']
        is_encrypted = data['encrypted']
        if any((is_hidden, is_locked, is_encrypted)):
            is_normal = False
        else:
            is_normal = True
                
        json_response = await user.req_s(UtilsReq.get_room_info, user, room_id)
        data = json_response['data']
        is_open = True if data['live_status'] == 1 else False
        current_area_id = data['parent_area_id']
        # print(is_hidden, is_locked, is_encrypted, is_open, current_area_id)
        is_ok = (area_id == current_area_id) and is_normal and is_open
        return is_ok
        
    @staticmethod
    async def send_gift(user, room_id, num_sent, bag_id, gift_id):
        if not num_sent or not room_id:
            return
        json_rsp = await user.req_s(UtilsReq.init_room, user, room_id)
        try:
            ruid = json_rsp['data']['uid']
        except:
            user.warn(f'send_gift {json_rsp}')
        biz_id = json_rsp['data']['room_id']
        # 200027 不足数目
        json_rsp = await user.req_s(UtilsReq.send_gift, user, gift_id, num_sent, bag_id, ruid, biz_id)
        # print(json_rsp)
        if not json_rsp['code']:
            data = json_rsp['data']
            print(f'# 送给房间{room_id:^9}礼物: {data["gift_name"]}X{data["gift_num"]}')
        else:
            print("# 错误", json_rsp['msg'])
            
    async def buy_gift(user, room_id, num_sent, coin_type, gift_id):
        if not num_sent or not room_id:
            return
        json_rsp = await user.req_s(UtilsReq.init_room, user, room_id)
        ruid = json_rsp['data']['uid']
        biz_id = json_rsp['data']['room_id']
        # 200027 不足数目
        json_rsp = await user.req_s(UtilsReq.buy_gift, user, gift_id, num_sent, ruid, biz_id, coin_type)
        if not json_rsp['code']:
            data = json_rsp['data']
            print(f'# 送给房间{room_id:^9}礼物: {data["gift_name"]}X{data["gift_num"]}')
        else:
            print("# 错误", json_rsp['msg'])
            
    @staticmethod
    async def fetch_giftbags(user):
        json_rsp = await user.req_s(UtilsReq.fetch_giftbags, user)
        gift_bags = []
        cur_time = json_rsp['data']['time']
        for gift in json_rsp['data']['list']:
            bag_id = gift['bag_id']
            gift_id = gift['gift_id']
            gift_num = gift['gift_num']
            gift_name = gift['gift_name']
            expire_at = gift['expire_at']
            left_time = expire_at - cur_time
            if not expire_at:
                left_days = '+∞'.center(6)
                left_time = None
            else:
                left_days = round(left_time / 86400, 1)
            gift_bags.append((bag_id, gift_id, gift_num, gift_name, left_days, left_time))
        return gift_bags
        
    @staticmethod
    async def print_giftbags(user):
        gift_bags = await UtilsTask.fetch_giftbags(user)
        user.info(['查询可用礼物:'])
        for _, _, gift_num, gift_name, left_days, _ in gift_bags:
            print(f'# {gift_name:^3}X{gift_num:^4} (在{left_days:^6}天后过期)')

    # medals_wanted [roomid0, roomid1 …]
    @staticmethod
    async def fetch_medals(user, medals_wanted=None):
        json_rsp = await user.req_s(UtilsReq.fetch_medals, user)
        # print(json_rsp)
        medals = []
        if not json_rsp['code']:
            for medal in json_rsp['data']['fansMedalList']:
                # 有的房间封禁了
                if 'roomid' in medal:
                    room_id = medal['roomid']
                    remain_intimacy = int(medal['dayLimit']) - int(medal['todayFeed'])
                    medal_name = medal['medal_name']
                    level = medal['level']
                    medals.append((room_id, remain_intimacy, medal_name, level))
                    
            if medals_wanted is not None:
                results = []
                for room_id in medals_wanted:
                    for medal in medals:
                        if medal[0] == room_id:
                            results.append(medal[:3])
                            break
            else:
                results = [medal[:3] for medal in sorted(medals, key=itemgetter(3), reverse=True)]
            return results
            
    # 这套对齐策略目前不完全对，而且看起来够恶心的
    # 如果对亲密度同样对齐，会导致输出过长
    @staticmethod
    async def print_medals(user):
        json_rsp = await user.req_s(UtilsReq.fetch_medals, user)
        # 打印队列
        print_queue = []
        print_queue.append('查询勋章信息')
        medal_name = utils.adjust_for_chinese('勋章名字', 7)
        uname = utils.adjust_for_chinese('用户名字', 12)
        intimacy = f'{"INTIMACY":^19}'
        today_intimacy = f'{"TODAY_INTIMACY":^14}'
        rank = f'{"RANK":^9}'
        worn_status = utils.adjust_for_chinese('佩戴状态', 6)
        room_id = f'{"ROOMID":^9}'
        print_queue.append(f'{medal_name} {uname} {intimacy} {today_intimacy} {rank} {worn_status} {room_id}')
        if not json_rsp['code']:
            for medal in json_rsp['data']['fansMedalList']:
                medal_name = utils.adjust_for_chinese(f'{medal["medal_name"]}|{medal["level"]}', 7)
                uname = utils.adjust_for_chinese(medal['anchorInfo']['uname'], 12)
                intimacy = f'{medal["intimacy"]:>9}/{medal["next_intimacy"]:<9}'
                today_intimacy = f'{medal["todayFeed"]:>6}/{medal["dayLimit"]:<7}'
                rank = f'{medal["rank"]:^9}'
                org_worn_status = '正在佩戴' if medal['status'] else '目前待机'
                worn_status = utils.adjust_for_chinese(org_worn_status, 6)
                room_id = f'{medal.get("roomid", "N/A"):^9}'
                print_queue.append(f'{medal_name} {uname} {intimacy} {today_intimacy} {rank} {worn_status} {room_id}')
            user.info(print_queue, True)
                        
    @staticmethod
    async def print_bilimain_tasks(user):
        user.info(['查询用户主站的日常任务情况'], True)
        json_rsp = await user.req_s(UtilsReq.fetch_bilimain_tasks, user)
        data = json_rsp['data']
        if data['login']:
            print('# 主站每日登录任务已完成')
        else:
            print('# 主站每日登录任务未完成')
        if data['watch_av']:
            print('# 主站每日观看视频任务已完成')
        else:
            print('# 主站每日观看视频任务未完成')
        print(f'# 主站每日投币 {data["coins_av"]} (这里乘了10，实际硬币个数为显示数目除以10)')
        if data['share_av']:
            print('# 主站每日分享视频任务已完成')
        else:
            print('# 主站每日分享视频任务未完成')
            
    @staticmethod
    async def print_livebili_tasks(user):
        user.info(['查询用户直播分站的日常任务情况'], True)
        json_rsp = await user.req_s(UtilsReq.fetch_livebili_tasks, user)
        # print(json_rsp)
        if not json_rsp['code']:
            data = json_rsp['data']
            print('双端观看直播：')
            double_watch_info = data['double_watch_info']
            if double_watch_info['status'] == 1:
                print('# 该任务已完成，但未领取奖励')
            elif double_watch_info['status'] == 2:
                print('# 该任务已完成，已经领取奖励')
            else:
                print('# 该任务未完成')
                if double_watch_info['web_watch'] == 1:
                    print('## 网页端观看任务已完成')
                else:
                    print('## 网页端观看任务未完成')
                if double_watch_info['mobile_watch'] == 1:
                    print('## 移动端观看任务已完成')
                else:
                    print('## 移动端观看任务未完成')
    
            print('直播在线宝箱：')
            box_info = data['box_info']
            if box_info['status'] == 1:
                print('# 该任务已完成')
            else:
                print('# 该任务未完成')
                print(f'## 一共{box_info["max_times"]}次重置次数，当前为第{box_info["freeSilverTimes"]}次第{box_info["type"]}个礼包(每次3个礼包)')
    
            print('每日签到：')
            sign_info = data['sign_info']
            if sign_info['status'] == 1:
                print('# 该任务已完成')
            else:
                print('# 该任务未完成')
            if sign_info['signDaysList'] == list(range(1, sign_info['curDay'] + 1)):
                print('# 当前全勤')
            else:
                print('# 出现断签')
    
            print('直播奖励：')
            live_time_info = data['live_time_info']
            if live_time_info['status'] == 1:
                print('# 已完成')
            else:
                print('# 未完成(目前本项目未实现自动完成直播任务)')
            
    # 这个api似乎是不全的，没有硬币这些
    @staticmethod
    async def print_mainbili_userinfo(user):
        user.info(['查询用户主站的信息'], True)
        json_rsp = await user.req_s(UtilsReq.fetch_bilimain_userinfo, user)
        data = json_rsp['data']
        print('# 用户名', data['uname'])
        print('# 硬币数', data['coins'])
        print('# b币数', data['bCoins'])
        level_info = data["level_info"]
        current_exp = level_info['current_exp']
        next_exp = level_info['next_exp']
        # 满级大佬
        if next_exp == -1:
            next_exp = current_exp
        print(f'# 主站等级值 {level_info["current_level"]}')
        print(f'# 主站经验值 {current_exp}/{next_exp}')
        utils.print_progress(current_exp, next_exp)
        
    @staticmethod
    async def print_livebili_userinfo(user):
        user.info(['查询用户直播分站的信息'], True)
        json_rsp_pc = await user.req_s(UtilsReq.fetch_livebili_userinfo_pc, user)
        json_rsp_ios = await user.req_s(UtilsReq.fetch_livebili_userinfo_ios, user)
        if not json_rsp_ios['code']:
            gold_ios = json_rsp_ios['data']['gold']
        if not json_rsp_pc['code']:
            data = json_rsp_pc['data']
            userInfo = data['userInfo']
            userCoinIfo = data['userCoinIfo']
            uname = userInfo['uname']
            achieve = data['achieves']
            user_level = userCoinIfo['user_level']
            silver = userCoinIfo['silver']
            gold = userCoinIfo['gold']
            identification = bool(userInfo['identification'])
            mobile_verify = bool(userInfo['mobile_verify'])
            user_next_level = userCoinIfo['user_next_level']
            user_intimacy = userCoinIfo['user_intimacy']
            user_next_intimacy = userCoinIfo['user_next_intimacy']
            user_level_rank = userCoinIfo['user_level_rank']
            billCoin = userCoinIfo['coins']
            bili_coins = userCoinIfo['bili_coins']
            print('# 用户名', uname)
            print(f'# 手机认证状况 {mobile_verify} | 实名认证状况 {identification}')
            print('# 银瓜子', silver)
            print('# 通用金瓜子', gold)
            print('# ios可用金瓜子', gold_ios)
            print('# 硬币数', billCoin)
            print('# b币数', bili_coins)
            print('# 成就值', achieve)
            print('# 等级值', user_level, '———>', user_next_level)
            print('# 经验值', user_intimacy)
            print('# 剩余值', user_next_intimacy - user_intimacy)
            utils.print_progress(user_intimacy, user_next_intimacy)
            print('# 等级榜', user_level_rank)
            
    @staticmethod
    async def print_capsule_info(user):
        user.info(['查询用户扭蛋的信息'], True)
        json_rsp = await user.req_s(UtilsReq.fetch_capsule_info, user)
        if not json_rsp['code']:
            data = json_rsp['data']
            if data['colorful']['status']:
                print(f'梦幻扭蛋币: {data["colorful"]["coin"]}个')
            else:
                print('梦幻扭蛋币暂不可用')
            if data['normal']['status']:
                print(f'普通扭蛋币: {data["normal"]["coin"]}个')
            else:
                print('普通扭蛋币暂不可用')
    
    @staticmethod
    async def open_capsule(user, num_opened):
        if num_opened not in (1, 10, 100):
            print('只能输入1或10或100')
            return
        json_rsp = await user.req_s(UtilsReq.open_capsule, user, num_opened)
        if not json_rsp['code']:
            for i in json_rsp['data']['text']:
                print(i)
                
    async def get_real_roomid(user, room_id):
        json_rsp = await user.req_s(UtilsReq.init_room, user, room_id)
        if not json_rsp['code']:
            print('查询结果:')
            data = json_rsp['data']
            if not data['short_id']:
                print('# 此房间无短房号')
            else:
                print(f'# 短号为:{data["short_id"]}')
            print(f'# 真实房间号为:{data["room_id"]}')
            return data['room_id']
        # 房间不存在
        elif json_rsp['code'] == 60004:
            print(json_rsp['msg'])
            
    async def send_danmu(user, msg, room_id):
        json_rsp = await user.req_s(UtilsReq.send_danmu, user, msg, room_id)
        print(json_rsp)
