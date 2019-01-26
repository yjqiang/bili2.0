import utils
from bili_global import API_LIVE

class BuyLatiaoReq:
    # 其实与utils部分差不多，怀疑可能是新旧api
    @staticmethod
    async def fetch_livebili_userinfo_pc(user):
        url = f'{API_LIVE}/xlive/web-ucenter/user/get_user_info'
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp
