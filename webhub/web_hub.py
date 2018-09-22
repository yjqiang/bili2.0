import copy
from webhub.bili_web_hub import BiliWebHub, HostBiliWebHub
from webhub.login_web_hub import LoginWebHub
from webhub.other_web_hub import OtherWebHub




class WebHub(BiliWebHub, LoginWebHub, OtherWebHub):
    def __init__(self, id, dict_new, dict_bili):
        self.dict_bili = copy.deepcopy(dict_bili)
        self.base_url = 'https://api.live.bilibili.com'
        self.set_status(dict_new)
        self.user_id = id
        self.bili_session = None
        self.var_other_session = None
        self.var_login_session = None
        if dict_bili:
            self.app_params = f'actionKey={dict_bili["actionKey"]}&appkey={dict_bili["appkey"]}&build={dict_bili["build"]}&device={dict_bili["device"]}&mobi_app={dict_bili["mobi_app"]}&platform={dict_bili["platform"]}'
        
class HostWebHub(HostBiliWebHub, LoginWebHub, OtherWebHub):
    def __init__(self, id, dict_new, dict_bili, host):
        self.dict_bili = copy.deepcopy(dict_bili)
        self.set_status(dict_new)
        self.user_id = id
        self.bili_session = None
        self.var_other_session = None
        self.var_login_session = None
        if dict_bili:
            self.app_params = f'actionKey={dict_bili["actionKey"]}&appkey={dict_bili["appkey"]}&build={dict_bili["build"]}&device={dict_bili["device"]}&mobi_app={dict_bili["mobi_app"]}&platform={dict_bili["platform"]}'
        self.host = host
        self.base_url = f'http://{self.host.get_host()}'
        self.headers_host = {'host': 'api.live.bilibili.com'}
    
    
                
    
