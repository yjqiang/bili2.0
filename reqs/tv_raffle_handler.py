from bili_global import API_LIVE
from json_rsp_ctrl import ZERO_ONLY_CTRL


class TvRaffleHandlerReq:
    @staticmethod
    async def check(user, real_roomid):
        url = f'{API_LIVE}/xlive/lottery-interface/v1/lottery/Check?roomid={real_roomid}'
        '''
        {"code":0,"message":"0","ttl":1,
         "data":{
             "pk":[],
             "guard":[],
             "gift":[{"raffleId":391119,"type":"GIFT_30277","from_user":{"uid":0,"uname":"友人江","face":"***.jpg"},"time_wait":32,"time":92,"max_time":120,"status":1,"sender_type":0,"asset_icon":"***.png","asset_animation_pic":"***.gif","thank_text":"感谢\u003c%友人江%\u003e 赠送的应援喵","weight":0,"gift_id":30277}]
        }}
        '''
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'],
                                                            ctrl=ZERO_ONLY_CTRL)
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
            'csrf_token': user.dict_bili['csrf']
        }
        json_rsp = await user.bililive_session.request_json('POST', url, data=data, headers=user.dict_bili['pcheaders'])
        return json_rsp
