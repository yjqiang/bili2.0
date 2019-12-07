import base64
from io import BytesIO

try:
    from PIL import Image
except ImportError:
    Image = None
    
import utils


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
    async def fetch_capcha(user):
        url = "https://passport.bilibili.com/captcha"
        binary_rsp = await user.login_session.request_binary('GET', url)
        return binary_rsp

    @staticmethod
    async def login(user, url_name, url_password, captcha=''):
        temp_params = f'actionKey={user.dict_bili["actionKey"]}&appkey={user.dict_bili["appkey"]}&build={user.dict_bili["build"]}&captcha={captcha}&device={user.dict_bili["device"]}&mobi_app={user.dict_bili["mobi_app"]}&password={url_password}&platform={user.dict_bili["platform"]}&username={url_name}'
        sign = user.calc_sign(temp_params)
        payload = f'{temp_params}&sign={sign}'
        url = "https://passport.bilibili.com/api/v3/oauth2/login"
        json_rsp = await user.login_session.request_json('POST', url, params=payload, is_login=True)
        return json_rsp

    @staticmethod
    async def is_token_usable(user):
        list_url = f'access_key={user.dict_bili["access_key"]}&{user.app_params}&ts={utils.curr_time()}'
        list_cookie = user.dict_bili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = user.calc_sign(params)
        true_url = f'https://passport.bilibili.com/api/v2/oauth2/info?{params}&sign={sign}'
        json_rsp = await user.login_session.request_json('GET', true_url, headers=user.dict_bili['appheaders'], is_login=True)
        return json_rsp

    @staticmethod
    async def refresh_token(user):
        list_url = f'access_key={user.dict_bili["access_key"]}&access_token={user.dict_bili["access_key"]}&{user.app_params}&refresh_token={user.dict_bili["refresh_token"]}&ts={utils.curr_time()}'
        list_cookie = user.dict_bili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = user.calc_sign(params)
        payload = f'{params}&sign={sign}'
        # print(payload)
        url = f'https://passport.bilibili.com/api/v2/oauth2/refresh_token'
        json_rsp = await user.login_session.request_json('POST', url, headers=user.dict_bili['appheaders'], params=payload, is_login=True)
        return json_rsp
        
    @staticmethod
    async def cnn_captcha(user, content):
        url = "http://152.32.186.69:19951/captcha/v1"
        str_img = base64.b64encode(content).decode(encoding='utf-8')
        json_rsp = await user.other_session.orig_req_json('POST', url, json={"image": str_img})
        captcha = json_rsp['message']
        print(f"此次登录出现验证码,识别结果为{captcha}")
        return captcha
        
    @staticmethod
    async def input_captcha(_, content):
        if Image is not None:
            img = Image.open(BytesIO(content))
            img.show()
            captcha = input('请手动输入验证码:')
        else:
            captcha = input('您并没有安装pillow模块，但仍然选择了手动输入，那就输呀:')
        return captcha
