import rsa
import base64
from urllib import parse
from bili_user.base_user import BaseUser


class LoginUser(BaseUser):
    async def handle_login_status(self):
        if not self.webhub.cookie_existed():
            return await self.login()
        if not (await self.check_token()):
            if not (await self.refresh_token()):
                return await self.login()
            else:
                if not (await self.check_token()):
                    print('请联系作者!!!!!!!!!')
                    return await self.login()
        return True
        
    async def check_token(self):
        json_response = await self.webhub.check_token()
        if not json_response['code'] and 'mid' in json_response['data']:
            print('token有效期检查: 仍有效')
            # print(json_response)
            return True
        print('token可能过期', json_response)
        return False
                
    async def refresh_token(self):
        json_response = await self.webhub.refresh_token()
        
        # print(json_response)
        
        if not json_response['code'] and 'mid' in json_response['data']['token_info']:
            print('token刷新成功')
            data = json_response['data']
            access_key = data['token_info']['access_token']
            refresh_token = data['token_info']['refresh_token']
            cookie = data['cookie_info']['cookies']
            generator_cookie = (f'{i["name"]}={i["value"]}' for i in cookie)
            cookie_format = ';'.join(generator_cookie)
            dic_saved_session = {
                'csrf': cookie[0]['value'],
                'access_key': access_key,
                'refresh_token': refresh_token,
                'cookie': cookie_format
                }
            self.write_user(dic_saved_session)
            # 更新token信息
            return True
        return False
        
    async def login(self):
        username = self.user_name
        password = self.user_password
        json_rsp = await self.webhub.fetch_key()
        value = json_rsp['data']
        key = value['key']
        Hash = str(value['hash'])
        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(key.encode())
        hashed_password = base64.b64encode(rsa.encrypt((Hash + password).encode('utf-8'), pubkey))
        url_password = parse.quote_plus(hashed_password)
        url_username = parse.quote_plus(username)
        
        json_rsp = await self.webhub.normal_login(url_username, url_password)
        # print(json_rsp)
        
        while json_rsp['code'] == -105:
            json_rsp = await self.webhub.captcha_login(url_username, url_password)
            # print(json_rsp)
                
        # print(json_rsp)
        if not json_rsp['code'] and not json_rsp['data']['status']:
            data = json_rsp['data']
            access_key = data['token_info']['access_token']
            refresh_token = data['token_info']['refresh_token']
            cookie = data['cookie_info']['cookies']
            generator_cookie = (f'{i["name"]}={i["value"]}' for i in cookie)
            cookie_format = ';'.join(generator_cookie)
            dic_saved_session = {
                'csrf': cookie[0]['value'],
                'access_key': access_key,
                'refresh_token': refresh_token,
                'cookie': cookie_format,
                'uid': cookie[1]['value']
                }
            # print(dic_saved_session)
            
            self.write_user(dic_saved_session)
            self.printer_with_id(['登陆成功'], True)
            return True
            
        else:
            dic_saved_session = {
                'csrf': f'{json_rsp}',
                'access_key': '',
                'refresh_token': '',
                'cookie': '',
                'uid': 'NULL'
                }
            # print(dic_saved_session)
            
            self.write_user(dic_saved_session)
            self.printer_with_id([f'登录失败,错误信息为:{json_rsp}'], True)
            return False
    
