import re
import random
import asyncio
from typing import Optional

from reqs.utils import UtilsReq
from reqs.main_daily_job import JudgeCaseReq, BiliMainReq, DahuiyuanReq
from .base_class import Sched, DontWait, Unique


class JudgeCaseTask(Sched, DontWait, Unique):
    TASK_NAME = 'judge_case'

    @staticmethod
    async def check(_):
        return (-2, (0, 30)),
        
    @staticmethod
    def judge_advice(num_judged, pct) -> Optional[int]:
        if num_judged >= 300:
            # 认为这里可能出现了较多分歧，抬一手
            if pct >= 0.4:
                return 2
            elif pct <= 0.25:
                return 4
        elif num_judged >= 150:
            if pct >= 0.9:
                return 2
            elif pct <= 0.1:
                return 4
        elif num_judged >= 50:
            if pct >= 0.97:
                return 2
            elif pct <= 0.03:
                return 4
        # 抬一手
        if num_judged >= 400:
            return 2
        return None
        
    @staticmethod
    async def check_case_status(user, case_id):
        # 3 放弃
        # 2 否 vote_rule
        # 4 删除 vote_delete
        # 1 封杀 vote_break
        json_rsp = await user.req_s(JudgeCaseReq.check_case_status, user, case_id)
        data = json_rsp['data']
        vote_break = data['voteBreak']
        vote_delete = data['voteDelete']
        vote_rule = data['voteRule']
        num_voted = vote_break + vote_delete + vote_rule
        ok_percent = (vote_rule / num_voted) if num_voted else 0
        user.info(f'案件{case_id}目前已投票{num_voted}, 认为言论合理比例{ok_percent}')
        return num_voted, ok_percent
        
    @staticmethod
    async def judge_1_case(user, case_id):
        wait_time = 0
        min_ok_pct = 1
        max_ok_pct = 0
        user.info(f'马上开始判定案件{case_id}')
        while True:
            num_judged, ok_pct = await JudgeCaseTask.check_case_status(user, case_id)
            advice = JudgeCaseTask.judge_advice(num_judged, ok_pct)
            if num_judged >= 50:
                min_ok_pct = min(min_ok_pct, ok_pct)
                max_ok_pct = max(max_ok_pct, ok_pct)
                # user.info('更新统计投票波动情况')
            user.info(f'案件{case_id}已经等待{wait_time}s，统计波动区间为{min_ok_pct}-{max_ok_pct}')
            if advice is None:
                if wait_time >= 1200:
                    # 如果case判定中，波动很小，则表示趋势基本一致
                    if 0 <= max_ok_pct - min_ok_pct <= 0.1 and num_judged > 200:
                        num_judged += 100
                        advice0 = JudgeCaseTask.judge_advice(num_judged, max_ok_pct)
                        advice1 = JudgeCaseTask.judge_advice(num_judged, min_ok_pct)
                        advice = advice0 if advice0 == advice1 else None
                    user.info('二次判定结果 {advice}')
                else:
                    sleeptime = 200 if num_judged < 300 else 60
                    user.info(f'案件{case_id}暂时无法判定，在{sleeptime}后重新尝试')
                    wait_time += sleeptime
                    await asyncio.sleep(sleeptime)
                    continue

            decision = advice if advice is not None else 3  # 如果还不行就放弃
            dicision_info = '作废票' if decision == 3 else '有效票'
            json_rsp = await user.req_s(JudgeCaseReq.judge_case, user, case_id, decision)
            user.info(f'案件{case_id}的投票决策：{dicision_info}({decision})', json_rsp)
            if not json_rsp['code']:
                user.info(f'案件{case_id}投票成功')
            else:
                user.info(f'案件{case_id}投票失败，请反馈作者')
            return
                   
    @staticmethod
    async def work(user):
        while True:
            json_rsp = await user.req_s(JudgeCaseReq.fetch_case, user)
            if not json_rsp['code']:
                case_id = json_rsp['data']['id']
                await JudgeCaseTask.judge_1_case(user, case_id)
            else:
                user.info('本次未获取到案件')
                return
            

