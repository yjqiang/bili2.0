from bili_user.base_user import BaseUser
import time
from task import Task
import bili_stats


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
                self.printer_with_id([f'# 房间{real_roomid:^9}小电视抽奖结果: {data["gift_name"]}X{data["gift_num"]}'], True)
                bili_stats.add2results(data['gift_name'], self.user_id, data['gift_num'])
        
    async def handle_1_TV_raffle(self, real_roomid, raffleid, raffle_type):
        print('参与', raffleid)
        json_response2 = await self.online_request(self.webhub.get_gift_of_TV, real_roomid, raffleid)
        bili_stats.add2joined_raffles('小电视(合计)', self.user_id)
        self.printer_with_id([f'参与了房间{real_roomid:^9}的小电视抽奖'], True)
        self.printer_with_id([f'# 小电视抽奖状态: {json_response2["msg"]}'])
        # -400不存在
        # -500繁忙
        code = json_response2['code']
        if not code:
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
        self.printer_with_id([f'参与了房间{roomid:^9}的大航海抽奖'], True)
        if not json_response2['code']:
            self.printer_with_id([f'# 房间{roomid:^9}大航海抽奖结果: {json_response2["data"]["message"]}'])
            bili_stats.add2joined_raffles('大航海(合计)', self.user_id)
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
            gift_name, gift_num = json_response1['data']['gift_desc'].split('X')
            bili_stats.add2results(gift_name, self.user_id, gift_num)
        else:
            print(json_response1)
            self.printer_with_id([f'# 移动端活动抽奖结果: {json_response1}'])
            
        self.printer_with_id(
                [f'# 网页端活动抽奖状态:  {json_pc_response}'])
        if not json_pc_response['code']:
            bili_stats.add2joined_raffles('活动(合计)', self.user_id)
        else:
            print(json_pc_response)
        return True
    
    async def post_watching_history(self, roomid):
        await self.online_request(self.webhub.post_watching_history, roomid)

