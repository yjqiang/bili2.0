from bili_global import API_LIVE
import utils
from json_rsp_ctrl import Ctrl, BaseCtrl, CtrlElem, Equal, In, JsonRspType


class TvRaffleHandlerReq:
    @staticmethod
    async def check(user, real_roomid):
        url = f"{API_LIVE}/gift/v3/smalltv/check?roomid={real_roomid}"
        response = await user.bililive_session.request_json('GET', url)
        return response
    
    @staticmethod
    async def join(user, real_roomid, TV_raffleid):
        url = f"{API_LIVE}/gift/v3/smalltv/join"
        payload = {
            "roomid": real_roomid,
            "raffleId": TV_raffleid,
            "type": "Gift",
            "csrf_token": ''
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
    async def notice(user, TV_roomid, TV_raffleid):
        url = f"{API_LIVE}/gift/v3/smalltv/notice?type=small_tv&raffleId={TV_raffleid}"
        response = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return response

                
class ReqCtrl:
    join_v4_ctrl = Ctrl(
        BaseCtrl(
            logout_verifiers=[CtrlElem(code=-401, others=[In('msg', '登录')])],
            ok_verifiers=[
                CtrlElem(code=0),
                CtrlElem(code=-405),  # 奖品都被领完啦
                CtrlElem(code=-403, others=[In('msg', '已')]),  # 'code': -403, 'msg': '您已参加抽奖~'
                CtrlElem(code=-403, others=[In('msg', '拒绝')]),  # 'code': -403, 'msg': '访问被拒绝'
                CtrlElem(code=-401, others=[In('msg', '没开始')])  # 抽奖还没开始哦
            ]))