class BiliMainTask(Sched, DontWait, Unique):
    TASK_NAME = 'bili_main'

    @staticmethod
    async def check(user):
        aids = await BiliMainTask.fetch_top_videos(user)
        return (-2, (0, 30), aids),
        
    @staticmethod
    async def fetch_bilimain_tasks(user):
        json_rsp = await user.req_s(UtilsReq.fetch_bilimain_tasks, user)
        data = json_rsp['data']
        login = data['login']
        watch_av = data['watch_av']
        coins_av = data['coins_av']
        share_av = data['share_av']
        print(login, watch_av, coins_av, share_av)
        return login, watch_av, coins_av, share_av
        
    @staticmethod
    async def send_coin2video(user, aid, num_sent):
        if num_sent not in (1, 2):
            return 1
        # 10004 稿件已经被删除
        # 34005 超过，满了
        # -104 不足硬币
        json_rsp = await user.req_s(BiliMainReq.send_coin2video, user, aid, num_sent)
        code = json_rsp['code']
        if not code:
            print(f'给视频av{aid}投{num_sent}枚硬币成功')
            return 0
        else:
            print('投币失败', json_rsp)
            # -104 硬币不足 -650 用户等级太低
            # -102 账号被封停
            # -101 未登陆
            if code == -104 or code == -102 or code == -650:
                return -1
            return 1
    
    @staticmethod
    async def fetch_top_videos(user):
        text_rsp = await user.req_s(BiliMainReq.fetch_top_videos, user)
        aids = [i.group(1) for i in re.finditer(r'www.bilibili.com/video/av(\d+)', text_rsp)]
        if not aids:
            user.warn(f'{text_rsp}, aid这里')
        # print(aids)
        aids = list(set(aids))
        return aids
    
    @staticmethod
    async def fetch_uper_videos(user, uids):
        aids = []
        for uid in uids:
            # 避免一堆videos，只取前几页
            for page in range(1, 5):
                json_rsp = await user.req_s(BiliMainReq.fetch_uper_videos, user, uid, page)
                videos = json_rsp['data']['item']
                if not videos:
                    break
                aids += [int(video['param']) for video in videos]
        return aids
        
    @staticmethod
    async def aid2cid(user, aid):
        json_rsp = await user.req_s(BiliMainReq.aid2cid, user, aid)
        code = json_rsp['code']
        if not code:
            data = json_rsp['data']
            state = data['state']
            if not state:  # state会-4/1 其中-4没有cid，1还能用，保险起见都不管了
                cid = data['pages'][0]['cid']  # 有的av有多个视频即多个cid
                return cid
        # 62002 稿件不可见
        # -404 啥都木有
        # -403 访问权限不足
        # 62004 视频正在审核中
        # 62003 等待发布中
        print(json_rsp)
        return None
        
    @staticmethod
    async def heartbeat(user, aid, cid):
        print('开始获取视频观看经验')
        json_rsp = await user.req_s(BiliMainReq.heartbeat, user, aid, cid)
        print('获取视频观看', json_rsp)
    
    @staticmethod
    async def send_coin(user, num_coin, aids):
        print('开始赠送硬币')
        for _ in range(user.task_ctrl['givecoin_max_try_times']):
            if num_coin <= 0:
                return
            aid = random.choice(aids)
            result = await BiliMainTask.send_coin2video(user, aid, 1)
            if result == -1:
                return
            elif not result:
                num_coin -= 1
    
    # 伪造了这个过程，实际没有分享出去
    @staticmethod
    async def share_video(user, aid):
        print('开始获取视频分享经验')
        print(await user.req_s(BiliMainReq.share_video, user, aid))

    @staticmethod
    async def work(user, top_video_aids):
        login, watch_av, num, share_av = await BiliMainTask.fetch_bilimain_tasks(user)
        if user.task_ctrl['fetchrule'] == 'bilitop':
            aids = top_video_aids
        else:
            aids = await BiliMainTask.fetch_uper_videos(user, user.task_ctrl['mid'])
        while True:
            aid = random.choice(aids)
            cid = await BiliMainTask.aid2cid(user, aid)
            if cid is not None:
                break
        if (not login) or not watch_av:
            await BiliMainTask.heartbeat(user, aid, cid)
        if not share_av:
            await BiliMainTask.share_video(user, aid)
        coin_set = min(user.task_ctrl['givecoin'], 5)
        num_coin = coin_set - num / 10
        if num_coin:
            await BiliMainTask.send_coin(user, num_coin, aids)


class DahuiyuanTask(Sched, DontWait, Unique):
    TASK_NAME = 'dahuiyuan'

    @staticmethod
    async def check(_):
        return (-2, (0, 30)),

    @staticmethod
    async def work(user):
        return None
        json_rsp = await user.req_s(DahuiyuanReq.recv_privilege_1, user)
        if not json_rsp['code']:
            user.info('领取b币成功')
        else:
            user.info(f'领取b币可能重复 {json_rsp}')
