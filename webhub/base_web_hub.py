import copy
import hashlib
import time
import json
import asyncio
import random


class BaseWebHub():
    def __init__(self, id, dict_new, dict_bili):
        self.dict_bili = copy.deepcopy(dict_bili)
        self.set_status(dict_new)
        self.user_id = id
        if dict_bili:
            self.app_params = f'actionKey={dict_bili["actionKey"]}&appkey={dict_bili["appkey"]}&build={dict_bili["build"]}&device={dict_bili["device"]}&mobi_app={dict_bili["mobi_app"]}&platform={dict_bili["platform"]}'
        
    def set_status(self, dict_new):
        for i, value in dict_new.items():
            self.dict_bili[i] = value
            if i == 'cookie':
                self.dict_bili['pcheaders']['cookie'] = value
                self.dict_bili['appheaders']['cookie'] = value
    
    def print_status(self):
        print(self.dict_bili)
        
    def cookie_existed(self):
        if self.dict_bili['pcheaders']['cookie'] and self.dict_bili['appheaders']['cookie']:
            return True
        return False
        
    def calc_sign(self, str):
        str = f'{str}{self.dict_bili["app_secret"]}'
        hash = hashlib.md5()
        hash.update(str.encode('utf-8'))
        sign = hash.hexdigest()
        return sign
        
    def CurrentTime(self):
        currenttime = int(time.time())
        return str(currenttime)
    
    def randomint(self):
        return ''.join(str(random.randint(0, 9)) for _ in range(17))
        
    async def get_json_rsp(self, rsp, url, is_login=False):
        if rsp.status == 200:
            # json_response = await response.json(content_type=None)
            data = await rsp.read()
            json_rsp = json.loads(data)
            if isinstance(json_rsp, dict) and 'code' in json_rsp:
                code = json_rsp['code']
                if code == 1024:
                    print('b站炸了，暂停所有请求1.5s后重试，请耐心等待')
                    await asyncio.sleep(1.5)
                    return None
                elif code == 3 or code == -401 or code == 1003 or code == -101:
                    print('api提示没有登录')
                    print(json_rsp)
                    if not is_login:
                        return 3
                    else:
                        return json_rsp
            return json_rsp
        elif rsp.status == 403:
            print('403频繁', url)
        return None
        
    async def get_text_rsp(self, rsp, url):
        if rsp.status == 200:
            return await rsp.text()
        elif rsp.status == 403:
            print('403频繁', url)
        return None
