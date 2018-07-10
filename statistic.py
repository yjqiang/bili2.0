class Statistics:
    __slots__ = ('result', 'pushed_raffle', 'joined_raffle')

    def __init__(self):
        self.pushed_raffle = {}
        self.joined_raffle = {}
        self.result = {}
        
    def add_to_result(self, type, num):
        self.result[type] = self.result.get(type, 0) + int(num)

    def getlist(self):
        for k, v in self.pushed_raffle.items():
            print(f'本次推送{k}次数: {v}')
        print()
        for k, v in self.joined_raffle.items():
            print(f'本次参与{k}次数: {v}')

    def getresult(self):
        print('本次参与抽奖结果为：')
        for k, v in self.result.items():
            print(f'{k}X{v}')

    def append_to_activitylist(self):
        self.append2joined_raffle('活动(合计)')

    def append_to_TVlist(self):
        self.append2joined_raffle('电视(合计)')
        
    def append_to_captainlist(self):
        self.append2joined_raffle('总督(合计)')
        
    def append2joined_raffle(self, type, num=1):
        self.joined_raffle[type] = self.joined_raffle.get(type, 0) + int(num)
        
    def append2pushed_raffle(self, type, area_id=0, num=1):
        if '摩天' in type:
            self.pushed_raffle[type] = self.pushed_raffle.get(type, 0) + int(num)
        elif area_id == 1:
            self.pushed_raffle[type] = self.pushed_raffle.get(type, 0) + int(num)
                    
