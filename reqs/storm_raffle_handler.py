import utils
from bili_global import API_LIVE


class StormRaffleHandlerReq:
    @staticmethod
    async def check(user, room_id):
        url = f"{API_LIVE}/lottery/v1/Storm/check?roomid={room_id}"
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def join_deprecated(user, raffle_id):
        url = f'{API_LIVE}/lottery/v1/Storm/join'
        data = {
            "id": raffle_id,
            "color": "16777215",
            "captcha_token": "",
            "captcha_phrase": "",
            "token": "",
            "csrf_token": user.dict_bili['csrf']
        }
        json_rsp = await user.bililive_session.request_json('POST', url, data=data, headers=user.dict_bili['pcheaders'])
        return json_rsp
   
    @staticmethod
    async def join(user, raffle_id):
        extra_params = {
            'access_key': user.dict_bili['access_key'],
            'ts': utils.curr_time(),
            'id': raffle_id,
        }
        params = user.sort_and_sign(extra_params)
        url = f'{API_LIVE}/lottery/v1/Storm/join'
        json_rsp = await user.bililive_session.request_json('POST', url, headers=user.dict_bili['appheaders'], params=params)
        return json_rsp
