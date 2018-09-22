import copy
import sys
from PIL import Image
from io import BytesIO
import requests
import base64
import aiohttp
from webhub.base_web_hub import BaseWebHub


class LoginWebHub(BaseWebHub):
    
    def __init__(self, id, dict_new, dict_bili):
        self.dict_bili = copy.deepcopy(dict_bili)
        self.set_status(dict_new)
        self.user_id = id
        self.var_login_session = None
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
        if self.var_login_session is None:
            self.var_login_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2.5))
            # print(0)
        return self.var_login_session
        
    async def login_session_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.login_session.get(url, headers=headers, data=data, params=params) as response:
                    json_rsp = await self.get_json_rsp(response, url, True)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
                
    async def login_session_post(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.login_session.post(url, headers=headers, data=data, params=params) as response:
                    json_rsp = await self.get_json_rsp(response, url, True)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
                
    async def login_session_get_binary(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.login_session.get(url, headers=headers, data=data, params=params) as response:
                    if response.status == 200:
                        return await response.read()
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
                
    async def logout(self):
        url = 'https://passport.bilibili.com/login?act=exit'
        json_rsp = await self.login_session_get(url, headers=self.dict_bili['pcheaders'])
        return json_rsp
        
    async def fetch_key(self):
        url = 'https://passport.bilibili.com/api/oauth2/getKey'
        temp_params = f'appkey={self.dict_bili["appkey"]}'
        sign = self.calc_sign(temp_params)
        params = {'appkey': self.dict_bili['appkey'], 'sign': sign}
        json_rsp = await self.login_session_post(url, data=params)
        return json_rsp

    async def normal_login(self, username, password):
        url = "https://passport.bilibili.com/api/v2/oauth2/login"
        temp_params = f'appkey={self.dict_bili["appkey"]}&password={password}&username={username}'
        sign = self.calc_sign(temp_params)
        payload = f'appkey={self.dict_bili["appkey"]}&password={password}&username={username}&sign={sign}'
        json_rsp = await self.login_session_post(url, params=payload)
        return json_rsp

    async def captcha_login(self, username, password):
        url = "https://passport.bilibili.com/captcha"
        binary_rsp = await self.login_session_get_binary(url)
        # print(binary_rsp)

        captcha = self.cnn_captcha(binary_rsp)
        temp_params = f'actionKey={self.dict_bili["actionKey"]}&appkey={self.dict_bili["appkey"]}&build={self.dict_bili["build"]}&captcha={captcha}&device={self.dict_bili["device"]}&mobi_app={self.dict_bili["mobi_app"]}&password={password}&platform={self.dict_bili["platform"]}&username={username}'
        sign = self.calc_sign(temp_params)
        payload = f'{temp_params}&sign={sign}'
        url = "https://passport.bilibili.com/api/v2/oauth2/login"
        json_rsp = await self.login_session_post(url, params=payload)
        return json_rsp

    async def check_token(self):
        list_url = f'access_key={self.dict_bili["access_key"]}&{self.app_params}&ts={self.CurrentTime()}'
        list_cookie = self.dict_bili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = self.calc_sign(params)
        true_url = f'https://passport.bilibili.com/api/v2/oauth2/info?{params}&sign={sign}'
        json_rsp = await self.login_session_get(true_url, headers=self.dict_bili['appheaders'])
        return json_rsp

    async def refresh_token(self):
        list_url = f'access_key={self.dict_bili["access_key"]}&access_token={self.dict_bili["access_key"]}&{self.app_params}&refresh_token={self.dict_bili["refresh_token"]}&ts={self.CurrentTime()}'
        list_cookie = self.dict_bili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = self.calc_sign(params)
        payload = f'{params}&sign={sign}'
        # print(payload)
        url = f'https://passport.bilibili.com/api/v2/oauth2/refresh_token'
        json_rsp = await self.login_session_post(url, headers=self.dict_bili['appheaders'], params=payload)
        return json_rsp
