import sys
import asyncio
from typing import Any

import aiohttp

import printer
from exceptions import LogoutError, ForbiddenError
from json_rsp_ctrl import Ctrl, JsonRspType, TMP_DEFAULT_CTRL

sem = asyncio.Semaphore(3)


class WebSession:
    __slots__ = ('var_session',)

    def __init__(self):
        self.var_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=4))

    @staticmethod
    async def __receive_json(rsp: aiohttp.ClientResponse):
        return await rsp.json(content_type=None)

    @staticmethod
    async def __receive_str(rsp: aiohttp.ClientResponse):
        return await rsp.text()

    @staticmethod
    async def __receive_bytes(rsp: aiohttp.ClientResponse):
        return await rsp.read()

    # 基本就是通用的 request
    async def __orig_req(self, parse_rsp, method, url, **kwargs):
        i = 0
        while True:
            i += 1
            if i >= 10:
                printer.warn(f'反复请求多次未成功, {url}, {kwargs}')
            try:
                async with self.var_session.request(method, url, **kwargs) as rsp:
                    if rsp.status == 200:
                        body = await parse_rsp(rsp)
                        if body:
                            return body
            except asyncio.CancelledError:
                raise
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
            await asyncio.sleep(0.02)

    async def orig_req_json(self,
                            method,
                            url,
                            **kwargs) -> Any:
        return await self.__orig_req(self.__receive_json, method, url, **kwargs)

    # 为 bilibili 这边加了一些东西的 request
    async def __req(self, parse_rsp, method, url, **kwargs):
        async with sem:
            i = 0
            while True:
                i += 1
                if i >= 10:
                    printer.warn(f'反复请求多次未成功, {url}, {kwargs}')
                try:
                    async with self.var_session.request(method, url, **kwargs) as rsp:
                        if rsp.status == 200:
                            body = await parse_rsp(rsp)
                            if body:  # 有时候是 None 或空，直接屏蔽。read 或 text 类似，禁止返回空的东西
                                return body
                        elif rsp.status in (412, 403):
                            printer.warn(f'403频繁, {url}, {kwargs}')
                            raise ForbiddenError(msg=url)
                except asyncio.CancelledError:
                    raise
                except ForbiddenError:
                    raise
                except:
                    # print('当前网络不好，正在重试，请反馈开发者!!!!')
                    print(sys.exc_info()[0], sys.exc_info()[1], url)
                await asyncio.sleep(0.02)

    # is_login 后期移除
    async def request_json(self,
                           method,
                           url,
                           is_login=False,
                           ctrl: Ctrl = TMP_DEFAULT_CTRL,
                           **kwargs) -> dict:
        while True:
            body = await self.__req(self.__receive_json, method, url, **kwargs)
            if not isinstance(body, dict):  # 这里是强制定制的，与b站配合的！！！！
                continue
            json_rsp_type = ctrl.verify(body)
            if json_rsp_type == JsonRspType.OK:
                return body
            elif json_rsp_type == JsonRspType.IGNORE:
                await asyncio.sleep(1.0)
            elif json_rsp_type == JsonRspType.LOGOUT:
                print('api提示没有登录')
                print(body)
                if not is_login:
                    raise LogoutError(msg='提示没有登陆')
                else:
                    return body

    async def request_binary(self,
                             method,
                             url,
                             **kwargs) -> bytes:
        return await self.__req(self.__receive_bytes, method, url, **kwargs)

    async def request_text(self,
                           method,
                           url,
                           **kwargs) -> str:
        return await self.__req(self.__receive_str, method, url, **kwargs)
