import hashlib
from typing import Optional


class PcPlatform:
    def __init__(self, pc_headers: dict):
        self.headers = pc_headers

    def update_cookie(self, cookie: str):
        self.headers['cookie'] = cookie


class AppPlatform:
    def __init__(self, app_headers: dict, app_params: dict):
        self.headers = app_headers
        self.params = {
            'actionKey': app_params['actionKey'],
            'appkey': app_params['appkey'],
            'build': app_params['build'],
            'device': app_params['device'],
            'mobi_app': app_params['mobi_app'],
            'platform': app_params['platform'],
        }
        self.app_secret = app_params['app_secret']

    def sign(self, extra_params: Optional[dict] = None) -> dict:
        if extra_params is None:
            dict_params = self.params.copy()
        else:
            dict_params = {**self.params, **extra_params}

        list_params = [f'{key}={value}' for key, value in dict_params.items()]
        list_params.sort()
        text = "&".join(list_params)
        text_with_appsecret = f'{text}{self.app_secret}'
        sign = hashlib.md5(text_with_appsecret.encode('utf-8')).hexdigest()
        dict_params['sign'] = sign
        return dict_params

    def update_cookie(self, cookie: str):
        self.headers['cookie'] = cookie


class TvPlatform:
    def __init__(self, tv_headers: dict, tv_params: dict):
        self.headers = tv_headers
        self.params = {
            'actionKey': tv_params['actionKey'],
            'appkey': tv_params['appkey'],
            'build': tv_params['build'],
            'device': tv_params['device'],
            'mobi_app': tv_params['mobi_app'],
            'platform': tv_params['platform'],
        }
        self.app_secret = tv_params['app_secret']

    def sign(self, extra_params: Optional[dict] = None) -> dict:
        if extra_params is None:
            dict_params = self.params.copy()
        else:
            dict_params = {**self.params, **extra_params}

        list_params = [f'{key}={value}' for key, value in dict_params.items()]
        list_params.sort()
        text = "&".join(list_params)
        text_with_appsecret = f'{text}{self.app_secret}'
        sign = hashlib.md5(text_with_appsecret.encode('utf-8')).hexdigest()
        dict_params['sign'] = sign
        return dict_params

    def update_cookie(self, cookie: str):
        self.headers['cookie'] = cookie
