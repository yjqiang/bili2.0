from bili_global import API_LIVE
import utils
from json_rsp_ctrl import ZERO_ONLY_CTRL


class HeartBeatReq:
    @staticmethod
    async def pc_heartbeat(user):
        url = f'{API_LIVE}/User/userOnlineHeart'
        data = {
            "csrf_token": user.dict_bili['csrf'],
            "csrf": user.dict_bili['csrf']
            }
        json_rsp = await user.bililive_session.request_json('POST', url, data=data, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def app_heartbeat(user):
        temp_params = f'access_key={user.dict_bili["access_key"]}&{user.app_params}&ts={utils.curr_time()}'
        sign = user.calc_sign(temp_params)
        url = f'{API_LIVE}/mobile/userOnlineHeart?{temp_params}&sign={sign}'
        payload = {'roomid': 23058, 'scale': 'xhdpi'}
        json_rsp = await user.bililive_session.request_json('POST', url, data=payload, headers=user.dict_bili['appheaders'])
        return json_rsp

                
class RecvHeartGiftReq:
    @staticmethod
    async def recv_heartgift(user):
        url = f"{API_LIVE}/gift/v2/live/heart_gift_receive?roomid=3&area_v2_id=34"
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp

                
class OpenSilverBoxReq:
    @staticmethod
    async def check_time(user):
        url = f'{API_LIVE}/lottery/v1/SilverBox/getCurrentTask'
        # {"code":0,"msg":"","message":"","data":{"minute":3,"silver":30,"time_start":1566611611,"time_end":1566611791,"times":1,"max_times":3}}
        # {'code': -10017, 'msg': '今天所有的宝箱已经领完!', 'message': '今天所有的宝箱已经领完!', 'data': {'minute': 9, 'silver': 190, 'max_times': 3}}
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp
    
    @staticmethod
    async def open_silver_box(user):
        temp_params = f'access_key={user.dict_bili["access_key"]}&{user.app_params}&ts={utils.curr_time()}'
        # {'code': 0, 'msg': 'ok', 'message': 'ok', 'data': {'silver': '894135', 'awardSilver': 30, 'isEnd': 0}}
        # {'code': -500, 'msg': '领取时间未到, 请稍后再试', 'message': '领取时间未到, 请稍后再试', 'data': {'surplus': 0.98333333333333}}
        # {'code': -903, 'msg': '已经领取过这个宝箱', 'message': '已经领取过这个宝箱', 'data': {'surplus': -8.0166666666667}}
        # {'code': 400, 'msg': '访问被拒绝', 'message': '访问被拒绝', 'data': []}
        sign = user.calc_sign(temp_params)
        url = f'{API_LIVE}/lottery/v1/SilverBox/getAward?{temp_params}&sign={sign}'
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['appheaders'])
        return json_rsp
        

class RecvDailyBagReq:
    @staticmethod
    async def recv_dailybag(user):
        url = f'{API_LIVE}/gift/v2/live/receive_daily_bag'
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp
        
        
class SignReq:
    @staticmethod
    async def sign(user):
        url = f'{API_LIVE}/sign/doSign'
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp
        
        
class WatchTvReq:
    @staticmethod
    async def watch_tv(user):
        url = f'{API_LIVE}/activity/v1/task/receive_award'
        data = {'task_id': 'double_watch_task'}
        json_rsp = await user.bililive_session.request_json('POST', url, data=data, headers=user.dict_bili['appheaders'])
        return json_rsp

                
class SignFansGroupsReq:
    @staticmethod
    async def fetch_groups(user):
        url = "https://api.vc.bilibili.com/link_group/v1/member/my_groups"
        json_rsp = await user.other_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp
    
    @staticmethod
    async def sign_group(user, group_id, owner_uid):
        temp_params = f'access_key={user.dict_bili["access_key"]}&actionKey={user.dict_bili["actionKey"]}&appkey={user.dict_bili["appkey"]}&build={user.dict_bili["build"]}&device={user.dict_bili["device"]}&group_id={group_id}&mobi_app={user.dict_bili["mobi_app"]}&owner_id={owner_uid}&platform={user.dict_bili["platform"]}&ts={utils.curr_time()}'
        sign = user.calc_sign(temp_params)
        url = f'https://api.vc.bilibili.com/link_setting/v1/link_setting/sign_in?{temp_params}&sign={sign}'
        json_rsp = await user.other_session.request_json('GET', url, headers=user.dict_bili['appheaders'])
        return json_rsp
        
        
class SendGiftReq:
    @staticmethod
    async def fetch_gift_config(user):
        url = f'{API_LIVE}/gift/v4/Live/giftConfig'
        json_rsp = await user.bililive_session.request_json('GET', url, ctrl=ZERO_ONLY_CTRL)
        return json_rsp
        
    @staticmethod
    async def fetch_wearing_medal(user):
        url = f'{API_LIVE}/live_user/v1/UserInfo/get_weared_medal'
        data = {
            'uid': user.dict_bili['uid'],
            'csrf_token': user.dict_bili['csrf']
        }
        json_rsp = await user.bililive_session.request_json('POST', url, headers=user.dict_bili['pcheaders'], data=data, ctrl=ZERO_ONLY_CTRL)
        return json_rsp
    
    
class ExchangeSilverCoinReq:
    @staticmethod
    async def silver2coin_web(user):
        url = f'{API_LIVE}/pay/v1/Exchange/silver2coin'
        data = {
            "platform": 'pc',
            "csrf_token": user.dict_bili['csrf']
        }
        json_rsp = await user.bililive_session.request_json('POST', url, headers=user.dict_bili['pcheaders'], data=data)
        return json_rsp
