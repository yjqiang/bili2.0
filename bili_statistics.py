from typing import Optional

import attr


@attr.s(slots=True)
class CoverChecker:
    number = attr.ib(
        default=0,
        validator=attr.validators.instance_of(int))
    min_id = attr.ib(
        default=-1,
        validator=attr.validators.instance_of(int))
    max_id = attr.ib(
        default=-1,
        validator=attr.validators.instance_of(int))

    # 只添加,不管重复性
    def add2checker(self, new_id: int):
        if self.min_id == -1 and self.max_id == -1:
            self.min_id = new_id
            self.max_id = new_id
            self.number += 1
            return
        if self.min_id < new_id:  # 过滤掉过老的id
            self.min_id = min(self.min_id, new_id)
            self.max_id = max(self.max_id, new_id)
            self.number += 1

    def result(self):
        if self.min_id == -1 and self.max_id == -1:
            num_wanted = 0
            num_actual = 0
            cover = 0
        else:
            num_wanted = self.max_id - self.min_id + 1
            num_actual = self.number
            cover = num_actual / num_wanted
        return f'覆盖率为 {num_actual} / {num_wanted} = {cover * 100:.2f}%'


@attr.s(slots=True)
class DuplicateChecker:
    LIST_SIZE_LIMITED = 1500
    CLEAN_LIST_CYCLE = 350

    number = attr.ib(
        default=0,
        validator=attr.validators.instance_of(int))
    ids = attr.ib(
        factory=list,
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(int),
            iterable_validator=attr.validators.instance_of(list)))

    def add2checker(self, new_id: int, need_check_duplicated=True) -> bool:
        if need_check_duplicated and self.is_duplicated(new_id):
            return False
        self.number += 1
        self.ids.append(new_id)
        # 定期清理，防止炸掉
        if len(self.ids) > self.CLEAN_LIST_CYCLE + self.LIST_SIZE_LIMITED:
            del self.ids[:self.CLEAN_LIST_CYCLE]
        return True

    def is_duplicated(self, new_id: int):
        return new_id in self.ids

    def result(self):
        return f'一共 {self.number} 个几乎不重复的 id'


