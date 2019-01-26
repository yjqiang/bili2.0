import sys
import asyncio
import json
import aiohttp
import printer

# sem = asyncio.Semaphore(3)
sem = None


class WebSession:
    def __init__(self):
        self.var_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=4))

    async def __get_json_body(self, rsp, is_login=False):
        # json_response = await response.json(content_type=None)
        data = await rsp.read()
        if not data:
            printer.warn(f'json_body出现问题   {data}')
            return None
        json_body = json.loads(data)
        # 之后考虑加入expected_code来约束这个判定
        if isinstance(json_body, dict) and 'code' in json_body:
            code = json_body['code']
            if code == 1024:
                print('b站炸了，暂停所有请求1.5s后重试，请耐心等待')
                await asyncio.sleep(1.5)
                return None
            elif code == 3 or code == -401 or code == 1003 or code == -101 or code == 401:
                print('api提示没有登录')
                print(json_body)
                if not is_login:
                    return 3
                else:
                    return json_body
        return json_body

    async def __get_text_body(self, rsp):
        text = await rsp.text()
        if not text:
            printer.warn(f'json_body出现问题   {text}')
            return None
        return text

    async def __get_binary_body(self, rsp):
        return await rsp.read()

    # method 类似于aiohttp里面的对应method，目前只支持GET、POST
    # is_login后期移除，json这里应该与expected_code协同
    async def request_json(self,
                           method,
                           url,
                           headers=None,
                           data=None,
                           params=None,
                           is_none_allowed=False,
                           is_login=False):
        async with sem:
            i = 0
            while True:
                i += 1
                if i >= 10:
                    printer.warn(url)
                try:
                    async with self.var_session.request(method, url, headers=headers, data=data, params=params) as rsp:
                        if rsp.status == 200:
                            json_body = await self.__get_json_body(
                                rsp, is_login)
                            if json_body is not None or is_none_allowed:
                                return json_body
                        elif rsp.status == 403:
                            print('403频繁', url)
                        elif rsp.status == 404:
                            return None
                except:
                    # print('当前网络不好，正在重试，请反馈开发者!!!!')
                    print(sys.exc_info()[0], sys.exc_info()[1], url)
                    continue

    async def request_binary(self,
                             method,
                             url,
                             headers=None,
                             data=None,
                             params=None,
                             is_none_allowed=False):
        async with sem:
            i = 0
            while True:
                i += 1
                if i >= 10:
                    printer.warn(url)
                try:
                    async with self.var_session.request(method, url, headers=headers, data=data, params=params) as rsp:
                        if rsp.status == 200:
                            binary_body = await self.__get_binary_body(rsp)
                            if binary_body is not None or is_none_allowed:
                                return binary_body
                        elif rsp.status == 403:
                            print('403频繁', url)
                        elif rsp.status == 404:
                            return None
                except:
                    # print('当前网络不好，正在重试，请反馈开发者!!!!')
                    print(sys.exc_info()[0], sys.exc_info()[1], url)
                    continue

    async def request_text(self,
                           method,
                           url,
                           headers=None,
                           data=None,
                           params=None,
                           is_none_allowed=False):
        async with sem:
            i = 0
            while True:
                i += 1
                if i >= 10:
                    printer.warn(url)
                try:
                    async with self.var_session.request(method, url, headers=headers, data=data, params=params) as rsp:
                        if rsp.status == 200:
                            text_body = await self.__get_text_body(rsp)
                            if text_body is not None or is_none_allowed:
                                return text_body
                        elif rsp.status == 403:
                            print('403频繁', url)
                        elif rsp.status == 404:
                            return None
                except:
                    # print('当前网络不好，正在重试，请反馈开发者!!!!')
                    print(sys.exc_info()[0], sys.exc_info()[1], url)
                    continue

