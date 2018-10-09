import copy
import sys
import aiohttp
from webhub.base_web_hub import BaseWebHub


class OtherWebHub(BaseWebHub):
    
    def __init__(self, id, dict_new, dict_bili):
        self.dict_bili = copy.deepcopy(dict_bili)
        self.set_status(dict_new)
        self.user_id = id
        self.var_other_session = None
        if dict_bili:
            self.app_params = f'actionKey={dict_bili["actionKey"]}&appkey={dict_bili["appkey"]}&build={dict_bili["build"]}&device={dict_bili["device"]}&mobi_app={dict_bili["mobi_app"]}&platform={dict_bili["platform"]}'
            
    @property
    def other_session(self):
        if self.var_other_session is None:
            self.var_other_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3))
            # print(0)
        return self.var_other_session
        
    async def other_session_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.other_session.get(url, headers=headers, data=data, params=params) as response:
                    json_rsp = await self.get_json_rsp(response, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
                
    async def other_session_post(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.other_session.post(url, headers=headers, data=data, params=params) as response:
                    json_rsp = await self.get_json_rsp(response, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
                
    async def session_text_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.other_session.get(url, headers=headers, data=data, params=params) as response:
                    text_rsp = await self.get_text_rsp(response, url)
                    if text_rsp is not None:
                        return text_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
                
    async def search_liveuser(self, name):
        search_url = f'https://search.bilibili.com/api/search?search_type=live_user&keyword={name}&page=1'
        json_rsp = await self.other_session_get(search_url)
        return json_rsp

    async def search_biliuser(self, name):
        search_url = f"https://search.bilibili.com/api/search?search_type=bili_user&keyword={name}"
        json_rsp = await self.other_session_get(search_url)
        return json_rsp
        
    async def load_img(self, url):
        return await self.other_session.get(url)
        
    async def get_grouplist(self):
        url = "https://api.vc.bilibili.com/link_group/v1/member/my_groups"
        json_rsp = await self.other_session_get(url, headers=self.dict_bili['pcheaders'])
        return json_rsp
    
    async def assign_group(self, i1, i2):
        temp_params = f'access_key={self.dict_bili["access_key"]}&actionKey={self.dict_bili["actionKey"]}&appkey={self.dict_bili["appkey"]}&build={self.dict_bili["build"]}&device={self.dict_bili["device"]}&group_id={i1}&mobi_app={self.dict_bili["mobi_app"]}&owner_id={i2}&platform={self.dict_bili["platform"]}&ts={self.CurrentTime()}'
        sign = self.calc_sign(temp_params)
        url = f'https://api.vc.bilibili.com/link_setting/v1/link_setting/sign_in?{temp_params}&sign={sign}'
        json_rsp = await self.other_session_get(url, headers=self.dict_bili['appheaders'])
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
        json_rsp = await self.other_session_post(url, headers=pcheaders, data=data)
        return json_rsp

    async def Heartbeat(self, aid, cid):
        url = 'https://api.bilibili.com/x/report/web/heartbeat'
        data = {'aid': aid, 'cid': cid, 'mid': self.dict_bili['uid'], 'csrf': self.dict_bili['csrf'],
                'played_time': 0, 'realtime': 0,
                'start_ts': self.CurrentTime(), 'type': 3, 'dt': 2, 'play_type': 1}
        json_rsp = await self.other_session_post(url, data=data, headers=self.dict_bili['pcheaders'])
        return json_rsp

    async def ReqMasterInfo(self):
        url = 'https://account.bilibili.com/home/reward'
        json_rsp = await self.other_session_get(url, headers=self.dict_bili['pcheaders'])
        return json_rsp

    async def ReqVideoCid(self, video_aid):
        url = f'https://www.bilibili.com/widget/getPageList?aid={video_aid}'
        json_rsp = await self.other_session_get(url)
        return json_rsp

    async def DailyVideoShare(self, video_aid):
        url = 'https://api.bilibili.com/x/web-interface/share/add'
        data = {'aid': video_aid, 'jsonp': 'jsonp', 'csrf': self.dict_bili['csrf']}
        json_rsp = await self.other_session_post(url, data=data, headers=self.dict_bili['pcheaders'])
        return json_rsp
    
    async def req_fetch_uper_video(self, mid, page):
        url = f'https://space.bilibili.com/ajax/member/getSubmitVideos?mid={mid}&pagesize=100&page={page}'
        json_rsp = await self.other_session_get(url)
        return json_rsp
                
    async def req_fetch_av(self):
        text_tsp = await self.session_text_get('https://www.bilibili.com/ranking/all/0/0/1/')
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
        json_rsp = await self.other_session_post(url, headers=self.dict_bili['pcheaders'], data=payload)
        return json_rsp
        
    async def req_fetch_case(self):
        url = 'http://api.bilibili.com/x/credit/jury/caseObtain'
        payload = {
            "jsonp": "jsonp",
            "csrf": self.dict_bili['csrf']
        }
        json_rsp = await self.other_session_post(url, headers=self.dict_bili['pcheaders'], data=payload)
        return json_rsp
        
    async def req_check_voted(self, id):
        headers = {
            **(self.dict_bili['pcheaders']),
            'Referer': f'https://www.bilibili.com/judgement/vote/{id}',
        }
        url = f'https://api.bilibili.com/x/credit/jury/juryCase?jsonp=jsonp&callback=jQuery1720{self.randomint()}_{self.CurrentTime()}&cid={id}&_={self.CurrentTime()}'
        text_rsp = await self.session_text_get(url, headers=headers)
        # print(text_rsp)
        return text_rsp
    
                
