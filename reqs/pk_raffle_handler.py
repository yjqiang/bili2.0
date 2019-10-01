from bili_global import API_LIVE
from json_rsp_ctrl import ZERO_ONLY_CTRL


class PkRaffleHandlerReq:
    @staticmethod
    async def check(user, real_roomid):
        url = f'{API_LIVE}/xlive/lottery-interface/v1/lottery/Check?roomid={real_roomid}'
        json_rsp = await user.bililive_session.request_json('GET', url, ctrl=ZERO_ONLY_CTRL)
        print('PK', json_rsp)
        return json_rsp

    @staticmethod
    async def join(user, real_roomid, raffle_id):
        url = f"{API_LIVE}/xlive/lottery-interface/v1/pk/join"

        data = {
            'roomid': real_roomid,
            'id': raffle_id,
            'csrf_token': user.dict_bili['csrf'],
            'csrf': user.dict_bili['csrf'],
        }

        response = await user.bililive_session.request_json('POST', url, data=data,
                                                            headers=user.dict_bili['pcheaders'])
        return response
