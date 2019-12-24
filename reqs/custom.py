import utils
from bili_global import API_LIVE


class BuyLatiaoReq:
    # 其实与utils部分差不多，怀疑可能是新旧api
    @staticmethod
    async def fetch_livebili_userinfo_pc(user):
        url = f'{API_LIVE}/xlive/web-ucenter/user/get_user_info'
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp
        
        
class BuyMedalReq:
    @staticmethod
    async def buy_medal(user, uid, coin_type):
        url = f'https://api.vc.bilibili.com/link_group/v1/member/buy_medal'
        data = {
            'coin_type': coin_type,
            'master_uid': uid,
            'platform': 'android',
            'csrf_token': user.dict_bili['csrf'],
            'csrf': user.dict_bili['csrf']
        }
        json_rsp = await user.other_session.request_json('POST', url, data=data, headers=user.dict_bili['pcheaders'])
        return json_rsp
