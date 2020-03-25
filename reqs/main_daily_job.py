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
            'select_like': 0,
            'cross_domain': 'true',
            'csrf': user.dict_bili['csrf']
        }
        json_rsp = await user.other_session.request_json('POST', url, headers=pcheaders, data=data)
        return json_rsp

    @staticmethod
    async def heartbeat(user, bvid, cid):
        url = 'https://api.bilibili.com/x/click-interface/web/heartbeat'
        data = {
            'cid': cid,
            'bvid': bvid,
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
        url = f'https://api.bilibili.com/x/space/arc/search?' \
              f'mid={mid}&ps=30&tid=0&pn={page}&keyword=&order=pubdate&jsonp=jsonp'
        json_rsp = await user.other_session.request_json('GET', url)
        return json_rsp
                
    @staticmethod
    async def fetch_top_videos(user):
        # 一个av对应多cid时候，就挑选了一个视频作为cid
        url = 'https://api.bilibili.com/x/web-interface/ranking?rid=0&day=1&type=1&arc_type=0&jsonp=jsonp'
        json_rsp = await user.other_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp


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
