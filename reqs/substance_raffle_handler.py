from bili_global import API_LIVE
from json_rsp_ctrl import JsonRspType, Ctrl, In


class SubstanceRaffleHandlerReq:
    @staticmethod
    async def check(user, aid):
        url = f"{API_LIVE}/lottery/v1/box/getStatus?aid={aid}"
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'], ctrl=ReqCtrl.check_ctrl)
        return json_rsp

    @staticmethod
    async def join(user, aid, number):
        url = f'{API_LIVE}/lottery/v1/box/draw?aid={aid}&number={number}'
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'], ctrl=ReqCtrl.join_ctrl)
        return json_rsp

    @staticmethod
    async def notice(user, aid, number):
        url = f"{API_LIVE}/lottery/v1/box/getWinnerGroupInfo?aid={aid}&number={number}"
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp


class ReqCtrl:
    check_ctrl = Ctrl(
        extend=(
            {'code': -500}, JsonRspType.LOGOUT,
            {'code': 0}, JsonRspType.OK,
            {'code': -400}, JsonRspType.OK,
        )
    )
        
    join_ctrl = Ctrl(
        extend=(
            {'code': -500, 'msg': In('登录')}, JsonRspType.LOGOUT,
            {'code': -500, 'msg': In('非法')}, JsonRspType.OK,
            {'code': 0}, JsonRspType.OK,
            {'code': -1}, JsonRspType.OK,  # 未开始抽奖
            {'code': -400}, JsonRspType.OK,  # 不存在/已经过期
            {'code': -3}, JsonRspType.OK,  # 已抽过
            {'code': 400, 'msg': In('拒绝')}, JsonRspType.OK,  # 小黑屋
        )
    )
