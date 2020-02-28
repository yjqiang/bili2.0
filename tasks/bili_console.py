"""这里面是console控制台使用的一些通用简单命令，更多自定义命令请查看custom.py
"""
from datetime import datetime

import utils
from reqs.utils import UtilsReq
from .utils import UtilsTask
from reqs.main_daily_job import JudgeCaseReq
from .base_class import Console, Wait, Multi


# 为了解决list打印问题，其实可以实现tasks都这样包裹，但感觉那样过于骚包了
def infos_pure_print_func(func):
    async def wrapper(user, *args, **kwargs):
        list_results = [i async for i in func(user, *args, **kwargs)]
        user.info(*list_results)
    return wrapper


class PrintGiftbagsTask(Console, Wait, Multi):
    TASK_NAME = 'null'

    @staticmethod
    async def check(_, user_id):
        return (user_id, None),

    @staticmethod
    @infos_pure_print_func
    async def cmd_console_work(user):
        gift_bags = await UtilsTask.fetch_giftbags(user)
        yield '查询可用礼物'
        for _, _, gift_num, gift_name, left_time in gift_bags:
            left_days = '+∞' if left_time is None else str(round(left_time / 86400, 2))
            yield f'{gift_name:^3}X{gift_num:^4} (在{left_days:^6}天后过期)'


class PrintMedalsTask(Console, Wait, Multi):
    TASK_NAME = 'null'

    @staticmethod
    async def check(_, user_id):
        return (user_id, None),

    # medals_wanted [roomid0, roomid1 …]
    # 这套对齐策略目前不完全对，而且看起来够恶心的
    # 如果对亲密度同样对齐，会导致输出过长
    @staticmethod
    @infos_pure_print_func
    async def cmd_console_work(user):
        json_rsp = await user.req_s(UtilsReq.fetch_medals, user)
        yield '查询勋章信息'
        medal_name = utils.hwid2fwid('勋章名字', 7)
        uname = utils.hwid2fwid('用户名字', 12)
        intimacy = f'{"INTIMACY":^19}'
        today_intimacy = f'{"TODAY_INTIMACY":^14}'
        rank = f'{"RANK":^9}'
        worn_status = utils.hwid2fwid('佩戴状态', 6)
        room_id = f'{"ROOMID":^9}'
        yield f'{medal_name} {uname} {room_id} {intimacy} {today_intimacy} {worn_status} {rank}'
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
                yield f'{medal_name} {uname} {room_id} {intimacy} {today_intimacy} {worn_status} {rank}'


class PrintMainBiliDailyJobTask(Console, Wait, Multi):
    TASK_NAME = 'null'

    @staticmethod
    async def check(_, user_id):
        return (user_id, None),

    @staticmethod
    @infos_pure_print_func
    async def cmd_console_work(user):
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


class PrintLiveBiliDailyJobTask(Console, Wait, Multi):
    TASK_NAME = 'null'

    @staticmethod
    async def check(_, user_id):
        return (user_id, None),

    @staticmethod
    @infos_pure_print_func
    async def cmd_console_work(user):
        yield '查询用户直播分站的日常任务情况'
        json_rsp = await user.req_s(UtilsReq.fetch_livebili_tasks, user)
        json_rsp_sign = await user.req_s(UtilsReq.fetch_livebili_sign_tasks, user)
        if not json_rsp['code'] and not json_rsp_sign['code']:
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
                yield f'# # 一共{box_info["max_times"]}次重置次数，当前为' \
                    f'第{box_info["freeSilverTimes"]}次第{box_info["type"]}个礼包(每次3个礼包)'

            yield '每日签到：'
            sign_info = json_rsp_sign['data']
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


class PrintMainBiliUserInfoTask(Console, Wait, Multi):
    TASK_NAME = 'null'

    @staticmethod
    async def check(_, user_id):
        return (user_id, None),

    # 这个api似乎是不全的，没有硬币这些
    @staticmethod
    @infos_pure_print_func
    async def cmd_console_work(user):
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
        yield f'主站经验值 {utils.print_progress(current_exp, next_exp)}'


