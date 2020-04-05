# 不具有任何意义,仅仅是常见func

from random import randint

from bili_global import API_LIVE
import utils
from json_rsp_ctrl import ZERO_ONLY_CTRL, LOGOUT_101_CTRL


class UtilsReq:
    @staticmethod
    def randomint():
        return ''.join(str(randint(0, 9)) for _ in range(17))

    @staticmethod
    async def fetch_blive_areas(user):
        url = f'{API_LIVE}/room/v1/Area/getList'
        rsp = await user.bililive_session.request_json('GET', url, ctrl=ZERO_ONLY_CTRL)
        return rsp
        
    @staticmethod
    async def post_watching_history(user, room_id):
        data = {
            "room_id": room_id,
            "csrf_token": user.dict_bili['csrf'],
            "csrf": user.dict_bili['csrf'],
            "platform": "pc",
        }
        url = f"{API_LIVE}/room/v1/Room/room_entry_action"
        response = await user.bililive_session.request_json('POST', url, data=data, headers=user.dict_bili['pcheaders'])
        return response
        
    @staticmethod
    async def init_room(user, roomid):
        url = f"{API_LIVE}/room/v1/Room/room_init?id={roomid}"
        # {"code":60004,"msg":"房间不存在","message":"房间不存在","data":[]}
        # api会抽风
        response = await user.bililive_session.request_json('GET', url, ignore_status_codes = (403,))
        return response
        
    @staticmethod
    async def get_rooms_by_area(user, areaid):
        url = f'{API_LIVE}/room/v3/area/getRoomList?parent_area_id={areaid}&sort_type=online&page_size=10'
        json_rsp = await user.bililive_session.request_json('GET', url, ctrl=ZERO_ONLY_CTRL)
        return json_rsp
        
    @staticmethod
    async def get_room_info(user, roomid):
        url = f"{API_LIVE}/room/v1/Room/get_info?room_id={roomid}"
        # {"code":1,"msg":"未找到该房间","message":"未找到该房间","data":[]}
        json_rsp = await user.bililive_session.request_json('GET', url)
        return json_rsp
    
    @staticmethod
    async def fetch_giftbags(user):
        # {"code":-101,"message":"账号未登录","ttl":1}
        url = f'{API_LIVE}/xlive/web-room/v1/gift/bag_list'
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp
        
    @staticmethod
    async def send_gift(user, gift_id, num_sent, bag_id, ruid, biz_id):
        url = f'{API_LIVE}/gift/v2/live/bag_send'
        data = {
            'uid': user.dict_bili['uid'],
            'gift_id': gift_id,
            'ruid': ruid,
            'gift_num': num_sent,
            'bag_id': bag_id,
            'platform': 'pc',
            'biz_code': 'live',
            'biz_id': biz_id,
            'rnd': utils.curr_time(),
            'storm_beat_id': '0',
            'metadata': '',
            'price': '0',
            'csrf_token': user.dict_bili['csrf']
        }
        json_rsp = await user.bililive_session.request_json('POST', url, headers=user.dict_bili['pcheaders'], data=data)
        return json_rsp
        
    @staticmethod
    async def buy_gift(user, gift_id, num_sent, ruid, biz_id, coin_type):
        url = f'{API_LIVE}/gift/v2/gift/send'
        data = {
            'uid': user.dict_bili['uid'],
            'gift_id': gift_id,
            'ruid': ruid,
            'gift_num': num_sent,
            'coin_type': coin_type,
            'bag_id': 0,
            'platform': 'pc',
            'biz_code': 'live',
            'biz_id': biz_id,
            'rnd': utils.curr_time(),
            'storm_beat_id': '0',
            'metadata': '',
            'price': '0',
            'csrf_token': user.dict_bili['csrf']
        }
        json_rsp = await user.bililive_session.request_json('POST', url, headers=user.dict_bili['pcheaders'], data=data)
        return json_rsp
 
    @staticmethod
    async def fetch_medals(user):
        url = f'{API_LIVE}/i/api/medal?page=1&pageSize=50'  # max 25，所以黑科技一般能用（233）
        # {"code":510001,"msg":"用户不存在","message":"用户不存在","data":[]}
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp
        
    @staticmethod
    async def fetch_bilimain_tasks(user):
        url = 'https://account.bilibili.com/home/reward'
        # {"code":-101}
        json_rsp = await user.other_session.request_json('GET', url, headers=user.dict_bili['pcheaders'], ctrl=LOGOUT_101_CTRL)
        return json_rsp
        
    @staticmethod
    async def fetch_livebili_tasks(user):
        url = f'{API_LIVE}/i/api/taskInfo'
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def fetch_livebili_sign_tasks(user):
        url = f'{API_LIVE}/sign/GetSignInfo'
        # {"code":-101,"message":"账号未登录","ttl":1}
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp
        
    # 有个其他的api，主页那里，但是类似于judge查询那样，json隐藏在text里面，恶心
    @staticmethod
    async def fetch_bilimain_userinfo(user):
        url = 'https://account.bilibili.com/home/userInfo'
        # {"code":-101}
        json_rsp = await user.other_session.request_json('GET', url, headers=user.dict_bili['pcheaders'], ctrl=LOGOUT_101_CTRL)
        return json_rsp
    
    @staticmethod
    async def fetch_livebili_userinfo_pc(user):
        url = f"{API_LIVE}/live_user/v1/UserInfo/live_info"
        # {"code":3,"msg":"请先登录","message":"请先登录","data":[]}
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp
    
    @staticmethod
    async def fetch_livebili_userinfo_ios(user):
        url = f'{API_LIVE}/live_user/v1/UserInfo/my_info?access_key={user.dict_bili["access_key"]}&platform=ios'
        # {"code":3,"msg":"user no login","message":"user no login","data":[]}
        json_rsp = await user.bililive_session.request_json('GET', url)
        return json_rsp
        
    @staticmethod
    async def fetch_capsule_info(user):
        url = f'{API_LIVE}/xlive/web-ucenter/v1/capsule/get_detail?from=web'
        # {"code":-101,"message":"账号未登录","ttl":1}
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def open_capsule(user, num_opened):
        url = f'{API_LIVE}/xlive/web-ucenter/v1/capsule/open_capsule'
        data = {
            'type': 'normal',
            "count": num_opened,
            'csrf_token': user.dict_bili['csrf'],
            'csrf': user.dict_bili['csrf']
        }
        json_rsp = await user.bililive_session.request_json('POST', url, data=data, headers=user.dict_bili['pcheaders'])
        return json_rsp
        
    @staticmethod
    async def send_danmu(user, msg, room_id):
        url = f'{API_LIVE}/msg/send'
        data = {
            'color': '16777215',
            'fontsize': '25',
            'mode': '1',
            'msg': msg,
            'rnd': '0',
            'roomid': int(room_id),
            'csrf_token': user.dict_bili['csrf'],
            'csrf': user.dict_bili['csrf']
        }
        json_rsp = await user.bililive_session.request_json('POST', url, headers=user.dict_bili['pcheaders'], data=data)
        return json_rsp

    @staticmethod
    async def uid2name(user, uid):
        url = f'{API_LIVE}/live_user/v1/card/card_up?uid={uid}'
        json_rsp = await user.bililive_session.request_json('POST', url)
        return json_rsp

    @staticmethod
    async def follow_user(user, uid):
        url = 'https://api.bilibili.com/x/relation/modify'
        payload = {
            'fid': uid,
            'act': 1,
            're_src': 11,
            'jsonp': 'jsonp',
            'csrf': user.dict_bili['csrf']
        }
        json_rsp = await user.other_session.request_json('POST', url, data=payload, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def unfollow_user(user, uid):
        url = 'https://api.bilibili.com/x/relation/modify'
        data = {
            'fid': int(uid),
            'act': 2,
            're_src': 11,
            'jsonp': 'jsonp',
            'csrf': user.dict_bili['csrf']
        }
        json_rsp = await user.other_session.request_json('POST', url, data=data, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def check_follow(user, uid):
        url = f'https://api.bilibili.com/x/relation?fid={uid}'
        json_rsp = await user.other_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def fetch_follow_groupids(user):
        url = 'https://api.bilibili.com/x/relation/tags'
        json_rsp = await user.other_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def create_follow_group(user, name):
        url = 'https://api.bilibili.com/x/relation/tag/create'
        payload = {
            'tag': name,
            'csrf': user.dict_bili['csrf'],
            'jsonp': 'jsonp'
        }
        json_rsp = await user.other_session.request_json('POST', url, data=payload, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def move2follow_group(user, uid, group_id):
        url = 'https://api.bilibili.com/x/relation/tags/addUsers?cross_domain=true'
        headers = {
            **user.dict_bili['pcheaders'],
            'Referer': f'https://space.bilibili.com/{user.dict_bili["uid"]}/'
        }
        payload = {
            'fids': uid,
            'tagids': group_id,
            'csrf': user.dict_bili['csrf']
        }
        json_rsp = await user.other_session.request_json('POST', url, data=payload, headers=headers)
        return json_rsp
