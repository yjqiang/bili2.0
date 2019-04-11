import random
import asyncio
from operator import itemgetter

from decorator import decorator

import printer
from reqs.utils import UtilsReq
import utils


# 为了解决list打印问题，其实可以实现tasks都这样包裹，但感觉那样过于骚包了
@decorator
async def infos_pure_print_func(func, *args, **kwargs):
    results = func(*args, **kwargs)
    list_results = [i async for i in results]
    user = args[0]
    user.infos(list_results)


class UtilsTask:
    @staticmethod
    async def enter_room(user, room_id):
        if not room_id:
            return
        await user.req_s(UtilsReq.post_watching_history, user, room_id)
    
    @staticmethod
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
                printer.infos([f'抽奖脚本检测到房间{roomid:^9}为异常房间'])
                return False
            else:
                printer.infos([f'抽奖脚本检测到房间{roomid:^9}为正常房间'])
                return True
    
    @staticmethod
    async def get_room_by_area(user, area_id, room_id=None):
        # None/0 都不行
        if room_id is not None and room_id:
            if await UtilsTask.is_ok_as_monitor(user, room_id, area_id):
                printer.infos([f'{area_id}号弹幕监控选择房间（{room_id}）'])
                return room_id
        if area_id == 1:
            room_id = 23058
            if await UtilsTask.is_ok_as_monitor(user, room_id, area_id):
                printer.infos([f'{area_id}号弹幕监控选择房间（{room_id}）'])
                return room_id
                
        while True:
            json_rsp = await user.req_s(UtilsReq.get_rooms_by_area, user, area_id)
            data = json_rsp['data']
            room_id = random.choice(data)['roomid']
            if await UtilsTask.is_ok_as_monitor(user, room_id, area_id):
                printer.infos([f'{area_id}号弹幕监控选择房间（{room_id}）'])
                return room_id
                
    @staticmethod
    async def is_ok_as_monitor(user, room_id, area_id):
        json_response = await user.req_s(UtilsReq.init_room, user, room_id)
        data = json_response['data']
        is_hidden = data['is_hidden']
        is_locked = data['is_locked']
        is_encrypted = data['encrypted']
        is_normal = not any((is_hidden, is_locked, is_encrypted))
                
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
            
    @staticmethod
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
    @infos_pure_print_func
    async def print_giftbags(user):
        gift_bags = await UtilsTask.fetch_giftbags(user)
        yield '查询可用礼物'
        for _, _, gift_num, gift_name, left_days, _ in gift_bags:
            yield f'{gift_name:^3}X{gift_num:^4} (在{left_days:^6}天后过期)'

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
        medal_name = utils.hwid2fwid('勋章名字', 7)
        uname = utils.hwid2fwid('用户名字', 12)
        intimacy = f'{"INTIMACY":^19}'
        today_intimacy = f'{"TODAY_INTIMACY":^14}'
        rank = f'{"RANK":^9}'
        worn_status = utils.hwid2fwid('佩戴状态', 6)
        room_id = f'{"ROOMID":^9}'
        print_queue.append(f'{medal_name} {uname} {intimacy} {today_intimacy} {rank} {worn_status} {room_id}')
        if not json_rsp['code']:
            for medal in json_rsp['data']['fansMedalList']:
                medal_name = utils.hwid2fwid(f'{medal["medal_name"]}|{medal["level"]}', 7)
                uname = utils.hwid2fwid(medal['anchorInfo']['uname'], 12)
                intimacy = f'{medal["intimacy"]:>9}/{medal["next_intimacy"]:<9}'
                today_intimacy = f'{medal["todayFeed"]:>6}/{medal["dayLimit"]:<7}'
                rank = f'{medal["rank"]:^9}'
                org_worn_status = '正在佩戴' if medal['status'] else '目前待机'
                worn_status = utils.hwid2fwid(org_worn_status, 6)
                room_id = f'{medal.get("roomid", "N/A"):^9}'
                print_queue.append(f'{medal_name} {uname} {intimacy} {today_intimacy} {rank} {worn_status} {room_id}')
            user.infos(print_queue)
                        
    @staticmethod
    @infos_pure_print_func
    async def print_bilimain_tasks(user):
        yield '查询用户主站的日常任务情况'
        json_rsp = await user.req_s(UtilsReq.fetch_bilimain_tasks, user)
        data = json_rsp['data']
        if data['login']:
            yield '主站每日登录任务已完成'
        else:
            yield '主站每日登录任务未完成'
        if data['watch_av']:
            yield '主站每日观看视频任务已完成'
        else:
            yield '主站每日观看视频任务未完成'
        yield f'主站每日投币 {data["coins_av"]} (这里乘了10，实际硬币个数为显示数目除以10)'
        if data['share_av']:
            yield '主站每日分享视频任务已完成'
        else:
            yield '主站每日分享视频任务未完成'
            
    @staticmethod
    @infos_pure_print_func
    async def print_livebili_tasks(user):
        yield '查询用户直播分站的日常任务情况'
        json_rsp = await user.req_s(UtilsReq.fetch_livebili_tasks, user)
        # print(json_rsp)
        if not json_rsp['code']:
            data = json_rsp['data']
            yield '双端观看直播:'
            double_watch_info = data['double_watch_info']
            if double_watch_info['status'] == 1:
                yield '# 任务已完成，但未领取奖励'
            elif double_watch_info['status'] == 2:
                yield '# 任务已完成，已经领取奖励'
            else:
                yield '# 该任务未完成'
                if double_watch_info['web_watch'] == 1:
                    yield '# # 网页端观看任务已完成'
                else:
                    yield '# # 网页端观看任务未完成'
                if double_watch_info['mobile_watch'] == 1:
                    yield '# # 移动端观看任务已完成'
                else:
                    yield '# # 移动端观看任务未完成'
    
            yield '直播在线宝箱：'
            box_info = data['box_info']
            if box_info['status'] == 1:
                yield '# 该任务已完成'
            else:
                yield '# 该任务未完成'
                yield f'# # 一共{box_info["max_times"]}次重置次数，当前为第{box_info["freeSilverTimes"]}次第{box_info["type"]}个礼包(每次3个礼包)'
    
            yield '每日签到：'
            sign_info = data['sign_info']
            if sign_info['status'] == 1:
                yield '# 该任务已完成'
            else:
                yield '# 该任务未完成'
            if sign_info['signDaysList'] == list(range(1, sign_info['curDay'] + 1)):
                yield '# 当前全勤'
            else:
                yield '# 出现断签'
    
            yield '直播奖励：'
            live_time_info = data['live_time_info']
            if live_time_info['status'] == 1:
                yield '# 已完成'
            else:
                yield '# 未完成(目前本项目未实现自动完成直播任务)'
            
    # 这个api似乎是不全的，没有硬币这些
    @staticmethod
    @infos_pure_print_func
    async def print_mainbili_userinfo(user):
        yield '查询用户主站的信息'
        json_rsp = await user.req_s(UtilsReq.fetch_bilimain_userinfo, user)
        data = json_rsp['data']
        yield f'用户名 {data["uname"]}'
        yield f'硬币数 {data["coins"]}'
        yield f'Ｂ币数 {data["bCoins"]}'
        level_info = data["level_info"]
        current_exp = level_info['current_exp']
        next_exp = level_info['next_exp']
        # 满级大佬
        if next_exp == -1:
            next_exp = current_exp
        yield f'主站等级值 {level_info["current_level"]}'
        yield f'主站经验值 {current_exp}/{next_exp}'
        yield utils.print_progress(current_exp, next_exp)
        
    @staticmethod
    @infos_pure_print_func
    async def print_livebili_userinfo(user):
        yield '查询用户直播分站的信息'
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
            is_svip = bool(userCoinIfo['svip'])
            svip_time = userCoinIfo['svip_time']
            is_vip = bool(userCoinIfo['vip'])
            vip_time = userCoinIfo['vip_time']
            yield f'用户名 {uname}'
            yield f'手机认证状况 {mobile_verify} | 实名认证状况 {identification}'
            yield f'月费老爷 {str(is_vip):^5} | 过期时间 {vip_time}'
            yield f'年费老爷 {str(is_svip):^5} | 过期时间 {svip_time}'
            yield f'银瓜子 {silver}'
            yield f'通用金瓜子 {gold}'
            yield f'ios可用金瓜子 {gold_ios}'
            yield f'硬币数 {billCoin}'
            yield f'Ｂ币数 {bili_coins}'
            yield f'成就值 {achieve}'
            yield f'等级值 {user_level}———>{user_next_level}'
            yield f'经验值 {user_intimacy}'
            yield f'剩余值 {user_next_intimacy - user_intimacy}'
            yield utils.print_progress(user_intimacy, user_next_intimacy)
            yield f'等级榜 {user_level_rank}'
            
    @staticmethod
    @infos_pure_print_func
    async def print_capsule_info(user):
        yield '查询用户扭蛋的信息'
        json_rsp = await user.req_s(UtilsReq.fetch_capsule_info, user)
        if not json_rsp['code']:
            data = json_rsp['data']
            if data['colorful']['status']:
                yield f'梦幻扭蛋币: {data["colorful"]["coin"]}个'
            else:
                yield '梦幻扭蛋币暂不可用'
            if data['normal']['status']:
                yield f'普通扭蛋币: {data["normal"]["coin"]}个'
            else:
                yield '普通扭蛋币暂不可用'
    
    @staticmethod
    async def open_capsule(user, num_opened):
        if num_opened not in (1, 10, 100):
            print('只能输入1或10或100')
            return
        json_rsp = await user.req_s(UtilsReq.open_capsule, user, num_opened)
        if not json_rsp['code']:
            for i in json_rsp['data']['text']:
                print(i)
                
    @staticmethod
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
            
    @staticmethod
    async def send_danmu(user, msg, room_id):
        json_rsp = await user.req_s(UtilsReq.send_danmu, user, msg, room_id)
        print(json_rsp)

    @staticmethod
    async def uid2name(user, uid):
        json_rsp = await user.req_s(UtilsReq.uid2name, user, uid)
        print('fetch uname', json_rsp)
        assert not json_rsp['code']
        return json_rsp['data'].get('uname')

    @staticmethod
    async def follow_user(user, uid):
        json_rsp = await user.req_s(UtilsReq.follow_user, user, uid)
        print('follow', json_rsp)
        if not json_rsp['code']:
            user.infos([f'用户关注{uid}成功'])
            return True
        user.warn(f'用户关注{uid}失败,{json_rsp}')
        return False

    @staticmethod
    async def unfollow(user, uid):
        while True:
            await user.req_s(UtilsReq.unfollow_user, user, uid)
            await asyncio.sleep(1)
            is_following, _ = await UtilsTask.check_follow(user, uid)
            if not is_following:
                user.infos([f'用户取关{uid}成功'])
                return True
            await asyncio.sleep(0.5)

    @staticmethod
    async def check_follow(user, uid):
        json_rsp = await user.req_s(UtilsReq.check_follow, user, uid)
        assert not json_rsp['code']
        # 0/uid
        is_following = int(json_rsp['data']['mid']) == int(uid)
        # tag none/[list] 不包含默认分组
        tag = json_rsp['data']['tag']
        if tag is None:
            group_ids = []
        else:
            group_ids = tag
        return is_following, group_ids

    @staticmethod
    async def fetch_group_id(user, group_name, read_only=False):
        json_rsp = await user.req_s(UtilsReq.fetch_follow_groupids, user)
        print('查询分组情况', json_rsp)
        assert not json_rsp['code']
        for group in json_rsp['data']:
            if group['name'] == group_name:
                return int(group['tagid'])
        if read_only:
            return None
        print(f'没有名为{group_name}分组, 正在创建新群组')
        json_rsp = await user.req_s(UtilsReq.create_follow_group, user, group_name)
        print('new group', json_rsp)
        return int(json_rsp['data']['tagid'])

    @staticmethod
    async def move2follow_group(user, uid, group_id):
        json_rsp = await user.req_s(UtilsReq.move2follow_group, user, uid, group_id)
        print('move2group', json_rsp)
        return
