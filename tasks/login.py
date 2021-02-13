import base64
from urllib import parse

import rsa

from reqs.login import LoginReq
from .base_class import Forced, Wait, Multi


class LoginTask(Forced, Wait, Multi):
    TASK_NAME = 'null'

    @staticmethod
    async def check(_):
        return (-2, None),

    @staticmethod
    async def work(user):
        # 搞两层的原因是normal这里catch了取消这里时，直接return，会导致user自己调用主动登陆功能失败
        await LoginTask.handle_login_status(user)

    @staticmethod
    async def handle_login_status(user):
        if not user.is_online():
            return await LoginTask.login(user)
        if not (await LoginTask.is_token_usable(user)):
            if not (await LoginTask.refresh_token(user)):
                return await LoginTask.login(user)
            else:
                if not (await LoginTask.is_token_usable(user)):
                    return await LoginTask.login(user)
        return True

    @staticmethod
    async def is_token_usable(user):
        json_rsp = await LoginReq.is_token_usable(user)
        if not json_rsp['code'] and 'mid' in json_rsp['data']:
            user.info('token有效期检查: 仍有效')
            return True
        user.info('token可能过期')
        return False

    @staticmethod
    async def refresh_token(user):
        json_rsp = await LoginReq.refresh_token(user)
        if not json_rsp['code'] and 'mid' in json_rsp['data']['token_info']:
            user.info('token刷新成功')
            data = json_rsp['data']
            access_key = data['token_info']['access_token']
            refresh_token = data['token_info']['refresh_token']
            cookies = data['cookie_info']['cookies']
            list_cookies = [f'{i["name"]}={i["value"]}' for i in cookies]
            cookie = ';'.join(list_cookies)
            login_data = {
                'csrf': cookies[0]['value'],
                'access_key': access_key,
                'refresh_token': refresh_token,
                'cookie': cookie
                }
            user.update_login_data(login_data)
            return True
        return False

    @staticmethod
    async def login(user):
        name = user.name
        password = user.password
        json_rsp = await LoginReq.fetch_key(user)
        data = json_rsp['data']

        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(data['key'])
        crypto_password = base64.b64encode(
            rsa.encrypt((data['hash'] + password).encode('utf-8'), pubkey)
        )
        url_password = parse.quote_plus(crypto_password)
        url_name = parse.quote_plus(name)
        
        json_rsp = await LoginReq.login(user, url_name, url_password)
        while json_rsp['code'] == -105:
            binary_rsp = await LoginReq.fetch_capcha(user)
            captcha = await LoginReq.cnn_captcha(user, binary_rsp)
            json_rsp = await LoginReq.login(user, url_name, url_password, captcha)
                
        if not json_rsp['code'] and not json_rsp['data']['status']:
            data = json_rsp['data']
            access_key = data['token_info']['access_token']
            refresh_token = data['token_info']['refresh_token']
            cookies = data['cookie_info']['cookies']
            list_cookies = [f'{i["name"]}={i["value"]}' for i in cookies]
            cookie = ';'.join(list_cookies)
            login_data = {
                'csrf': cookies[0]['value'],
                'access_key': access_key,
                'refresh_token': refresh_token,
                'cookie': cookie,
                'uid': data['token_info']['mid']
                }
            
            user.update_login_data(login_data)
            user.info('登陆成功')
            return True
        else:
            login_data = {
                'csrf': f'{json_rsp}',
                'access_key': '',
                'refresh_token': '',
                'cookie': '',
                'uid': 'NULL'
                }
            # print(dic_saved_session)
            user.update_login_data(login_data)
            user.info(f'登录失败,错误信息为:{json_rsp}')
            return False
