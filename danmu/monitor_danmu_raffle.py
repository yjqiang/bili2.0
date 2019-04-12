import asyncio
import aiohttp


from .bili_danmu_monitor import DanmuPrinter, DanmuRaffleMonitor
from .yj_monitor import YjMonitorDanmu, TcpYjMonitorClient
from . import raffle_handler


async def run_danmu_monitor(
        raffle_danmu_areaids,
        yjmonitor_danmu_roomid,
        printer_danmu_roomid,
        yjmonitor_tcp_addr,
        yjmonitor_tcp_key,
        future=None
        ):
    session = aiohttp.ClientSession()

    tasks = [asyncio.ensure_future(raffle_handler.run())]
    for area_id in raffle_danmu_areaids:
        task = asyncio.ensure_future(
            DanmuRaffleMonitor(
                room_id=0,
                area_id=area_id,
                session=session).run_forever())
        tasks.append(task)
        
    if yjmonitor_danmu_roomid:
        task = asyncio.ensure_future(
            YjMonitorDanmu(
                room_id=yjmonitor_danmu_roomid,
                area_id=0,
                session=session).run_forever())
        tasks.append(task)
    elif yjmonitor_tcp_key:
        task = asyncio.ensure_future(
            TcpYjMonitorClient(
                key=yjmonitor_tcp_key,
                url=yjmonitor_tcp_addr,
                area_id=0).run_forever())
        tasks.append(task)
    
    printer_danmu = DanmuPrinter(
        room_id=printer_danmu_roomid,
        area_id=-1,
        session=session)
    if future is not None:
        future.set_result(printer_danmu)
    task = asyncio.ensure_future(
            printer_danmu.run_forever())
    tasks.append(task)
    
    await asyncio.wait(tasks)
