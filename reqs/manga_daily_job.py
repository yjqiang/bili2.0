import utils
from json_rsp_ctrl import Ctrl, JsonRspType, In, BASE_CTRL

MANGA_SIGN_CTRL = Ctrl(
    extend=(
        {'msg': In('uid must > 0')}, JsonRspType.LOGOUT,
    ),
    base=BASE_CTRL,
    default=JsonRspType.OK
)


class MangaSignReq:
    @staticmethod
    async def sign(user):
        url = 'https://manga.bilibili.com/twirp/activity.v1.Activity/ClockIn'
        extra_params = [
            f'access_key={user.dict_bili["access_key"]}',
            f'ts={utils.curr_time()}'
        ]
        params = user.sort_and_sign(extra_params)

        json_rsp = await user.other_session.request_json(
            'POST', url,
            # 不知道为啥必须这么做2333
            headers={**user.dict_bili['appheaders'], 'Content-Type': "application/x-www-form-urlencoded"},
            params=params,
            ctrl=MANGA_SIGN_CTRL, ok_status_codes=(200, 400,)
        )
        return json_rsp


class ShareComicReq:
    @staticmethod
    async def share_comic(user):
        url = f'https://manga.bilibili.com/twirp/activity.v1.Activity/ShareComic'
        extra_params = [
            f'access_key={user.dict_bili["access_key"]}',
            f'ts={utils.curr_time()}'
        ]
        params = user.sort_and_sign(extra_params)

        json_rsp = await user.other_session.request_json(
            'POST',
            url,
            # 不知道为啥必须这么做2333
            headers={**user.dict_bili['appheaders'], 'Content-Type': "application/x-www-form-urlencoded"},
            params=params,
            ok_status_codes=(200, 401,)
        )
        return json_rsp
