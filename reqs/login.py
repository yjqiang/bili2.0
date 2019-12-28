import base64
    
import utils
from json_rsp_ctrl import Ctrl, JsonRspType, In


# 为 login 的相关请求专门设计，在登陆中返回"JsonRspType.LOGOUT"不管的。
# 其余和 BASE_CTRL 一样就行
LOGIN_CTRL = Ctrl(
    extend=(
        {'code': 0}, JsonRspType.OK,  # 目前为止，0 肯定成功，如果例外，自己另写

        {'code': 1024}, JsonRspType.IGNORE,
        {'msg': In('操作太快')}, JsonRspType.IGNORE,
        {'msg': In('系统繁忙')}, JsonRspType.IGNORE,
        {'msg': In('过于频繁')}, JsonRspType.IGNORE,
        {'message': In('服务繁忙')}, JsonRspType.IGNORE,
    ),
    base=None,
    default=JsonRspType.OK
)


class LoginReq:
    @staticmethod
    async def logout(user):
        url = 'https://passport.bilibili.com/login?act=exit'
        json_rsp = await user.login_session.request_json('GET', url, headers=user.dict_bili['pcheaders'], ctrl=LOGIN_CTRL)
        return json_rsp
        
    @staticmethod
    async def fetch_key(user):
        url = 'https://passport.bilibili.com/api/oauth2/getKey'
        params = user.sort_and_sign()
        json_rsp = await user.login_session.request_json('POST', url, params=params, ctrl=LOGIN_CTRL)
        return json_rsp

    @staticmethod
    async def fetch_capcha(user):
        url = "https://passport.bilibili.com/captcha"
        binary_rsp = await user.login_session.request_binary('GET', url, ctrl=LOGIN_CTRL)
        return binary_rsp

    @staticmethod
    async def login(user, url_name, url_password, captcha=''):
        extra_params = [
            f'captcha={captcha}',
            f'password={url_password}',
            f'username={url_name}'

        ]
        params = user.sort_and_sign(extra_params)
        url = "https://passport.bilibili.com/api/v3/oauth2/login"
        json_rsp = await user.login_session.request_json('POST', url, headers=user.dict_bili['appheaders'], params=params, ctrl=LOGIN_CTRL)
        return json_rsp

    @staticmethod
    async def is_token_usable(user):
        list_cookie = user.dict_bili['cookie'].split(';')
        extra_params = [
            f'access_key={user.dict_bili["access_key"]}',
            f'ts={utils.curr_time()}'
        ] + list_cookie
        params = user.sort_and_sign(extra_params)
        true_url = f'https://passport.bilibili.com/api/v3/oauth2/info'
        json_rsp = await user.login_session.request_json('GET', true_url, params=params, headers=user.dict_bili['appheaders'], ctrl=LOGIN_CTRL)
        return json_rsp

    @staticmethod
    async def refresh_token(user):
        list_cookie = user.dict_bili['cookie'].split(';')
        extra_params = [
            f'access_key={user.dict_bili["access_key"]}',
            f'access_token={user.dict_bili["access_key"]}',
            f'refresh_token={user.dict_bili["refresh_token"]}',
            f'ts={utils.curr_time()}'
        ] + list_cookie

        params = user.sort_and_sign(extra_params)
        url = f'https://passport.bilibili.com/api/v2/oauth2/refresh_token'
        json_rsp = await user.login_session.request_json('POST', url, headers=user.dict_bili['appheaders'], params=params, ctrl=LOGIN_CTRL)
        return json_rsp
        
    @staticmethod
    async def cnn_captcha(user, content):
        url = "http://152.32.186.69:19951/captcha/v1"
        str_img = base64.b64encode(content).decode(encoding='utf-8')
        json_rsp = await user.other_session.orig_req_json('POST', url, json={"image": str_img})
        captcha = json_rsp['message']
        print(f"此次登录出现验证码,识别结果为{captcha}")
        return captcha
