import asyncio
import random
import aiohttp


class Host():
    instance = None
        
    def __new__(cls):
        if not cls.instance:
            cls.instance = super(Host, cls).__new__(cls)
            cls.instance.list_ips = [
                "14.136.134.86",
                "14.136.134.87",
                "27.221.61.100",
                "27.221.61.109",
                "47.88.107.100",
                "47.88.138.238",
                "47.90.50.109",
                "47.90.207.174",
                "47.91.19.168",
                "47.91.74.133",
                "58.222.35.202",
                "58.222.35.205",
                "101.75.240.7",
                "101.200.58.11",
                "110.80.129.143",
                "111.19.137.164",
                "111.230.84.45",
                "111.230.84.59",
                "111.230.85.89",
                "111.231.211.246",
                "111.231.212.88",
                "112.117.218.167",
                "113.113.80.9",
                "113.207.83.212",
                "114.80.223.177",
                "116.207.118.12",
                "118.89.74.45",
                "118.89.74.220",
                "120.41.32.15",
                "120.92.78.97",
                "120.92.113.99",
                "120.92.174.135",
                "120.92.218.109",
                "120.192.82.106",
                "120.221.74.132",
                "120.221.74.135",
                "122.143.15.150",
                "122.228.77.85",
                "123.206.1.201",
                "140.143.82.138",
                "140.143.177.142",
                "140.249.9.4",
                "140.249.9.7",
                "211.159.214.11",
                "218.98.33.197",
                "223.85.58.74"
                ]
        return cls.instance

    async def test_proxy(self, ip):
        # url = 'http://api.github.com/events'
        url = f'http://{ip}/room/v1/Room/room_init?id=6'
        headers = {'host': 'api.live.bilibili.com'}
        async with aiohttp.ClientSession() as session:
            num_won = 0
            for i in range(10):
                try:
                    rsp = await session.get(url, headers=headers, timeout=1)
                    if rsp.status == 200:
                        num_won += 1
                except:
                    print('fail ip', ip)
        if num_won >= 8:
            return True
        return False
    
    async def proxies_filter(self):
        tasklist = []
        for ip in self.list_ips:
            task = asyncio.ensure_future(self.test_proxy(ip))
            tasklist.append(task)
        results = await asyncio.gather(*tasklist)
        self.list_ips = [ip for ip, tag in zip(self.list_ips, results) if tag]
        print(len(self.list_ips))
        
    def get_host(self):
        return random.choice(self.list_ips)
    


