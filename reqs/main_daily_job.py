import utils
from .utils import UtilsReq


class JudgeCaseReq:
    @staticmethod
    async def judge_case(user, case_id, decision):
        url = 'http://api.bilibili.com/x/credit/jury/vote'
        payload = {
            "jsonp": "jsonp",
            "cid": case_id,
            "vote": decision,
            "content": "",
            "likes": "",
            "hates": "",
            "attr": "1",
            "csrf": user.dict_bili['csrf']
        }
        json_rsp = await user.other_session.request_json('POST', url, headers=user.dict_bili['pcheaders'], data=payload)
        return json_rsp
     
    @staticmethod
    async def fetch_case(user):
        url = 'http://api.bilibili.com/x/credit/jury/caseObtain'
        data = {
            "jsonp": "jsonp",
            "csrf": user.dict_bili['csrf']
        }
        json_rsp = await user.other_session.request_json('POST', url, headers=user.dict_bili['pcheaders'], data=data)
        return json_rsp
        
    @staticmethod
    async def check_case_status(user, case_id):
        headers = {
            **(user.dict_bili['pcheaders']),
            'Referer': f'https://www.bilibili.com/judgement/vote/{case_id}',
        }
        url = f'https://api.bilibili.com/x/credit/jury/juryCase?callback=jQuery1720{UtilsReq.randomint()}_{utils.curr_time()}&cid={case_id}&_={utils.curr_time()}'
        json_rsp = await user.other_session.request_json('GET', url, headers=headers)
        return json_rsp
        
    @staticmethod
    async def fetch_judged_cases(user):
        headers = {
            **(user.dict_bili['pcheaders']),
            'Referer': 'https://www.bilibili.com/judgement/index',
        }
        url = f'https://api.bilibili.com/x/credit/jury/caseList?callback=jQuery1720{UtilsReq.randomint()}_{utils.curr_time()}&pn=1&ps=25&_={utils.curr_time()}'
        json_rsp = await user.other_session.request_json('GET', url, headers=headers)
        return json_rsp
        
        
class BiliMainReq:
    @staticmethod
    async def send_coin2video(user, aid, num_sent):
        url = 'https://api.bilibili.com/x/web-interface/coin/add'
        pcheaders = {
            **(user.dict_bili['pcheaders']),
            'referer': f'https://www.bilibili.com/video/av{aid}'
            }
        data = {
            'aid': aid,
            'multiply': num_sent,
            'cross_domain': 'true',
            'csrf': user.dict_bili['csrf']
        }
        json_rsp = await user.other_session.request_json('POST', url, headers=pcheaders, data=data)
        return json_rsp

    @staticmethod
    async def heartbeat(user, aid, cid):
        url = 'https://api.bilibili.com/x/report/web/heartbeat'
        data = {
            'aid': aid,
            'cid': cid,
            'mid': user.dict_bili['uid'],
            'csrf': user.dict_bili['csrf'],
            'played_time': 0,
            'realtime': 0,
            'start_ts': utils.curr_time(),
            'type': 3,
            'dt': 2,
            'play_type': 1
            }
        json_rsp = await user.other_session.request_json('POST', url, data=data, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def share_video(user, aid):
        url = 'https://api.bilibili.com/x/web-interface/share/add'
        data = {'aid': aid, 'jsonp': 'jsonp', 'csrf': user.dict_bili['csrf']}
        json_rsp = await user.other_session.request_json('POST', url, data=data, headers=user.dict_bili['pcheaders'])
        return json_rsp
        
    @staticmethod
    async def aid2cid(user, aid):
        url = f'https://api.bilibili.com/x/web-interface/view?aid={aid}'
        json_rsp = await user.other_session.request_json('GET', url)
        return json_rsp
    
    @staticmethod
    async def fetch_uper_videos(user, mid, page):
        url = f'https://app.bilibili.com/x/v2/space/archive?build=1&pn={page}&ps=20&vmid={mid}'
        json_rsp = await user.other_session.request_json('GET', url)
        return json_rsp
                
    @staticmethod
    async def fetch_top_videos(user):
        url = 'https://www.bilibili.com/ranking/all/0/0/1/'
        text_tsp = await user.other_session.request_text('GET', url, headers=user.dict_bili['pcheaders'])
        return text_tsp


class DahuiyuanReq:
    # b 币
    @staticmethod
    async def recv_privilege_1(user):
        url = f'https://api.bilibili.com/x/vip/privilege/receive'
        data = {
            'type': 1,
            'csrf': user.dict_bili['csrf'],
        }
        json_rsp = await user.other_session.request_json('POST', url, headers=user.dict_bili['pcheaders'], data=data)
        return json_rsp
