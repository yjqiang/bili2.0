import json
import asyncio
import random
from typing import Optional

import utils
from dyn import dyn_raffle_sql
from dyn.bili_data_types import DynRaffleStatus, DynRaffleJoined, DynRaffleResults, DynRaffleLuckydog
from reqs.dyn_raffle_handler import DynRaffleHandlerReq
from .utils import UtilsTask


class DynRaffleHandlerTask:
    @staticmethod
    def target(step):
        if step == 0:
            return DynRaffleHandlerTask.check
        if step == 1:
            return DynRaffleHandlerTask.join
        if step == 2:
            return DynRaffleHandlerTask.notice
        return None

    @staticmethod
    async def create_dyn(user):
        json_rsp = await user.req_s(DynRaffleHandlerReq.create_dyn, user)
        user.info([f'用户生成动态 {json_rsp}'], True)
        return int(json_rsp['data']['doc_id'])

    @staticmethod
    async def repost_dyn_raffle(user, orig_dynid, at_num):
        if len(user.dyn_lottery_friends) < at_num:
            return False
        print('开始转发动态: ', orig_dynid)
        at_users = [(str(uid), name) for uid, name in random.sample(user.dyn_lottery_friends, at_num)]

        location = 0
        ctrl = []
        content = ''
        for uid, name in at_users:
            ulength = len(name)
            ctrl_piece = {
                'data': uid,
                'location': location,
                'length': ulength + 1,  # 算上at符号
                'type': 1,
            }
            ctrl.append(ctrl_piece)
            location += ulength + 1 + 1  # 空格
            # 1个空格隔开
            content += f'@{name} '

        message = ["emmmm...", "中奖吧！", "啊~~", "抽奖玩", "拉低中奖率2333", "反正先转了再说", "先转为敬", "大佬大佬抽奖带我.jpg", "我是非酋", "欧皇驾到"]
        content += random.choice(message)
        at_uids = ','.join([uid for uid, _ in at_users])
        str_ctrl = json.dumps(ctrl)

        json_rsp = await user.req_s(DynRaffleHandlerReq.repost_dyn, user, orig_dynid, content, at_uids, str_ctrl)
        data = json_rsp['data']
        print(json_rsp)
        return not json_rsp['code'] and data['errmsg'] == '符合条件，允许发布'

    @staticmethod
    async def fetch_reposted_dynid(user, uid, orig_dynid):
        offset = 0
        while True:
            json_rsp = await user.req_s(DynRaffleHandlerReq.fetch_dyns, user, uid, offset)
            if 'cards' not in json_rsp['data']:
                return None
            cards = json_rsp['data']['cards']
            assert cards
            for dyn in cards:
                desc = dyn['desc']
                print(desc['orig_dy_id'], desc['dynamic_id'])
                if int(orig_dynid) == int(desc['orig_dy_id']):
                    return int(desc['dynamic_id'])

            offset = cards[-1]['desc']['dynamic_id']

    @staticmethod
    async def del_dyn_by_docid(user, doc_id):
        json_rsp = await user.req_s(DynRaffleHandlerReq.del_dyn_by_docid, user, doc_id)
        code = json_rsp['code']
        # 0(success) / -1(哎呀，系统君开小差了(⊙□⊙))
        if not code:
            user.info([f'用户删除动态{doc_id}(doc_id)成功'], True)
            return True
        user.info([f'用户删除动态{doc_id}(doc_id)失败，可能系统错误或重复删除请求, {json_rsp}'], True)
        return False

    @staticmethod
    async def del_dyn_by_dynid(user, dyn_id):
        json_rsp = await user.req_s(DynRaffleHandlerReq.del_dyn_by_dynid, user, dyn_id)
        code = json_rsp['code']
        # logout提示信息{'code': -6, 'msg': '', 'message': '', 'data': {}}
        # {'code': 2200013, 'msg': '不能删除别人的动态', 'message': '不能删除别人的动态', 'data': {}}
        # {'code': 0, 'msg': 'succ', 'message': 'succ', 'data': {'result': 0, 'errmsg': '删除成功', '_gt_': 0}}
        # {'code': 1100404, 'msg': '不能重复删除', 'message': '不能重复删除', 'data': {}}
        # {'code': 1100405, 'msg': '', 'message': '', 'data': {}}
        if not code:
            user.info([f'用户删除动态{dyn_id}(dyn_id)成功'], True)
            return True
        user.info([f'用户删除动态{dyn_id}(dyn_id)失败，可能系统错误或重复删除请求, {json_rsp}'], True)
        return False

    @staticmethod
    async def is_dyn_raffle(user, doc_id):
        json_rsp = await user.req_s(DynRaffleHandlerReq.is_dyn_raffle, user, doc_id)
        code = json_rsp['code']
        print('_____________________________________')
        print('is_dyn_raffle:', doc_id, 'code:', code)
        if not code:
            data = json_rsp['data']
            item = data['item']
            str_ext = item['extension']
            print(doc_id, str_ext)
            if str_ext:
                dict_ext = json.loads(str_ext.replace('\'', ''))
                # 抽奖 不符合的可能{}或者lott_cfg为空或者其他一些
                if 'lott_cfg' in dict_ext and dict_ext['lott_cfg']:
                    lott_cfg = json.loads(dict_ext['lott_cfg'])
                    print('lott_cfg', lott_cfg)
                    title = lott_cfg['title']
                    # 目前未发现其他title
                    if title == '互动抽奖':
                        uid = data['user']['uid']
                        post_time = int(item['upload_timestamp'])
                        describe = item['description']
                        return 0, (uid, post_time, describe)
                    else:
                        user.warn(f'互动抽奖初步查询 {json_rsp}')
                        return 2, None
            return 1, None
        elif code == 110001:
            return -1, None
        # 目前未发现其他code
        user.warn(f'互动抽奖初步查询 {json_rsp}')
        return 3, None

    @staticmethod
    async def fetch_dyn_raffle_status(
            user, doc_id: int, uid: int, post_time: int, describe: str) -> Optional[DynRaffleStatus]:
        json_rsp = await user.req_s(DynRaffleHandlerReq.fetch_dyn_raffle, user, doc_id)
        code = json_rsp['code']
        if not code:
            print('check raffle_status', json_rsp)
            data = json_rsp['data']
            dyn_id = data['business_id']
            # 开奖时间
            lottery_time = data['lottery_time']

            # @人数
            at_num = data['lottery_at_num']
            # 关注 1 true
            feed_limit = data['lottery_feed_limit']
            first_prize_cmt = data['first_prize_cmt']
            second_prize_cmt = data.get('second_prize_cmt', '')
            third_prize_cmt = data.get('third_prize_cmt', '')
            # 需要邮寄???????存疑
            # post = data['need_post']
            dyn_raffle_status = DynRaffleStatus(
                dyn_id=dyn_id,
                doc_id=doc_id,
                describe=describe,
                uid=uid,
                post_time=post_time,
                lottery_time=lottery_time,
                at_num=at_num,
                feed_limit=feed_limit,
                prize_cmt_1st=first_prize_cmt,
                prize_cmt_2nd=second_prize_cmt,
                prize_cmt_3rd=third_prize_cmt
            )
            print('获取到的抽奖信息为', dyn_raffle_status)
            return dyn_raffle_status
        elif code == -9999:
            print(f'抽奖动态{doc_id}已经删除')
            return None

    @staticmethod
    async def fetch_dyn_raffle_results(
            user, dyn_raffle_status: DynRaffleStatus) -> Optional[DynRaffleResults]:
        json_rsp = await user.req_s(DynRaffleHandlerReq.fetch_dyn_raffle, user, dyn_raffle_status.doc_id)
        code = json_rsp['code']
        if not code:
            print('check raffle_status', json_rsp)
            data = json_rsp['data']
            if 'lottery_result' not in data:
                return None
            lottery_result = data['lottery_result']
            first_prize_result = lottery_result['first_prize_result']
            second_prize_result = lottery_result.get('second_prize_result', [])
            third_prize_result = lottery_result.get('third_prize_result', [])
            list_first_prize_result = [int(lucky_dog['uid']) for lucky_dog in first_prize_result]
            list_second_prize_result = [int(lucky_dog['uid']) for lucky_dog in second_prize_result]
            list_third_prize_result = [int(lucky_dog['uid']) for lucky_dog in third_prize_result]

            dyn_raffle_results = DynRaffleResults(
                dyn_id=dyn_raffle_status.dyn_id,
                doc_id=dyn_raffle_status.doc_id,
                describe=dyn_raffle_status.describe,
                uid=dyn_raffle_status.uid,
                post_time=dyn_raffle_status.post_time,
                lottery_time=dyn_raffle_status.lottery_time,

                prize_cmt_1st=dyn_raffle_status.prize_cmt_1st,
                prize_cmt_2nd=dyn_raffle_status.prize_cmt_2nd,
                prize_cmt_3rd=dyn_raffle_status.prize_cmt_3rd,
                prize_list_1st=list_first_prize_result,
                prize_list_2nd=list_second_prize_result,
                prize_list_3rd=list_third_prize_result
            )
            print('获取到的抽奖信息为', dyn_raffle_results)
            return dyn_raffle_results
        elif code == -9999:
            print(f'抽奖动态{dyn_raffle_status.doc_id}已经删除')
            return None

    @staticmethod
    async def check(user, dyn_raffle_status: DynRaffleStatus):
        if not dyn_raffle_sql.is_raffleid_duplicate(dyn_raffle_status.dyn_id):
            user.info([f'{dyn_raffle_status.doc_id}的动态抽奖通过重复性过滤'], True)
            dyn_raffle_sql.insert_dynraffle_status_table(dyn_raffle_status)
            max_sleeptime = max(min(35, dyn_raffle_status.lottery_time-utils.curr_time() - 10), 0)
            return (1, (0, max_sleeptime), -2, dyn_raffle_status),
        user.info([f'{dyn_raffle_status.doc_id}的动态抽奖未通过重复性过滤'], True)
        return None

    @staticmethod
    async def follow_raffle_organizer(user, uid):
        is_following, group_ids = await UtilsTask.check_follow(user, uid)
        if is_following:
            print('已经关注，不再处理')
            return
        print('未关注，即将弄到抽奖分组')
        await UtilsTask.follow_user(user, uid)
        group_id = await UtilsTask.fetch_group_id(user, '抽奖关注')
        await UtilsTask.move2follow_group(user, uid, group_id)
        return

    @staticmethod
    async def unfollow_raffle_organizer(user, uid):
        user.info([f'正在处理动态抽奖的取关问题'], True)
        group_id = await UtilsTask.fetch_group_id(user, '抽奖关注')
        is_following, group_ids = await UtilsTask.check_follow(user, uid)
        if group_id in group_ids:
            await UtilsTask.unfollow(user, uid)

    @staticmethod
    async def join(user, dyn_raffle_status: DynRaffleStatus):
        async with user.repost_del_lock:
            if dyn_raffle_status.feed_limit:  # 关注
                await DynRaffleHandlerTask.follow_raffle_organizer(user, dyn_raffle_status.uid)

            # 创建动态并提交数据库
            if await DynRaffleHandlerTask.repost_dyn_raffle(user, dyn_raffle_status.dyn_id, dyn_raffle_status.at_num):
                user.info([f'转发参与动态{dyn_raffle_status.dyn_id}成功'], True)
                for i in range(5):  # 经常不能及时刷新
                    await asyncio.sleep(3)
                    dyn_id = await DynRaffleHandlerTask.fetch_reposted_dynid(user, user.dict_bili['uid'], dyn_raffle_status.dyn_id)
                    if dyn_id is not None:
                        user.info([f'查找转发动态{dyn_raffle_status.dyn_id}生成{dyn_id}'], True)
                        dyn_raffle_joined = DynRaffleJoined(dyn_id=dyn_id, orig_dynid=dyn_raffle_status.dyn_id, uid=user.dict_bili['uid'])
                        print(dyn_raffle_joined)
                        dyn_raffle_sql.insert_dynraffle_joined_table(dyn_raffle_joined)
                        return
                user.warn(f'查找转发动态{dyn_raffle_status.dyn_id}生成失败')
            else:
                user.warn(f'转发参与动态{dyn_raffle_status.dyn_id}失败')
            return

    @staticmethod
    async def notice(user, dyn_raffle_status: DynRaffleStatus, dyn_raffle_results: Optional[DynRaffleResults], all_done_future=None):
        int_user_uid = int(user.dict_bili['uid'])
        async with user.repost_del_lock:
            dyn_raffle_joined = dyn_raffle_sql.select_by_primary_key_from_dynraffle_joined_table(
                uid=int_user_uid, orig_dynid=dyn_raffle_status.dyn_id)

            if dyn_raffle_joined is None:
                user.info(['未从数据库中查阅到动态抽奖，可能是之前已经删除了'], True)
                return

            if dyn_raffle_results is None or \
                    int_user_uid not in dyn_raffle_results.prize_list_1st and \
                    int_user_uid not in dyn_raffle_results.prize_list_2nd and \
                    int_user_uid not in dyn_raffle_results.prize_list_3rd:
                # 删除动态，并且同步数据库
                await DynRaffleHandlerTask.del_dyn_by_dynid(user, dyn_raffle_joined.dyn_id)
                dyn_raffle_sql.del_from_dynraffle_joind_table(
                    uid=int_user_uid,
                    orig_dynid=dyn_raffle_status.dyn_id
                )

                # 如果本抽奖需要关注且up主的其他抽奖不再需要关注/up主不再有其他抽奖，就运行unfollow_raffle_organizer
                if dyn_raffle_status.feed_limit and dyn_raffle_sql.should_unfollowed(
                        uid=int_user_uid, orig_uid=dyn_raffle_status.uid):
                    await DynRaffleHandlerTask.unfollow_raffle_organizer(user, dyn_raffle_status.uid)
            else:
                dyn_raffle_sql.del_from_dynraffle_joind_table(
                    uid=int_user_uid,
                    orig_dynid=dyn_raffle_status.dyn_id
                )
                following_uid = dyn_raffle_status.uid if dyn_raffle_status.feed_limit else 0
                dyn_raffle_sql.insert_dynraffle_luckydog_table(DynRaffleLuckydog(
                    uid=dyn_raffle_joined.uid,
                    dyn_id=dyn_raffle_joined.dyn_id,
                    orig_dynid=dyn_raffle_joined.orig_dynid,
                    following_uid=following_uid
                ))

        if dyn_raffle_sql.should_del_from_dynraffle_status_table(dyn_raffle_status.dyn_id):
            dyn_raffle_sql.del_from_dynraffle_status_table(dyn_raffle_status.dyn_id)
            if all_done_future is not None:
                all_done_future.set_result(True)
