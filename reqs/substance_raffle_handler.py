from bili_global import API_LIVE
from json_rsp_ctrl import Ctrl, BaseCtrl, CtrlElem, Equal, In


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
        BaseCtrl(
            logout_verifiers=[CtrlElem(code=-500)],
            ok_verifiers=[
                CtrlElem(code=0),
                CtrlElem(code=-400)
            ]
        ))
        
    join_ctrl = Ctrl(
        BaseCtrl(
            logout_verifiers=[CtrlElem(code=-500)],
            ok_verifiers=[
                CtrlElem(code=0),
                CtrlElem(code=-1),  # 未开始抽奖
                CtrlElem(code=-400),  # 不存在/已经过期
                CtrlElem(code=-3),  # 已抽过
                CtrlElem(code=400, others=[In('msg', '拒绝')])  # 小黑屋
            ]
        ))
