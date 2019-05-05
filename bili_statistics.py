class BiliStatistics:
    LIST_SIZE_LIMITED = 1000
    CLEAN_LIST_CYCLE = 350
    
    def __init__(self, area_num=0):
        self.area_num = area_num
        # 只有一个(可以认为id为-1的super user)
        self.pushed_raffles = {}
        
        # 每个用户一个小dict
        self.joined_raffles = {}
        self.raffle_results = {}
        
        # 这是用于重复问题
        self.raffle_ids = []

    def init(self, area_num: int):
        self.area_num = area_num
        
    def print_statistics(self, user_id):
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
            self.__print_one_stats(user_id)
    
    def __print_one_stats(self, user_id):
        print('本次参与抽奖统计：')
        joined_of_id = self.joined_raffles.get(user_id, {})
        for k, v in joined_of_id.items():
            print(f'{v:^5} X {k}')
        print()
            
        print('本次抽奖结果统计：')
        results_of_id = self.raffle_results.get(user_id, {})
        for k, v in results_of_id.items():
            print(f'{v:^5} X {k}')
            
    def add2pushed_raffles(self, raffle_name, broadcast_type, num):
        orig_num = self.pushed_raffles.get(raffle_name, 0)
        # broadcast_type 0全区 1分区 2本房间
        if broadcast_type == 0:
            self.pushed_raffles[raffle_name] = orig_num + num / self.area_num
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
    def add2raffle_ids(self, raffle_id):
        self.raffle_ids.append(raffle_id)
        # 定期清理，防止炸掉
        if len(self.raffle_ids) > self.CLEAN_LIST_CYCLE+self.LIST_SIZE_LIMITED:
            del self.raffle_ids[:self.CLEAN_LIST_CYCLE]
            # print(self.raffle_ids)
    
    def is_raffleid_duplicate(self, raffle_id):
        return raffle_id in self.raffle_ids

                
var_bili_statistics = BiliStatistics()


def init(*args, **kwargs):
    var_bili_statistics.init(*args, **kwargs)
    

def add2pushed_raffles(raffle_name, broadcast_type=0, num=1):
    var_bili_statistics.add2pushed_raffles(raffle_name, broadcast_type, int(num))
        
        
def add2joined_raffles(raffle_name, user_id, num=1):
    var_bili_statistics.add2joined_raffles(raffle_name, user_id, int(num))
 
       
def add2results(gift_name, user_id, num=1):
    var_bili_statistics.add2results(gift_name, user_id, int(num))
    

def add2raffle_ids(raffle_id):
    var_bili_statistics.add2raffle_ids(int(raffle_id))
    
    
def is_raffleid_duplicate(raffle_id):
    return var_bili_statistics.is_raffleid_duplicate(int(raffle_id))
    

def print_statistics(user_id=None):
    var_bili_statistics.print_statistics(user_id)
