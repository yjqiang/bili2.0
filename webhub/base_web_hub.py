import copy
import hashlib
import time
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
