import copy
from PIL import Image
from io import BytesIO
import requests
import base64
from webhub.base_web_hub import BaseWebHub
from webhub.web_session import WebSession


class LoginWebHub(BaseWebHub):
    
    def __init__(self, id, dict_new, dict_bili):
        self.dict_bili = copy.deepcopy(dict_bili)
        self.set_status(dict_new)
        self.user_id = id
        self._login_session = None
        if dict_bili:
            self.app_params = f'actionKey={dict_bili["actionKey"]}&appkey={dict_bili["appkey"]}&build={dict_bili["build"]}&device={dict_bili["device"]}&mobi_app={dict_bili["mobi_app"]}&platform={dict_bili["platform"]}'
        
    def cnn_captcha(self, content):
        img = base64.b64encode(content)
        url = "http://47.95.255.188:5000/code"
        data = {"image": img}
        rsp = requests.post(url, data=data)
        captcha = rsp.text
        print(f'此次登录出现验证码,识别结果为{captcha}')
        return captcha
        
    def input_captcha(self, content):
        img = Image.open(BytesIO(content))
        # img.thumbnail(size)
        img.show()
        captcha = input('手动输入验证码')
        return captcha
        
    @property
    def login_session(self):
        if self._login_session is None:
            self._login_session = WebSession()
            # print(0)
        return self._login_session
        
    async def login_req_json(self, method, url, headers=None, data=None, params=None):
        json_body = await self.login_session.request_json(method, url, headers=headers, data=data, params=params, is_login=True)
        return json_body
                
    async def login_req_binary(self, method, url, headers=None, data=None, params=None):
        binary_body = await self.login_session.request_binary(method, url, headers=headers, data=data, params=params)
        return binary_body
                
    async def logout(self):
        url = 'https://passport.bilibili.com/login?act=exit'
        json_rsp = await self.login_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return json_rsp
        
    async def fetch_key(self):
        url = 'https://passport.bilibili.com/api/oauth2/getKey'
        temp_params = f'appkey={self.dict_bili["appkey"]}'
        sign = self.calc_sign(temp_params)
        params = {'appkey': self.dict_bili['appkey'], 'sign': sign}
        json_rsp = await self.login_req_json('POST', url, data=params)
        return json_rsp

    async def normal_login(self, username, password):
        url = "https://passport.bilibili.com/api/v2/oauth2/login"
        temp_params = f'appkey={self.dict_bili["appkey"]}&password={password}&username={username}'
        sign = self.calc_sign(temp_params)
        payload = f'appkey={self.dict_bili["appkey"]}&password={password}&username={username}&sign={sign}'
        json_rsp = await self.login_req_json('POST', url, params=payload)
        return json_rsp

    async def captcha_login(self, username, password):
        url = "https://passport.bilibili.com/captcha"
        binary_rsp = await self.login_req_binary('GET', url)
        # print(binary_rsp)

        captcha = self.cnn_captcha(binary_rsp)
        temp_params = f'actionKey={self.dict_bili["actionKey"]}&appkey={self.dict_bili["appkey"]}&build={self.dict_bili["build"]}&captcha={captcha}&device={self.dict_bili["device"]}&mobi_app={self.dict_bili["mobi_app"]}&password={password}&platform={self.dict_bili["platform"]}&username={username}'
        sign = self.calc_sign(temp_params)
        payload = f'{temp_params}&sign={sign}'
        url = "https://passport.bilibili.com/api/v2/oauth2/login"
        json_rsp = await self.login_req_json('POST', url, params=payload)
        return json_rsp

    async def check_token(self):
        list_url = f'access_key={self.dict_bili["access_key"]}&{self.app_params}&ts={self.CurrentTime()}'
        list_cookie = self.dict_bili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = self.calc_sign(params)
        true_url = f'https://passport.bilibili.com/api/v2/oauth2/info?{params}&sign={sign}'
        json_rsp = await self.login_req_json('GET', true_url, headers=self.dict_bili['appheaders'])
        return json_rsp

    async def refresh_token(self):
        list_url = f'access_key={self.dict_bili["access_key"]}&access_token={self.dict_bili["access_key"]}&{self.app_params}&refresh_token={self.dict_bili["refresh_token"]}&ts={self.CurrentTime()}'
        list_cookie = self.dict_bili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = self.calc_sign(params)
        payload = f'{params}&sign={sign}'
        # print(payload)
        url = f'https://passport.bilibili.com/api/v2/oauth2/refresh_token'
        json_rsp = await self.login_req_json('POST', url, headers=self.dict_bili['appheaders'], params=payload)
        return json_rsp
