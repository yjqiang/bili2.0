from bili_global import API_LIVE
import utils


class TvRaffleHandlerReq:
    @staticmethod
    async def check(user, real_roomid):
        url = f"{API_LIVE}/gift/v3/smalltv/check?roomid={real_roomid}"
        response = await user.bililive_session.request_json('GET', url)
        return response
        
    @staticmethod
    async def join_v4(user, real_roomid, raffle_id, raffle_type):
        url = f"{API_LIVE}/gift/v4/smalltv/getAward"
        temp_params = f'access_key={user.dict_bili["access_key"]}&{user.app_params}&raffleId={raffle_id}&roomid={real_roomid}&ts={utils.curr_time()}&type={raffle_type}'
        sign = user.calc_sign(temp_params)
        payload = f'{temp_params}&sign={sign}'
        json_rsp = await user.bililive_session.request_json('POST', url, params=payload, headers=user.dict_bili['appheaders'])
        return json_rsp
