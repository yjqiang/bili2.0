from bili_global import API_LIVE
from json_rsp_ctrl import ZERO_ONLY_CTRL


class GuardRaffleHandlerReq:
    @staticmethod
    async def check(user, real_roomid):
        url = f'{API_LIVE}/xlive/lottery-interface/v1/lottery/Check?roomid={real_roomid}'
        '''
        {"code":0,"message":"0","ttl":1,
         "data":{
             "pk":[],
             "guard":[{"id":1388385,"sender":{"uid":12724278,"uname":"洛小倾丶","face":"***.jpg"},"keyword":"guard","privilege_type":2,"time":5281,"status":1,"time_wait":0,"asset_icon":"***.png","asset_animation_pic":"***.gif","thank_text":"恭喜\u003c%洛小倾丶%\u003e上任提督","weight":0},],
             "gift":[]
        }}
        '''
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'],
                                                            ctrl=ZERO_ONLY_CTRL)
        return json_rsp
    
    @staticmethod
    async def join(user, real_roomid, raffle_id):
        url = f"{API_LIVE}/xlive/lottery-interface/v3/guard/join"
        '''
        {"code":0,
         "data":{
             "id":1388393,"award_id":0,"award_type":0,"award_num":1,"award_image":"***.png","award_name":"粉丝勋章亲密度","award_text":"粉丝勋章亲密度+1（当前佩戴）","award_ex_time":0
         },"message":"ok","msg":"ok"}
         
        {'code': 400, 'data': None, 'message': '你已经领取过啦', 'msg': '你已经领取过啦'}
        
        {'code': 400, 'data': None, 'message': '已经过期啦,下次早点吧', 'msg': '已经过期啦,下次早点吧'}
        '''
        data = {
            'roomid': real_roomid,
            'id': raffle_id,
            'type': 'guard',
            'csrf_token': user.dict_bili['csrf']
        }
        json_rsp = await user.bililive_session.request_json('POST', url, data=data, headers=user.dict_bili['pcheaders'])
        return json_rsp
