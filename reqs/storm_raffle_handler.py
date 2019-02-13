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
        temp_params = f'access_key={user.dict_bili["access_key"]}&actionKey={user.dict_bili["actionKey"]}&appkey={user.dict_bili["appkey"]}&build={user.dict_bili["build"]}&device={user.dict_bili["device"]}&id={raffle_id}&mobi_app={user.dict_bili["mobi_app"]}&platform={user.dict_bili["platform"]}&ts={utils.curr_time()}'
        sign = user.calc_sign(temp_params)
        url = f'{API_LIVE}/lottery/v1/Storm/join?{temp_params}&sign={sign}'
        json_rsp = await user.bililive_session.request_json('POST', url, headers=user.dict_bili['appheaders'])
        return json_rsp