class BiliStatistics:
    __slots__ = (
        'area_num', 'area_duplicated', 'pushed_raffles',
        'joined_raffles', 'raffle_results',
        'danmu_raffleid_checker', 'cover_checker0', 'cover_checker1', 'tasks_records',
    )

    def __init__(self, area_num=0):
        self.area_num = area_num
        self.area_duplicated = False
        # 只有一个(可以认为id为-1的super user)
        self.pushed_raffles = {}
        
        # 每个用户一个小dict
        self.joined_raffles = {}
        self.raffle_results = {}
        
        # 这是用于具体统计
        self.danmu_raffleid_checker = DuplicateChecker()
        self.cover_checker0 = CoverChecker()  # 舰队风暴遗漏统计
        self.cover_checker1 = CoverChecker()  # 小电视遗漏统计
        # 用于限制每天用户最多某个任务的最大参与次数
        self.tasks_records = {}  # {use0: {task0: 1, task1: 2}, user1: {task1: 9}}

    def init(self, area_num: int, area_duplicated: bool):
        self.area_num = area_num
        self.area_duplicated = area_duplicated
        
    def print_statistics(self, user_id):
        print('本次抽奖推送数据：')
        print(f'舰队风暴推送遗漏统计：{self.cover_checker0.result()}')
        print(f'小电视的推送遗漏统计：{self.cover_checker1.result()}')
        print(f'全部弹幕抽奖推送统计：{self.danmu_raffleid_checker.result()}')
        print()

        print('本次推送抽奖统计：')
        for k, v in self.pushed_raffles.items():
            if isinstance(v, int):
                print(f'{v:^5} X {k}')
            else:
                print(f'{v:^5.2f} X {k}')
        print()
        
        if user_id == -2:
            print('暂时不支持全部打印，考虑到用户可能很多')
        else:
            print('本次参与抽奖统计：')
            joined_of_id = self.joined_raffles.get(user_id, {})
            for k, v in joined_of_id.items():
                print(f'{v:^5} X {k}')
            print()

            print('本次抽奖结果统计：')
            results_of_id = self.raffle_results.get(user_id, {})
            for k, v in results_of_id.items():
                print(f'{v:^5} X {k}')
            print()

            print('当日参与任务统计（null类任务不计入；只是压入计划，不一定已经参与；整点清零）：')
            results_of_id = self.tasks_records.get(user_id, {})
            for k, v in results_of_id.items():
                print(f'{v:^5} X {k}')
            
    def add2pushed_raffles(self, raffle_name, broadcast_type, num):
        orig_num = self.pushed_raffles.get(raffle_name, 0)
        # broadcast_type 0全区 1分区 2本房间
        if broadcast_type == 0:
            self.pushed_raffles[raffle_name] = orig_num + num / self.area_num
        elif broadcast_type == 1 and self.area_duplicated:
            self.pushed_raffles[raffle_name] = orig_num + num / 2
        else:
            self.pushed_raffles[raffle_name] = orig_num + num

    def add2joined_raffles(self, raffle_name, user_id, num):
        # 活动(合计)
        # 小电视(合计)
        # 大航海(合计)
        if user_id not in self.joined_raffles:
            self.joined_raffles[user_id] = {}
        raffles_of_id = self.joined_raffles[user_id]
        raffles_of_id[raffle_name] = raffles_of_id.get(raffle_name, 0) + num
            
    def add2results(self, gift_name, user_id, num=1):
        if user_id not in self.raffle_results:
            self.raffle_results[user_id] = {}
        results_of_id = self.raffle_results[user_id]
        results_of_id[gift_name] = results_of_id.get(gift_name, 0) + num
        
    # raffle_id int
    def add2raffle_ids(self, raffle_id: int, raffle_type: Optional[str]):
        if raffle_type in ('STORM', 'GUARD'):
            self.cover_checker0.add2checker(raffle_id)
        elif raffle_type in ('TV',):
            self.cover_checker1.add2checker(raffle_id)
        self.danmu_raffleid_checker.add2checker(raffle_id, need_check_duplicated=False)
    
    def is_raffleid_duplicate(self, raffle_id: int):
        return self.danmu_raffleid_checker.is_duplicated(raffle_id)

    def add2tasks_records(self, task_name, user_id: int, max_time: int):
        if not max_time:  # 0显然就是一直不参与的
            return False
        if user_id not in self.tasks_records:
            self.tasks_records[user_id] = {}
        records_of_user = self.tasks_records[user_id]
        number = records_of_user.get(task_name, 0)
        if max_time != -1 and number >= max_time:  # -1 特殊处理，表示无限参与
            return False
        records_of_user[task_name] = number + 1
        return True

    def start_new_day(self):
        self.tasks_records.clear()

                
var_bili_statistics = BiliStatistics()


def init(*args, **kwargs):
    var_bili_statistics.init(*args, **kwargs)
    

def add2pushed_raffles(raffle_name, broadcast_type=0, num=1):
    var_bili_statistics.add2pushed_raffles(raffle_name, broadcast_type, int(num))
        
        
def add2joined_raffles(raffle_name, user_id, num=1):
    var_bili_statistics.add2joined_raffles(raffle_name, user_id, int(num))
 
       
def add2results(gift_name, user_id, num=1):
    var_bili_statistics.add2results(gift_name, user_id, int(num))
    

def add2raffle_ids(raffle_id, raffle_type: Optional[str] = None):
    var_bili_statistics.add2raffle_ids(int(raffle_id), raffle_type)


def add2tasks_records(task_name, user_id: int, max_time: int):
    return var_bili_statistics.add2tasks_records(task_name, user_id, max_time)
    
    
def is_raffleid_duplicate(raffle_id):
    return var_bili_statistics.is_raffleid_duplicate(int(raffle_id))
    

def print_statistics(user_id=None):
    var_bili_statistics.print_statistics(user_id)


def start_new_day():
    var_bili_statistics.start_new_day()
