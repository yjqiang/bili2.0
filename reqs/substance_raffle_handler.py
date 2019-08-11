from bili_global import API_LIVE


class SubstanceRaffleHandlerReq:
    @staticmethod
    async def check(user, aid):
        url = f"{API_LIVE}/lottery/v1/box/getStatus?aid={aid}"
        # {"code":-500,"msg":"未登录","message":"未登录","data":[]}
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def join(user, aid, number):
        url = f'{API_LIVE}/lottery/v1/box/draw?aid={aid}&number={number}'
        # {"code":-500,"msg":"未登录","message":"未登录","data":[]}
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def notice(user, aid, number):
        url = f"{API_LIVE}/lottery/v1/box/getWinnerGroupInfo?aid={aid}&number={number}"
        # {"code":-500,"msg":"未登录","message":"未登录","data":[]}
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp
