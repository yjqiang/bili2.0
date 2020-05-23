import base64
from urllib import parse

import requests
    
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
        json_rsp = await user.login_session.request_json('GET', url, headers=user.pc.headers, ctrl=LOGIN_CTRL)
        return json_rsp
        
    @staticmethod
    async def fetch_key(user):
        url = 'https://passport.snm0516.aisee.tv/api/oauth2/getKey'
        params = user.tv_sign()
        json_rsp = await user.login_session.request_json('POST', url, params=params, ctrl=LOGIN_CTRL)
        return json_rsp

    @staticmethod
    async def fetch_capcha(user):
        url = "https://passport.snm0516.aisee.tv/api/captcha?token=5598158bcd8511e1"
        binary_rsp = await user.login_session.request_binary('GET', url, headers=user.tv.headers)
        return binary_rsp

    @staticmethod
    async def login(user, url_name, url_password, captcha=''):
        extra_params = {
            'captcha': captcha,
            'password': url_password,
            'username': url_name,
            'channel': 'master',
            'guid': 'XYEBAA3E54D502E17BD606F0589A356902FCF',
            'token': '5598158bcd8511e1'
        }

        params = user.tv_sign(extra_params)
        url = "https://passport.snm0516.aisee.tv/api/tv/login"

        json_rsp = await user.login_session.request_json('POST', url, headers=user.app.headers, params=params, ctrl=LOGIN_CTRL)
        return json_rsp

    @staticmethod
    async def access_token_2_cookies(user, access_token):
        extra_params = {
            'access_key': access_token,
            'gourl': 'https%3A%2F%2Faccount.bilibili.com%2Faccount%2Fhome',
        }

        params = user.tv_sign(extra_params)
        url = f"https://passport.bilibili.com/api/login/sso"
        rsp = await user.login_session.request('GET', url, allow_redirects=False, params=params, ok_status_codes=(302,))
        return rsp

    @staticmethod
    async def is_token_usable(user):
        dict_cookie = dict()
        for param in user.dict_user['cookie'].split(';'):
            key, value = param.split('=')
            dict_cookie[key] = value

        extra_params = {
            'access_key': user.dict_user['access_key'],
            'access_token': user.dict_user['access_key'],
            'ts': utils.curr_time(),
            ** dict_cookie
        }
        params = user.app_sign(extra_params)
        true_url = f'https://passport.bilibili.com/api/v3/oauth2/info'
        json_rsp = await user.login_session.request_json('GET', true_url, params=params, headers=user.app.headers, ctrl=LOGIN_CTRL)
        return json_rsp

    @staticmethod
    async def refresh_token(user):
        dict_cookie = dict()
        for param in user.dict_user['cookie'].split(';'):
            key, value = param.split('=')
            dict_cookie[key] = value

        extra_params = {
            'access_key': user.dict_user['access_key'],
            'access_token': user.dict_user['access_key'],
            'refresh_token': user.dict_user['refresh_token'],
            'ts': utils.curr_time(),
            ** dict_cookie
        }
        params = user.app_sign(extra_params)
        url = f'https://passport.bilibili.com/api/v2/oauth2/refresh_token'
        json_rsp = await user.login_session.request_json('POST', url, headers=user.app.headers, params=params, ctrl=LOGIN_CTRL)
        print('json_rsp', json_rsp)
        return json_rsp
        
    @staticmethod
    async def cnn_captcha(user, content):
        url = "http://152.32.186.69:19951/captcha/v1"
        str_img = base64.b64encode(content).decode(encoding='utf-8')
        json_rsp = await user.other_session.orig_req_json('POST', url, json={"image": str_img})
        captcha = json_rsp['message']
        print(f"此次登录出现验证码,识别结果为{captcha}")
        return captcha
