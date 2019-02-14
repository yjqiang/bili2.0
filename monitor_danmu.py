import aiohttp
from danmu import DanmuPrinter, DanmuRaffleHandler, YjMonitorHandler


class DanmuMonitor:
    def __init__(self):
        self._session = None
        self.danmu_printer = None
        
    @property
    def session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session
        
    async def run_danmu_printer(self, room_id):
        self.danmu_printer = DanmuPrinter(room_id, -1, self.session)
        await self.danmu_printer.run_forever()
        
    async def run_danmu_raffle_handler(self, area_id):
        await DanmuRaffleHandler(0, area_id, self.session).run_forever()
        
    async def run_yjraffle_monitor(self, room_id):
        if room_id:
            await YjMonitorHandler(room_id, 0, self.session).run_forever()
            
            
danmu_monitor = DanmuMonitor()


async def reconnect_danmu(real_roomid):
    if danmu_monitor.danmu_printer is None:
        return
    await danmu_monitor.danmu_printer.reconnect(real_roomid)
    
async def run_danmu_printer(room_id):
    await danmu_monitor.run_danmu_printer(room_id)
    
async def run_danmu_raffle_handler(area_id):
    await danmu_monitor.run_danmu_raffle_handler(area_id)
        
async def run_yjraffle_monitor(room_id):
    await danmu_monitor.run_yjraffle_monitor(room_id)
