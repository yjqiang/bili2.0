from bili_global import API_LIVE


class SubstanceRaffleHandlerReq:
    @staticmethod
    async def check(user, aid):
        url = f"{API_LIVE}/xlive/lottery-interface/v2/Box/getStatus?aid={aid}"
        # {"code":-500,"msg":"未登录","message":"未登录","data":[]}
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.pc.headers)
        return json_rsp

    @staticmethod
    async def join(user, aid, number):
        url = f'{API_LIVE}/xlive/lottery-interface/v2/Box/draw?aid={aid}&number={number}'
        # {"code":-500,"msg":"未登录","message":"未登录","data":[]}
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.pc.headers)
        return json_rsp

    @staticmethod
    async def notice(user, aid, number):
        url = f"{API_LIVE}/xlive/lottery-interface/v2/Box/getWinnerGroupInfo?aid={aid}&number={number}"
        # {"code":-500,"msg":"未登录","message":"未登录","data":[]}
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.pc.headers)
        return json_rsp
