import sys
import asyncio
import aiohttp
import printer
from exceptions import LogoutError, RspError
from json_rsp_ctrl import Ctrl, JsonRspType, DEFAULT_CTRL, TMP_DEFAULT_CTRL

sem = asyncio.Semaphore(3)


class WebSession:
    def __init__(self):
        self.var_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=4))

    @staticmethod
    async def __get_json_body(rsp):
        json_body = await rsp.json(content_type=None)
        return json_body

    @staticmethod
    async def __get_text_body(rsp):
        text = await rsp.text()
        return text

    @staticmethod
    async def __get_binary_body(rsp):
        return await rsp.read()

    # method 类似于aiohttp里面的对应method，目前只支持GET、POST
    # is_login后期移除，json这里应该与expected_code协同
    async def request_json(self,
                           method,
                           url,
                           is_login=False,
                           ctrl: Ctrl = TMP_DEFAULT_CTRL,
                           **kwargs) -> dict:
        async with sem:
            i = 0
            while True:
                i += 1
                if i >= 10:
                    printer.warn(url)
                try:
                    async with self.var_session.request(method, url, **kwargs) as rsp:
                        if rsp.status == 200:
                            json_body = await self.__get_json_body(rsp)
                            if json_body:  # 有时候是None或空，直接屏蔽。下面的read/text类似，禁止返回空的东西
                                json_rsp_type = ctrl.verify(json_body)
                                if json_rsp_type == JsonRspType.OK:
                                    return json_body
                                elif json_rsp_type == JsonRspType.IGNORE:
                                    await asyncio.sleep(1.0)
                                elif json_rsp_type == JsonRspType.LOGOUT:
                                    print('api提示没有登录')
                                    print(json_body)
                                    if not is_login:
                                        raise LogoutError(msg='提示没有登陆')
                                    else:
                                        return json_body
                        elif rsp.status == 403:
                            printer.warn(f'403频繁, {url}')
                            await asyncio.sleep(240)
                except RspError:
                    raise
                except:
                    # print('当前网络不好，正在重试，请反馈开发者!!!!')
                    print(sys.exc_info()[0], sys.exc_info()[1], url)
                await asyncio.sleep(0.02)

    async def request_binary(self,
                             method,
                             url,
                             **kwargs) -> bytes:
        async with sem:
            i = 0
            while True:
                i += 1
                if i >= 10:
                    printer.warn(url)
                try:
                    async with self.var_session.request(method, url, **kwargs) as rsp:
                        if rsp.status == 200:
                            binary_body = await self.__get_binary_body(rsp)
                            if binary_body:
                                return binary_body
                        elif rsp.status == 403:
                            printer.warn(f'403频繁, {url}')
                            await asyncio.sleep(240)
                except:
                    # print('当前网络不好，正在重试，请反馈开发者!!!!')
                    print(sys.exc_info()[0], sys.exc_info()[1], url)
                await asyncio.sleep(0.02)

    async def request_text(self,
                           method,
                           url,
                           **kwargs) -> str:
        async with sem:
            i = 0
            while True:
                i += 1
                if i >= 10:
                    printer.warn(url)
                try:
                    async with self.var_session.request(method, url, **kwargs) as rsp:
                        if rsp.status == 200:
                            text_body = await self.__get_text_body(rsp)
                            if text_body:
                                return text_body
                        elif rsp.status == 403:
                            printer.warn(f'403频繁, {url}')
                            await asyncio.sleep(240)
                except:
                    # print('当前网络不好，正在重试，请反馈开发者!!!!')
                    print(sys.exc_info()[0], sys.exc_info()[1], url)
                await asyncio.sleep(0.02)
