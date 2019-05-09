from typing import Optional

from reqs.substance_raffle_handler import SubstanceRaffleHandlerReq
import utils
from substance import substance_raffle_sql
from substance.bili_data_types import (
    SubstanceRaffleStatus,
    SubstanceRaffleJoined,
    SubstanceRaffleResults,
    SubstanceRaffleLuckydog,
)
from .task_func_decorator import normal
from .base_class import ForcedTask


class SubstanceRaffleUtilsTask:
    @staticmethod
    async def fetch_substance_raffle_results(
            user, substance_raffle_status: SubstanceRaffleStatus) -> Optional[SubstanceRaffleResults]:
        json_rsp = await user.req_s(
            SubstanceRaffleHandlerReq.notice, user, substance_raffle_status.aid, substance_raffle_status.number)
        assert not json_rsp['code']
        print(substance_raffle_status, json_rsp)
        list_winners = json_rsp['data']['winnerList']
        assert list_winners
        substance_raffle_results = SubstanceRaffleResults(
            aid=substance_raffle_status.aid,
            number=substance_raffle_status.number,
            describe=substance_raffle_status.describe,
            join_start_time=substance_raffle_status.join_start_time,
            join_end_time=substance_raffle_status.join_end_time,
            prize_cmt=substance_raffle_status.prize_cmt,
            prize_list=[int(winner['uid']) for winner in list_winners]
        )
        return substance_raffle_results

    @staticmethod
    async def check_and_fetch_raffle(user, aid):
        json_rsp = await user.req_s(SubstanceRaffleHandlerReq.check, user, aid)
        code = json_rsp['code']

        if not code:
            results = []
            title = json_rsp['data']['title']
            raffles = json_rsp['data']['typeB']
            for number, value in enumerate(raffles, start=1):
                join_end_time = value['join_end_time']
                join_start_time = value['join_start_time']
                prize_cmt = [raffle_result['jp_name'] for raffle_result in value['list']]
                substance_raffle_status = SubstanceRaffleStatus(
                    aid=aid,
                    number=number,
                    describe=title,
                    join_start_time=join_start_time,
                    join_end_time=join_end_time,
                    handle_status=-1,
                    prize_cmt=prize_cmt
                )
                results.append(substance_raffle_status)
            return 0, results
        elif code == -400:
            return 404, []
        # warn
        return -1, []

    @staticmethod
    async def check(user, aid):
        json_rsp = await user.req_s(SubstanceRaffleHandlerReq.check, user, aid)
        code = json_rsp['code']
        if not code:
            return True
        elif code == -400:
            return False
        user.warn([f'实物抽奖, {json_rsp}'], True)
        return False


class SubstanceRaffleJoinTask(ForcedTask):
    TASK_NAME = 'join_substance_raffle'
    @staticmethod
    async def check(_, *args):
        return (-2, None, *args),  # 参见notifier的特殊处理，为None就会依次处理，整个过程awaitable

    @staticmethod
    @normal
    async def work(user, substance_raffle_status: SubstanceRaffleStatus):
        if substance_raffle_status.join_end_time - utils.curr_time() < 10:
            user.infos([f'实物{substance_raffle_status.aid}马上或已经开奖，放弃参与'])
        json_rsp = await user.req_s(
            SubstanceRaffleHandlerReq.join, user, substance_raffle_status.aid, substance_raffle_status.number)
        user.infos([f'参与实物抽奖回显：{json_rsp}'])
        # 如果返回小黑屋，假设小黑屋可能持续较久，所以不会再尝试了
        if not json_rsp['code']:
            substance_raffle_joined = SubstanceRaffleJoined(
                uid=user.dict_bili['uid'],
                aid=substance_raffle_status.aid,
                number=substance_raffle_status.number
            )
            print(substance_raffle_joined)
            substance_raffle_sql.insert_substanceraffle_joined_table(substance_raffle_joined)


class SubstanceRaffleNoticeTask(ForcedTask):
    @staticmethod
    async def check(_, *args):
        return (-2, None, *args),  # 参见notifier的特殊处理，为None就会依次处理，整个过程awaitable

    @staticmethod
    @normal
    async def work(
            user,  substance_raffle_status: SubstanceRaffleStatus,
            substance_raffle_result: Optional[SubstanceRaffleResults]):
        int_user_uid = int(user.dict_bili['uid'])
        dyn_raffle_joined = substance_raffle_sql.select_by_primary_key_from_substanceraffle_joined_table(
            uid=int_user_uid, aid=substance_raffle_status.aid, number=substance_raffle_status.number)

        if dyn_raffle_joined is None:
            user.infos(['未从数据库中查阅到动态抽奖，可能是之前已经删除了'])

        elif substance_raffle_result is None or \
                int_user_uid not in substance_raffle_result.prize_list:
            # 删除动态，并且同步数据库
            substance_raffle_sql.del_from_substanceraffle_joind_table(
                uid=int_user_uid,
                aid=substance_raffle_status.aid,
                number=substance_raffle_status.number
            )
        else:
            substance_raffle_sql.del_from_substanceraffle_joind_table(
                uid=int_user_uid,
                aid=substance_raffle_status.aid,
                number=substance_raffle_status.number
            )

            substance_raffle_sql.insert_substanceraffle_luckydog_table(SubstanceRaffleLuckydog(
                uid=dyn_raffle_joined.uid,
                aid=substance_raffle_status.aid,
                number=substance_raffle_status.number
            ))
