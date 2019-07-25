from bili_global import API_LIVE
import utils
from json_rsp_ctrl import Ctrl, In, JsonRspType


class TvRaffleHandlerReq:
    @staticmethod
    async def check(user, real_roomid):
        url = f"{API_LIVE}/gift/v3/smalltv/check?roomid={real_roomid}"
        response = await user.bililive_session.request_json('GET', url)
        return response
    
    @staticmethod
    async def join(user, real_roomid, raffle_id):
        url = f"{API_LIVE}/gift/v3/smalltv/join"
        payload = {
            "roomid": real_roomid,
            "raffleId": raffle_id,
            "type": "Gift",
            "csrf_token": user.dict_bili['csrf']
            }
            
        response = await user.bililive_session.request_json('POST', url, data=payload, headers=user.dict_bili['pcheaders'])
        return response
        
    @staticmethod
    async def join_v4(user, real_roomid, raffle_id, raffle_type):
        url = f"{API_LIVE}/gift/v4/smalltv/getAward"
        temp_params = f'access_key={user.dict_bili["access_key"]}&{user.app_params}&raffleId={raffle_id}&roomid={real_roomid}&ts={utils.curr_time()}&type={raffle_type}'
        sign = user.calc_sign(temp_params)
        payload = f'{temp_params}&sign={sign}'
        json_rsp = await user.bililive_session.request_json('POST', url, params=payload, headers=user.dict_bili['appheaders'], ctrl=ReqCtrl.join_v4_ctrl)
        return json_rsp
    
    @staticmethod
    async def notice(user, room_id, raffle_id):
        url = f"{API_LIVE}/gift/v3/smalltv/notice?type=small_tv&raffleId={raffle_id}"
        response = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return response

                
class ReqCtrl:
    join_v4_ctrl = Ctrl(
        extend=(
            {'code': -401, 'msg': In('登录')}, JsonRspType.LOGOUT,
            {'code': 0}, JsonRspType.OK,
            {'code': -405}, JsonRspType.OK,  # 奖品都被领完啦
            {'code': -403, 'msg': In('已')}, JsonRspType.OK,  # 'code': -403, 'msg': '您已参加抽奖~'
            {'code': -403, 'msg': In('拒绝')}, JsonRspType.OK,  # 'code': -403, 'msg': '访问被拒绝'
            {'code': -401, 'msg': In('没开始')}, JsonRspType.OK,  # 抽奖还没开始哦
        )
    )
