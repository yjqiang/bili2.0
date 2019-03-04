import base64
from PIL import Image
from io import BytesIO
import requests
from .utils import UtilsReq


class LoginReq:
    @staticmethod
    async def logout(user):
        url = 'https://passport.bilibili.com/login?act=exit'
        json_rsp = await user.login_session.request_json('GET', url, headers=user.dict_bili['pcheaders'], is_login=True)
        return json_rsp
        
    @staticmethod
    async def fetch_key(user):
        url = 'https://passport.bilibili.com/api/oauth2/getKey'
        temp_params = f'appkey={user.dict_bili["appkey"]}'
        sign = user.calc_sign(temp_params)
        params = {'appkey': user.dict_bili['appkey'], 'sign': sign}
        json_rsp = await user.login_session.request_json('POST', url, data=params, is_login=True)
        return json_rsp

    @staticmethod
    async def normal_login(user, url_name, url_password):
        url = "https://passport.bilibili.com/api/v2/oauth2/login"
        temp_params = f'appkey={user.dict_bili["appkey"]}&password={url_password}&username={url_name}'
        sign = user.calc_sign(temp_params)
        payload = f'appkey={user.dict_bili["appkey"]}&password={url_password}&username={url_name}&sign={sign}'
        json_rsp = await user.login_session.request_json('POST', url, params=payload, is_login=True)
        return json_rsp

    @staticmethod
    async def captcha_login(user, url_name, url_password):
        url = "https://passport.bilibili.com/captcha"
        binary_rsp = await user.login_session.request_binary('GET', url)

        captcha = LoginReq.cnn_captcha(binary_rsp)
        temp_params = f'actionKey={user.dict_bili["actionKey"]}&appkey={user.dict_bili["appkey"]}&build={user.dict_bili["build"]}&captcha={captcha}&device={user.dict_bili["device"]}&mobi_app={user.dict_bili["mobi_app"]}&password={url_password}&platform={user.dict_bili["platform"]}&username={url_name}'
        sign = user.calc_sign(temp_params)
        payload = f'{temp_params}&sign={sign}'
        url = "https://passport.bilibili.com/api/v2/oauth2/login"
        json_rsp = await user.login_session.request_json('POST', url, params=payload, is_login=True)
        return json_rsp

    @staticmethod
    async def is_token_usable(user):
        list_url = f'access_key={user.dict_bili["access_key"]}&{user.app_params}&ts={UtilsReq.curr_time()}'
        list_cookie = user.dict_bili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = user.calc_sign(params)
        true_url = f'https://passport.bilibili.com/api/v2/oauth2/info?{params}&sign={sign}'
        json_rsp = await user.login_session.request_json('GET', true_url, headers=user.dict_bili['appheaders'], is_login=True)
        return json_rsp

    @staticmethod
    async def refresh_token(user):
        list_url = f'access_key={user.dict_bili["access_key"]}&access_token={user.dict_bili["access_key"]}&{user.app_params}&refresh_token={user.dict_bili["refresh_token"]}&ts={UtilsReq.curr_time()}'
        list_cookie = user.dict_bili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = user.calc_sign(params)
        payload = f'{params}&sign={sign}'
        # print(payload)
        url = f'https://passport.bilibili.com/api/v2/oauth2/refresh_token'
        json_rsp = await user.login_session.request_json('POST', url, headers=user.dict_bili['appheaders'], params=payload, is_login=True)
        return json_rsp
        
    @staticmethod
    def cnn_captcha(content):
        bytes_img = base64.b64encode(content)
        url = "http://115.159.205.242:19951/captcha/v1"
        str_img = str(bytes_img, encoding='utf-8')
        json = {"image": str_img}
        response = requests.post(url, json=json)
        captcha = response.json()['message']
        print(f"此次登录出现验证码,识别结果为{captcha}")
        return captcha
        
    @staticmethod
    def input_captcha(content):
        img = Image.open(BytesIO(content))
        # img.thumbnail(size)
        img.show()
        captcha = input('手动输入验证码')
        return captcha
