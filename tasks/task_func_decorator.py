import asyncio

from decorator import decorator

from printer import info as print


@decorator
async def unique(func, *args, **kwargs):
    user, *args = args
    if func in user.recording_tasks:
        status = user.recording_tasks[func]
    else:
        status = {}
        user.recording_tasks[func] = status
    if 'finish_time' not in status or status['finish_time']:
        status['finish_time'] = 0  # 0 表示开始且未完成
        status['start_time'] = 1
        try:
            result = await func(user, *args, **kwargs)
            status['finish_time'] = 1  # 1 表示结束
            return result
        except asyncio.CancelledError:
            print(f'❌取消正在进行的{func}任务')
            status['finish_time'] = -1  # -1 表示取消了
    else:
        print(f'重复推送{func}（此为debug信息忽略即可）')
    return None
    
    
@decorator
async def normal(func, *args, **kwargs):
    user, *args = args
    try:
        return await func(user, *args, **kwargs)
    except asyncio.CancelledError:
        return None
