from bili_global import API_LIVE

class TvRaffleHandlerReq:
    @staticmethod
    async def check(user, real_roomid):
        url = f"{API_LIVE}/gift/v3/smalltv/check?roomid={real_roomid}"
        response = await user.bililive_session.request_json('GET', url)
        return response
    
    @staticmethod    
    async def join(user, real_roomid, TV_raffleid):
        url = f"{API_LIVE}/gift/v3/smalltv/join"
        payload = {
            "roomid": real_roomid,
            "raffleId": TV_raffleid,
            "type": "Gift",
            "csrf_token": ''
            }
            
        response = await user.bililive_session.request_json('POST', url, data=payload, headers=user.dict_bili['pcheaders'])
        return response
    
    @staticmethod
    async def notice(user, TV_roomid, TV_raffleid):
        url = f"{API_LIVE}/gift/v3/smalltv/notice?type=small_tv&raffleId={TV_raffleid}"
        response = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return response
        
    
