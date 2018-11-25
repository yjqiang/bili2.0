import copy
from webhub.base_web_hub import BaseWebHub
from webhub.web_session import WebSession


class OtherWebHub(BaseWebHub):
    
    def __init__(self, id, dict_new, dict_bili):
        self.dict_bili = copy.deepcopy(dict_bili)
        self.set_status(dict_new)
        self.user_id = id
        self._other_session = None
        if dict_bili:
            self.app_params = f'actionKey={dict_bili["actionKey"]}&appkey={dict_bili["appkey"]}&build={dict_bili["build"]}&device={dict_bili["device"]}&mobi_app={dict_bili["mobi_app"]}&platform={dict_bili["platform"]}'
            
    @property
    def other_session(self):
        if self._other_session is None:
            self._other_session = WebSession()
            # print(0)
        return self._other_session
        
    async def other_req_json(self, method, url, headers=None, data=None, params=None):
        json_body = await self.other_session.request_json(method, url, headers=headers, data=data, params=params)
        return json_body
                
    async def other_req_text(self, method, url, headers=None, data=None, params=None):
        text_body = await self.other_session.request_text(method, url, headers=headers, data=data, params=params)
        return text_body
        
    async def other_req_binary(self, method, url, headers=None, data=None, params=None):
        binary_body = await self.other_session.request_binary(method, url, headers=headers, data=data, params=params)
        return binary_body
                
    async def search_liveuser(self, name):
        search_url = f'https://search.bilibili.com/api/search?search_type=live_user&keyword={name}&page=1'
        json_rsp = await self.other_req_json('GET', search_url)
        return json_rsp

    async def search_biliuser(self, name):
        search_url = f"https://search.bilibili.com/api/search?search_type=bili_user&keyword={name}"
        json_rsp = await self.other_req_json('GET', search_url)
        return json_rsp
        
    async def load_img(self, url):
        return await self.other_req_binary('GET', url)
        
    async def get_grouplist(self):
        url = "https://api.vc.bilibili.com/link_group/v1/member/my_groups"
        json_rsp = await self.other_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return json_rsp
    
    async def assign_group(self, i1, i2):
        temp_params = f'access_key={self.dict_bili["access_key"]}&actionKey={self.dict_bili["actionKey"]}&appkey={self.dict_bili["appkey"]}&build={self.dict_bili["build"]}&device={self.dict_bili["device"]}&group_id={i1}&mobi_app={self.dict_bili["mobi_app"]}&owner_id={i2}&platform={self.dict_bili["platform"]}&ts={self.CurrentTime()}'
        sign = self.calc_sign(temp_params)
        url = f'https://api.vc.bilibili.com/link_setting/v1/link_setting/sign_in?{temp_params}&sign={sign}'
        json_rsp = await self.other_req_json('GET', url, headers=self.dict_bili['appheaders'])
        return json_rsp
        
    async def ReqGiveCoin2Av(self, video_id, num):
        url = 'https://api.bilibili.com/x/web-interface/coin/add'
        pcheaders = {
            **(self.dict_bili['pcheaders']),
            'referer': f'https://www.bilibili.com/video/av{video_id}'
            }
        data = {
            'aid': video_id,
            'multiply': num,
            'cross_domain': 'true',
            'csrf': self.dict_bili['csrf']
        }
        json_rsp = await self.other_req_json('POST', url, headers=pcheaders, data=data)
        return json_rsp

    async def Heartbeat(self, aid, cid):
        url = 'https://api.bilibili.com/x/report/web/heartbeat'
        data = {'aid': aid, 'cid': cid, 'mid': self.dict_bili['uid'], 'csrf': self.dict_bili['csrf'],
                'played_time': 0, 'realtime': 0,
                'start_ts': self.CurrentTime(), 'type': 3, 'dt': 2, 'play_type': 1}
        json_rsp = await self.other_req_json('POST', url, data=data, headers=self.dict_bili['pcheaders'])
        return json_rsp

    async def ReqMasterInfo(self):
        url = 'https://account.bilibili.com/home/reward'
        json_rsp = await self.other_req_json('GET', url, headers=self.dict_bili['pcheaders'])
        return json_rsp

    async def ReqVideoCid(self, video_aid):
        url = f'https://www.bilibili.com/widget/getPageList?aid={video_aid}'
        json_rsp = await self.other_req_json('GET', url)
        return json_rsp

    async def DailyVideoShare(self, video_aid):
        url = 'https://api.bilibili.com/x/web-interface/share/add'
        data = {'aid': video_aid, 'jsonp': 'jsonp', 'csrf': self.dict_bili['csrf']}
        json_rsp = await self.other_req_json('POST', url, data=data, headers=self.dict_bili['pcheaders'])
        return json_rsp
    
    async def req_fetch_uper_video(self, mid, page):
        url = f'https://space.bilibili.com/ajax/member/getSubmitVideos?mid={mid}&pagesize=100&page={page}'
        json_rsp = await self.other_req_json('GET', url)
        return json_rsp
                
    async def req_fetch_av(self):
        text_tsp = await self.other_req_text('GET', 'https://www.bilibili.com/ranking/all/0/0/1/')
        return text_tsp
    
    async def req_vote_case(self, id, vote):
        url = 'http://api.bilibili.com/x/credit/jury/vote'
        payload = {
            "jsonp": "jsonp",
            "cid": id,
            "vote": vote,
            "content": "",
            "likes": "",
            "hates": "",
            "attr": "1",
            "csrf": self.dict_bili['csrf']
        }
        json_rsp = await self.other_req_json('POST', url, headers=self.dict_bili['pcheaders'], data=payload)
        return json_rsp
        
    async def req_fetch_case(self):
        url = 'http://api.bilibili.com/x/credit/jury/caseObtain'
        payload = {
            "jsonp": "jsonp",
            "csrf": self.dict_bili['csrf']
        }
        json_rsp = await self.other_req_json('POST', url, headers=self.dict_bili['pcheaders'], data=payload)
        return json_rsp
        
    async def req_check_voted(self, id):
        headers = {
            **(self.dict_bili['pcheaders']),
            'Referer': f'https://www.bilibili.com/judgement/vote/{id}',
        }
        url = f'https://api.bilibili.com/x/credit/jury/juryCase?jsonp=jsonp&callback=jQuery1720{self.randomint()}_{self.CurrentTime()}&cid={id}&_={self.CurrentTime()}'
        text_rsp = await self.other_req_text('GET', url, headers=headers)
        # print(text_rsp)
        return text_rsp
    
                