class PrintLiveBiliUserInfoTask(Console, Wait, Multi):
    TASK_NAME = 'null'

    @staticmethod
    async def check(_, user_id):
        return (user_id, None),

    @staticmethod
    @infos_pure_print_func
    async def cmd_console_work(user):
        yield '查询用户直播分站的信息'
        json_rsp_pc = await user.req_s(UtilsReq.fetch_livebili_userinfo_pc, user)
        json_rsp_ios = await user.req_s(UtilsReq.fetch_livebili_userinfo_ios, user)
        if not json_rsp_pc['code'] and not json_rsp_ios['code']:
            gold_ios = json_rsp_ios['data']['gold']

            data = json_rsp_pc['data']
            user_info = data['userInfo']
            user_coin_info = data['userCoinIfo']

            uname = user_info['uname']
            achieve = data['achieves']
            user_level = user_coin_info['user_level']
            silver = user_coin_info['silver']
            gold = user_coin_info['gold']
            # identification = bool(user_info['identification'])
            mobile_verify = bool(user_info['mobile_verify'])
            user_next_level = user_coin_info['user_next_level']
            user_intimacy = user_coin_info['user_intimacy']
            user_next_intimacy = user_coin_info['user_next_intimacy']
            user_level_rank = user_coin_info['user_level_rank']
            coins = user_coin_info['coins']
            bili_coins = user_coin_info['bili_coins']

            is_svip = bool(user_coin_info['svip'])
            svip_time = user_coin_info['svip_time']
            is_vip = bool(user_coin_info['vip'])
            vip_time = user_coin_info['vip_time']
            yield f'用户名 {uname}'
            yield f'手机认证状况 {mobile_verify} | 实名认证状况 null'
            yield f'月费老爷 {str(is_vip):^5} | 过期时间 {vip_time}'
            yield f'年费老爷 {str(is_svip):^5} | 过期时间 {svip_time}'
            yield f'银瓜子 {silver}'
            yield f'通用金瓜子 {gold}'
            yield f'iOS可用金瓜子 {gold_ios}'
            yield f'硬币数 {coins}'
            yield f'Ｂ币数 {bili_coins}'
            yield f'成就值 {achieve}'
            yield f'等级值 {user_level}------->{user_next_level}'
            yield f'经验值 {utils.print_progress(user_intimacy, user_next_intimacy)}'
            yield f'等级榜 {user_level_rank}'


class PrintJudgeTask(Console, Wait, Multi):
    TASK_NAME = 'null'

    @staticmethod
    async def check(_, user_id):
        return (user_id, None),

    @staticmethod
    async def cmd_console_work(user):
        json_rsp = await user.req_s(JudgeCaseReq.fetch_judged_cases, user)
        data = json_rsp['data']
        if data is None:
            user.info(f'该用户非风纪委成员')
            return
        today = datetime.today().date()
        sum_cases = 0
        valid_cases = 0
        judging_cases = 0
        for case in data:
            ts = case['voteTime'] / 1000
            vote_day = datetime.fromtimestamp(ts).date()
            if vote_day == today:
                sum_cases += 1
                vote = case['vote']
                if not vote:
                    judging_cases += 1
                elif case['vote'] != 3:
                    valid_cases += 1
        user.info(f'今日投票{sum_cases}（{valid_cases}票有效（非弃权），{judging_cases}票还在进行中）')


class PrintCapsuleTask(Console, Wait, Multi):
    TASK_NAME = 'null'

    @staticmethod
    async def check(_, user_id):
        return (user_id, None),

    @staticmethod
    @infos_pure_print_func
    async def cmd_console_work(user):
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


class OpenCapsuleTask(Console, Wait, Multi):
    TASK_NAME = 'null'

    @staticmethod
    async def check(_, user_id, num_opened):
        return (user_id, None, num_opened),

    @staticmethod
    async def cmd_console_work(user, num_opened):
        await UtilsTask.open_capsule(user, num_opened)


class SendDanmuTask(Console, Wait, Multi):
    TASK_NAME = 'null'

    @staticmethod
    async def check(_, user_id, msg, room_id):
        return (user_id, None, msg, room_id),

    @staticmethod
    async def cmd_console_work(user, msg, room_id):
        await UtilsTask.send_danmu(user, msg, room_id)


class PrintUserStatusTask(Console, Wait, Multi):
    TASK_NAME = 'null'

    @staticmethod
    async def check(_, user_id):
        return (user_id, None),

    @staticmethod
    async def cmd_console_work(user):
        user.print_status()
