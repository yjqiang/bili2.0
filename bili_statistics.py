class BiliStatistics:
    def __init__(self, area_num=0):
        self.area_num = area_num
        # 只有一个(可以认为id为-1的super user)
        self.pushed_raffles = {}
        
        # 每个用户一个小dict
        self.joined_raffles = {}
        self.raffle_results = {}
        
        # 这是用于重复问题
        self.raffle_ids = []
        
    def print_statistics(self, id):
        print('本次推送抽奖统计：')
        for k, v in self.pushed_raffles.items():
            if isinstance(v, int):
                print(f'{v:^5} X {k}')
            else:
                print(f'{v:^5.2f} X {k}')
        print()
        
        if id == -2:
            print('暂时不支持全部打印，考虑到用户可能很多')
        else:
            self.__print_one_stats(id)
    
    def __print_one_stats(self, id):
        print('本次参与抽奖统计：')
        joined_of_id = self.joined_raffles.get(id, {})
        for k, v in joined_of_id.items():
            print(f'{v:^5} X {k}')
        print()
            
        print('本次抽奖结果统计：')
        results_of_id = self.raffle_results.get(id, {})
        for k, v in results_of_id.items():
            print(f'{v:^5} X {k}')
            
    def add2pushed_raffles(self, raffle_name, broadcast_type, num):
        orig_num = self.pushed_raffles.get(raffle_name, 0)
        # broadcast_type 0全区 1分区 2本房间
        if broadcast_type == 0:
            self.pushed_raffles[raffle_name] = orig_num + num / self.area_num
        else:
            self.pushed_raffles[raffle_name] = orig_num + num

    def add2joined_raffles(self, raffle_name, id, num):
        # 活动(合计)
        # 小电视(合计)
        # 大航海(合计)
        if id not in self.joined_raffles:
            self.joined_raffles[id] = {}
        raffles_of_id = self.joined_raffles[id]
        raffles_of_id[raffle_name] = raffles_of_id.get(raffle_name, 0) + num
            
    def add2results(self, gift_name, id, num=1):
        if id not in self.raffle_results:
            self.raffle_results[id] = {}
        results_of_id = self.raffle_results[id]
        results_of_id[gift_name] = results_of_id.get(gift_name, 0) + num
        
    # raffle_id int
    def add2raffle_ids(self, raffle_id):
        self.raffle_ids.append(raffle_id)
        # 定期清理，防止炸掉
        if len(self.raffle_ids) > 150:
            del self.raffle_ids[:75]
            # print(self.raffle_ids)
    
    def is_raffleid_duplicate(self, raffle_id):
        return (raffle_id in self.raffle_ids)

                
var = BiliStatistics()


def init_area_num(area_num):
    var.area_num = area_num
    

def add2pushed_raffles(raffle_name, broadcast_type=0, num=1):
    var.add2pushed_raffles(raffle_name, broadcast_type, int(num))
        
        
def add2joined_raffles(raffle_name, id, num=1):
    var.add2joined_raffles(raffle_name, id, int(num))
 
       
def add2results(gift_name, id, num=1):
    var.add2results(gift_name, id, int(num))
    

def add2raffle_ids(raffle_id):
    var.add2raffle_ids(int(raffle_id))
    
    
def is_raffleid_duplicate(raffle_id):
    return var.is_raffleid_duplicate(int(raffle_id))
    

def print_statistics(id=None):
    var.print_statistics(id)
