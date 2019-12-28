from reqs.manga_daily_job import (
    MangaSignReq,
    ShareComicReq
)
from .base_class import Sched, DontWait, Unique


class MangaSignTask(Sched, DontWait, Unique):
    TASK_NAME = 'manga_sign'

    @staticmethod
    async def check(_):
        return (-2, (0, 3)),

    @staticmethod
    async def work(user):
        json_rsp = await user.req_s(MangaSignReq.sign, user)
        if not json_rsp['code']:
            user.info('漫画每日签到')
        else:
            user.info(f'漫画每日签到可能重复执行 {json_rsp}')


class ShareComicTask(Sched, DontWait, Unique):
    TASK_NAME = 'share_comic'

    @staticmethod
    async def check(_):
        return (-2, (0, 3)),

    @staticmethod
    async def work(user):
        json_rsp = await user.req_s(ShareComicReq.share_comic, user)
        if not json_rsp['code']:
            user.info('漫画每日分享')
        else:
            user.info(f'漫画每日分享可能重复执行 {json_rsp}')
