from bili_global import API_LIVE
from json_rsp_ctrl import ZERO_ONLY_CTRL


class TvRaffleHandlerReq:
    @staticmethod
    async def check(user, real_roomid):
        url = f'{API_LIVE}/xlive/lottery-interface/v1/lottery/Check?roomid={real_roomid}'
        json_rsp = await user.bililive_session.request_json('GET', url, ctrl=ZERO_ONLY_CTRL)
        return json_rsp
        
    @staticmethod
    async def join(user, real_roomid, raffle_id, raffle_type):
        url = f"{API_LIVE}/xlive/lottery-interface/v5/smalltv/join"
        '''
        {'code': 0,
         'data': {
             'id': 391309, 'award_id': 1, 'award_type': 0, 'award_num': 1, 'award_image': '***.png', 'award_name': '辣条', 'award_text': '', 'award_ex_time': 1568822400
         }, 'message': '', 'msg': ''}
         
        {'code': -401, 'data': None, 'message': '抽奖还没开始哦, 请耐心等待~', 'msg': '抽奖还没开始哦, 请耐心等待~'}
        
        {'code': -403, 'data': None, 'message': '您已参加抽奖~', 'msg': '您已参加抽奖~'}
        
        {'code': -405, 'data': None, 'message': '奖品都被领完啦！下次下手快点哦~', 'msg': '奖品都被领完啦！下次下手快点哦~'} 
        
        {'code': -403, 'data': None, 'message': '访问被拒绝', 'msg': '访问被拒绝'}
        '''
        data = {
            'id': raffle_id,
            'roomid': real_roomid,
            'type': raffle_type,
            'csrf_token': user.dict_user['csrf']
        }
        json_rsp = await user.bililive_session.request_json('POST', url, data=data, headers=user.pc.headers)
        return json_rsp
