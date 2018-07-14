import asyncio
import random
import aiohttp


class Host():
    instance = None
        
    def __new__(cls, ips=None):
        if not cls.instance:
            cls.instance = super(Host, cls).__new__(cls)
            cls.instance.list_ips = ips
               
        return cls.instance

    async def test_proxy(self, ip):
        url = f'http://{ip}/room/v1/Room/room_init?id=6'
        # url = f'http://{ip}/gift/v3/live/gift_config'
        headers = {'host': 'api.live.bilibili.com'}
        timeout = aiohttp.ClientTimeout(total=1.5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            num_won = 0
            for i in range(10):
                try:
                    rsp = await session.get(url, headers=headers)
                    if rsp.status == 200:
                        num_won += 1
                except:
                    print('fail ip', ip)
        if num_won >= 9:
            return True
        return False
    
    async def proxies_filter(self):
        tasklist = []
        for ip in self.list_ips:
            task = asyncio.ensure_future(self.test_proxy(ip))
            tasklist.append(task)
        results = await asyncio.gather(*tasklist)
        self.list_ips = list(set([ip for ip, tag in zip(self.list_ips, results) if tag]))
        self.list_ips.sort()
        print('可用ip为', len(self.list_ips), '个')
        
    def get_host(self):
        return random.choice(self.list_ips)
    

