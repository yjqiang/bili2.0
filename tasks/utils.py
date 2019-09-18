import random
import asyncio
from operator import itemgetter

from reqs.utils import UtilsReq
import utils


class UtilsTask:
    @staticmethod
    async def enter_room(user, room_id):
        if not room_id:
            return
        await user.req_s(UtilsReq.post_watching_history, user, room_id)

    @staticmethod
    async def fetch_blive_areas(user):
        json_rsp = await user.req_s(UtilsReq.fetch_blive_areas, user)
        return [int(area['id']) for area in json_rsp['data']]

    @staticmethod
    async def is_normal_room(user, room_id) -> bool:
        if not room_id:
            return True
        json_rsp = await user.req_s(UtilsReq.init_room, user, room_id)
        if not json_rsp['code']:
            data = json_rsp['data']
            return not any((data['is_hidden'], data['is_locked'], data['encrypted']))
        return False

    @staticmethod
    async def get_room_by_area(user, area_id: int):
        if area_id == 1:
            room_id = 23058
            if await UtilsTask.is_ok_as_monitor(user, room_id, area_id):
                return room_id
                
        while True:
            json_rsp = await user.req_s(UtilsReq.get_rooms_by_area, user, area_id)
            list_rooms = json_rsp['data']['list']
            if list_rooms:
                room_id = random.choice(list_rooms)['roomid']
                if await UtilsTask.is_ok_as_monitor(user, room_id, area_id):
                    return room_id
            elif not area_id in await UtilsTask.fetch_blive_areas(user): # 运行过程中某个分区删除
                return None
            await asyncio.sleep(30)
                
    @staticmethod
    async def is_ok_as_monitor(user, room_id, area_id) -> bool:
        if not await UtilsTask.is_normal_room(user, room_id):
            return False

        json_rsp = await user.req_s(UtilsReq.get_room_info, user, room_id)
        if not json_rsp['code']:
            data = json_rsp['data']
            # data['live_status']  # 1/0
            return area_id == data['parent_area_id'] and bool(data['live_status'])
        return False
        
    @staticmethod
    async def send_gift(user, room_id, num_sent, bag_id, gift_id):
        if not num_sent or not room_id:
            return
        json_rsp = await user.req_s(UtilsReq.init_room, user, room_id)
        # TODO FIX
        try:
            ruid = json_rsp['data']['uid']
        except ValueError:
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
        cur_time = utils.curr_time()
        for gift in json_rsp['data']['list']:
            bag_id = gift['bag_id']
            gift_id = gift['gift_id']
            gift_num = gift['gift_num']
            gift_name = gift['gift_name']
            expire_at = gift['expire_at']
            left_time = None if not expire_at else expire_at - cur_time
            gift_bags.append((bag_id, gift_id, gift_num, gift_name, left_time))
        return gift_bags

    # medals_wanted_by_uid [uid0, uid1 …]
    @staticmethod
    async def fetch_medals(user, medals_wanted_by_uid=None):
        json_rsp = await user.req_s(UtilsReq.fetch_medals, user)
        # print(json_rsp)
        if not json_rsp['code']:
            medals = []
            for medal in json_rsp['data']['fansMedalList']:
                # 有的房间封禁了
                if 'roomid' in medal and 'target_id' in medal:
                    room_id = medal['roomid']
                    remain_intimacy = medal['day_limit'] - medal['today_feed']
                    medal_name = medal['medal_name']
                    level = medal['level']
                    uid = medal['target_id']
                    medals.append((room_id, remain_intimacy, medal_name, level, uid))

            if medals_wanted_by_uid is not None:
                results = []
                for uid in medals_wanted_by_uid:
                    for medal in medals:
                        if medal[4] == uid:
                            results.append(medal[:3])
                            break
            else:
                results = [medal[:3] for medal in sorted(medals, key=itemgetter(3), reverse=True)]
            return results
    
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
    async def check_uid_by_roomid(user, room_id):
        json_rsp = await user.req_s(UtilsReq.init_room, user, room_id)
        if not json_rsp['code']:
            uid = json_rsp['data']['uid']
            print(f'房间号{room_id}对应的UID为{uid}')
            return int(uid)
        return None
            
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
            user.info(f'用户关注{uid}成功')
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
                user.info(f'用户取关{uid}成功')
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
