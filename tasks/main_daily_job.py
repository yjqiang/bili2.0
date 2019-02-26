import re
import random
from datetime import datetime
import utils
from reqs.utils import UtilsReq
from reqs.main_daily_job import JudgeCaseReq, BiliMainReq


class JudgeCaseTask:
    @staticmethod
    def target(step):
        if step == 0:
            return JudgeCaseTask.judge
        if step == 1:
            return JudgeCaseTask.judge_case
        return None
        
    @staticmethod
    async def print_judge_tasks(user):
        json_rsp = await user.req_s(JudgeCaseReq.fetch_judged_cases, user)
        data = json_rsp['data']
        if data is None:
            user.info([f'该用户非风纪委成员'], True)
            return
        today = datetime.today().date()
        sum_cases = 0
        valid_cases = 0
        judging_cases = 0
        for case in data:
            ts = case['voteTime'] / 1000
            vote_day = datetime.fromtimestamp(ts).date()
            if vote_day == today:
                sum_cases += 1
                vote = case['vote']
                if not vote:
                    judging_cases += 1
                elif case['vote'] != 3:
                    valid_cases += 1
        user.info([f'今日投票{sum_cases}（{valid_cases}票有效（非弃权），{judging_cases}票还在进行中）'], True)
        
    @staticmethod
    def judge_advice(num_judged, pct):
        advice = None
        if num_judged >= 300:
            # 认为这里可能出现了较多分歧，抬一手
            if pct >= 0.4:
                advice = 2
            elif pct <= 0.25:
                advice = 4
        elif num_judged >= 150:
            if pct >= 0.9:
                advice = 2
            elif pct <= 0.1:
                advice = 4
        elif num_judged >= 50:
            if pct >= 0.97:
                advice = 2
            elif pct <= 0.03:
                advice = 4
        # 抬一手
        if advice is None and num_judged >= 400:
            advice = 2
        return advice
        
    @staticmethod
    async def check_case_status(user, case_id):
        # 3放弃
        # 2 否 voterule
        # 4 删除 votedelete
        # 1 封杀 votebreak
        json_rsp = await user.req_s(JudgeCaseReq.check_case_status, user, case_id)
        data = json_rsp['data']
        votebreak = data['voteBreak']
        voteDelete = data['voteDelete']
        voteRule = data['voteRule']
        voted = votebreak+voteDelete+voteRule
        percent = (voteRule / voted) if voted else 0
        
        print(f'\"{data["originContent"]}\"')
        print('该案件目前已投票', voted)
        print('认为言论合理比例', percent)
        return voted, percent
        
    @staticmethod
    async def judge_case(user, case_id, wait_time, fluctuation):
        print(f'{case_id}   {wait_time}   {fluctuation}')
        min_pct, max_pct = fluctuation
        num_judged, ok_pct = await JudgeCaseTask.check_case_status(user, case_id)
        advice = JudgeCaseTask.judge_advice(num_judged, ok_pct)
        if num_judged >= 50:
            min_pct = min(min_pct, ok_pct)
            max_pct = max(max_pct, ok_pct)
            print('统计投票波动情况', min_pct, max_pct)
        
        if advice is not None:
            pass
        elif wait_time >= 1200:
            print('进入二次判定')
            # 如果case判定中，波动很小，则表示趋势基本一致
            if 0 <= max_pct - min_pct <= 0.1 and num_judged > 200:
                num_judged += 100
                advice0 = JudgeCaseTask.judge_advice(num_judged, max_pct)
                advice1 = JudgeCaseTask.judge_advice(num_judged, min_pct)
                advice = advice0 if advice0 == advice1 else None
            print('二次判定结果', advice)
        else:
            sleeptime = 180 if num_judged < 300 else 60
            user.info([f'案件{case_id}暂时无法判定，在{sleeptime}后重新尝试'], True)
            wait_time += sleeptime
            fluctuation = (min_pct, max_pct)
            return (1, (sleeptime, sleeptime+5), user.id, case_id, wait_time, fluctuation),
        
        decision = advice if advice is not None else 3
        dicision_info = '作废票' if decision == 3 else '有效票'
        print(f'{case_id}案件的投票决策', decision, dicision_info)
        json_rsp = await user.req_s(JudgeCaseReq.judge_case, user, case_id, decision)
        print(json_rsp)
        if not json_rsp['code']:
            print(f'{case_id}案件 投票成功')
        else:
            print(f'{case_id}案件 投票失败，请反馈作者')
        sleeptime = 5
        return (0, (sleeptime, sleeptime+30), user.id),
                   
    @staticmethod
    async def judge(user):
        json_rsp = await user.req_s(JudgeCaseReq.fetch_case, user)
        print(json_rsp)
        if not json_rsp['code']:
            case_id = json_rsp['data']['id']
            wait_time = 0
            fluctuation = (1, 0)
            sleeptime = 0
            return (1, (sleeptime, sleeptime+5), user.id, case_id, wait_time, fluctuation),
        else:
            print('本次未获取到案件')
            sleeptime = 3600
            return (0, (sleeptime, sleeptime+30), user.id),
            

# 这里怀疑登陆硬币没做好！！！
class BiliMainTask:
    @staticmethod
    def target(step):
        if step == 0:
            return BiliMainTask.finish_bilimain_tasks
        return None
        
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
            return False
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
            if code == -104 or code == -102 or code == -650:
                return -1
            return 1
    
    @staticmethod
    async def fetch_top_videos(user):
        text_rsp = await user.req_s(BiliMainReq.fetch_top_videos, user)
        aids = re.findall(r'(?<=www.bilibili.com/video/av)\d+(?=/)', text_rsp)
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
        while num_coin > 0:
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
    
    # 后期微调，因为获取fetch_top_videos这个东西可以共享的！！！但是调节起来估计很恶心
    @staticmethod
    async def finish_bilimain_tasks(user):
        login, watch_av, num, share_av = await BiliMainTask.fetch_bilimain_tasks(user)
        if user.task_ctrl['fetchrule'] == 'bilitop':
            aids = await BiliMainTask.fetch_top_videos(user)
            # print(list_topvideo)
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
        # b站傻逼有记录延迟，3点左右成功率高一点
        sleeptime = utils.seconds_until_tomorrow() + 10800
        return (0, (sleeptime, sleeptime+30), user.id),
        
