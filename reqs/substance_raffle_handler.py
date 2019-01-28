from bili_global import API_LIVE


class SubstanceRaffleHandlerReq:
    @staticmethod
    async def check(user, aid):
        url = f"{API_LIVE}/lottery/v1/box/getStatus?aid={aid}"
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def join(user, aid, num):
        url = f'{API_LIVE}/lottery/v1/box/draw?aid={aid}&number={num + 1}'
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp
