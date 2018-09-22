from bili_user.base_user import BaseUser
import time
from task import Task


class JoinRaffleUser(BaseUser):
    async def handle_1_substantial_raffle(self, i, g):
        json_response1 = await self.online_request(self.webhub.get_gift_of_lottery, i, g)
        print("当前时间:", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        print("参与实物抽奖回显：", json_response1)
        
    async def check_tv_result(self, raffleid, real_roomid):
        json_response = await self.online_request(self.webhub.get_TV_result, real_roomid, raffleid)
        # print(json_response)
        if not json_response['code']:
            # {'code': 0, 'msg': '正在抽奖中..', 'message': '正在抽奖中..', 'data': {'gift_id': '-1', 'gift_name': '', 'gift_num': 0, 'gift_from': '', 'gift_type': 0, 'gift_content': '', 'status': 3}}
            if json_response['data']['gift_id'] == '-1':
                print([f'json_response'], True)
                return
            elif json_response['data']['gift_id'] != '-1':
                data = json_response['data']
                self.printer_with_id([f'# 房间{real_roomid:^9}道具抽奖结果: {data["gift_name"]}X{data["gift_num"]}'], True)
                self.statistics.add_to_result(data['gift_name'], int(data['gift_num']))
        
    async def handle_1_TV_raffle(self, real_roomid, raffleid, raffle_type):
        print('参与', raffleid)
        json_response2 = await self.online_request(self.webhub.get_gift_of_TV, real_roomid, raffleid)
        self.statistics.append_to_TVlist()
        self.printer_with_id([f'参与了房间{real_roomid:^9}的道具抽奖'], True)
        self.printer_with_id([f'# 道具抽奖状态: {json_response2["msg"]}'])
        # -400不存在
        # -500繁忙
        code = json_response2['code']
        if not code:
            # Statistics.append_to_TVlist(raffleid, real_roomid)
            Task().call_after('check_tv_result', 190, (raffleid, real_roomid), id=self.user_id)
            return True
        elif code == -500:
            print('# -500繁忙，稍后重试')
            return False
        elif code == 400:
            self.fall_in_jail()
            return False
        else:
            print(json_response2)
            return True
                
    async def handle_1_guard_raffle(self, roomid, raffleid):
        json_response2 = await self.online_request(self.webhub.get_gift_of_guard, roomid, raffleid)
        print(json_response2)
        if not json_response2['code']:
            print("# 获取到房间 %s 的总督奖励: " % (roomid), json_response2['data']['message'])
            # print(json_response2)
            self.statistics.append_to_guardlist()
        else:
            print(json_response2)
        return True
                                                
    async def handle_1_activity_raffle(self, room_id, text2, raffleid):
        # print('参与')
        json_response1 = await self.online_request(self.webhub.get_gift_of_events_app, room_id, text2, raffleid)
        json_pc_response = await self.online_request(self.webhub.get_gift_of_events_web, room_id, text2, raffleid)
        
        self.printer_with_id([f'参与了房间{room_id:^9}的活动抽奖'], True)
    
        if not json_response1['code']:
            self.printer_with_id([f'# 移动端活动抽奖结果: {json_response1["data"]["gift_desc"]}'])
            self.statistics.add_to_result(*(json_response1['data']['gift_desc'].split('X')))
        else:
            print(json_response1)
            self.printer_with_id([f'# 移动端活动抽奖结果: {json_response1}'])
            
        self.printer_with_id(
                [f'# 网页端活动抽奖状态:  {json_pc_response}'])
        if not json_pc_response['code']:
            self.statistics.append_to_activitylist()
        else:
            print(json_pc_response)
        return True
    
    async def post_watching_history(self, roomid):
        await self.online_request(self.webhub.post_watching_history, roomid)

