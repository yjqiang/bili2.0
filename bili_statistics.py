from typing import Optional
from collections import deque

import attr

from utils import curr_time


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
    LIST_SIZE_LIMITED = 3000

    number = attr.ib(default=0, init=False)
    ids = attr.ib(init=False)

    @ids.default
    def _ids(self):
        return deque(maxlen=DuplicateChecker.LIST_SIZE_LIMITED)

    def add2checker(self, new_id: int, need_check_duplicated=True) -> bool:
        if need_check_duplicated and self.is_duplicated(new_id):
            return False
        self.number += 1
        self.ids.append(new_id)
        return True

    def is_duplicated(self, new_id: int):
        return new_id in self.ids

    def result(self):
        return f'一共 {self.number} 个几乎不重复的 id'


@attr.s(slots=True)
class UniqueTaskChecker:  # 准确的说是 task.work 的唯一性, task.check 不受控
    # 可以发现,UniqueTaskChecker 初始化是 cancel 状态，即可以成功 restart
    start_time = attr.ib(init=False, factory=curr_time)
    end_time = attr.ib(init=False, default=-1)

    # 已经 done 或 cancel 的 task，不需要删除该实例，下次用的时候 restart 一下就行
    # 负责检查是否重复并且如不重复，restart
    def restart(self) -> bool:
        if self.is_unique():
            self.start_time = curr_time()
            self.end_time = 0
            return True
        return False

    def cancel(self):
        self.end_time = -1

    def done(self):
        self.end_time = curr_time()

    def is_unique(self) -> bool:
        return bool(self.end_time)  # 非0


@attr.s(slots=True)
class UniqueTaskCheckers:
    records = attr.ib(init=False, factory=dict)

    def start(self, user_id, task) -> bool:
        records_of_user = self.records.setdefault(user_id, {})
        if task not in records_of_user:
            records_of_user[task] = UniqueTaskChecker()
        unique_task_checker = records_of_user[task]
        return unique_task_checker.restart()

    def cancel(self, user_id, task):
        self.records[user_id][task].cancel()

    def done(self, user_id, task):
        self.records[user_id][task].done()


@attr.s(slots=True)
class MaxTimeTaskChecker:  # 准确的说是task.work的唯一性, task.check不受控
    num = attr.ib(init=False, default=0)

    # 负责检查是否重复并且如不重复，restart
    def add(self, max_time) -> bool:
        if self.is_addable(max_time):
            self.num += 1
            return True
        return False

    def is_addable(self, max_time) -> bool:
        if max_time == -1 or self.num < max_time:  # -1 特殊处理，表示无限参与
            return True
        return False


@attr.s(slots=True)
class MaxTimeTaskCheckers:
    records = attr.ib(init=False, factory=dict)

    def add(self, user_id, task, max_time) -> bool:
        records_of_user = self.records.setdefault(user_id, {})
        if task not in records_of_user:
            records_of_user[task] = MaxTimeTaskChecker()
        max_time_task_checker = records_of_user[task]
        return max_time_task_checker.add(max_time)

    def clear(self):
        self.records.clear()


class BiliStatistics:
    __slots__ = (
        'area_num', 'area_duplicated', 'pushed_raffles',
        'joined_raffles', 'raffle_results',
        'danmu_raffleid_checker', 'cover_checker0', 'cover_checker1',
        'max_time_task_checkers', 'unique_task_checkers'
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
        self.max_time_task_checkers = MaxTimeTaskCheckers()  # {use0: {task0: 1, task1: 2}, user1: {task1: 9}}
        # 用于限制用户不可同时参加某任务
        self.unique_task_checkers = UniqueTaskCheckers()

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
            print(self.max_time_task_checkers)
            print(self.unique_task_checkers)
            
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

    def add2max_time_task_checkers(self, user_id, task, max_time: int) -> bool:
        return self.max_time_task_checkers.add(user_id, task, max_time)

    def start_new_day(self):
        self.max_time_task_checkers.clear()

    def start_unique_task(self, user_id, task) -> bool:
        return self.unique_task_checkers.start(user_id, task)

    def cancel_unique_task(self, user_id, task):
        return self.unique_task_checkers.cancel(user_id, task)

    def done_unique_task(self, user_id, task):
        return self.unique_task_checkers.done(user_id, task)

                
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
    
    
def is_raffleid_duplicate(raffle_id):
    return var_bili_statistics.is_raffleid_duplicate(int(raffle_id))
    

def print_statistics(user_id=None):
    var_bili_statistics.print_statistics(user_id)


def add2max_time_task_checkers(user_id, task, max_time) -> bool:
    return var_bili_statistics.add2max_time_task_checkers(user_id, task, max_time)


def start_new_day():
    var_bili_statistics.start_new_day()


def start_unique_task(user_id, task) -> bool:
    return var_bili_statistics.start_unique_task(user_id, task)


def cancel_unique_task(user_id, task):
    var_bili_statistics.cancel_unique_task(user_id, task)


def done_unique_task(user_id, task):
    var_bili_statistics.done_unique_task(user_id, task)
