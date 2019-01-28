from reqs.substance_raffle_handler import SubstanceRaffleHandlerReq
from utils import curr_time


class SubstanceRaffleHandlerTask:
    @staticmethod
    def target(step):
        if step == 0:
            return SubstanceRaffleHandlerTask.check
        if step == 1:
            return SubstanceRaffleHandlerTask.join
        return None
        
    # aid 有点类似于roomid
    @staticmethod
    async def check(user, aid):
        json_rsp = await user.req_s(SubstanceRaffleHandlerReq.check, user, aid)
        print('id对应code数值为', json_rsp['code'], aid)
        blacklist = ['test', 'TEST', '测试', '加密']
        next_step_settings = []
        # -400 不存在
        if not json_rsp['code']:
            temp = json_rsp['data']['title']
            if any(word in temp for word in blacklist):
                print("检测到疑似钓鱼类测试抽奖，默认不参与，请自行判断抽奖可参与性")
            else:
                raffles = json_rsp['data']['typeB']
                for num, value in enumerate(raffles):
                    join_end_time = value['join_end_time']
                    join_start_time = value['join_start_time']
                    ts = curr_time()
                    if int(join_end_time) > ts > int(join_start_time):
                        print('本次获取到的抽奖id为', num, aid)
                        max_wait = min(60, int(join_end_time) - ts)
                        next_step_setting = (1, (0, max_wait), -2, aid, num)
                        next_step_settings.append(next_step_setting)
                    if ts < int(join_start_time):
                        print('即将参加的id', num, aid)
        return next_step_settings

    @staticmethod
    async def join(user, aid, num):
        json_rsp = await user.req_s(SubstanceRaffleHandlerReq.join, user, aid, num)
        user.info([f'参与实物抽奖回显：{json_rsp}'], True)
        
    @staticmethod
    async def check_code(user, aid):
        json_rsp = await user.req_s(SubstanceRaffleHandlerReq.check, user, aid)
        # print(aid, json_rsp)
        return json_rsp['code']
        
