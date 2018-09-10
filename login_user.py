import rsa
import time
import base64
from urllib import parse
from base_user import BaseUser


class LoginUser(BaseUser):
    def handle_login_status(self):
        if not self.check_token():
            if not self.refresh_token():
                return self.login()
            else:
                if not self.check_token():
                    print('请联系作者!!!!!!!!!')
                    return self.login()
        return True
        
    def check_token(self):
        response = self.webhub.check_token()
        json_response = response.json()
        if not json_response['code'] and 'mid' in json_response['data']:
            print('token有效期检查: 仍有效')
            # print(json_response)
            return True
        print('token可能过期', json_response)
        return False
                
    def refresh_token(self):
        response = self.webhub.refresh_token()
        json_response = response.json()
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
        print('联系作者(token刷新失败，cookie过期)', json_response)
        return False
        
    def login(self):
        username = self.user_name
        password = self.user_password
        response = self.webhub.fetch_key()
        value = response.json()['data']
        key = value['key']
        Hash = str(value['hash'])
        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(key.encode())
        hashed_password = base64.b64encode(rsa.encrypt((Hash + password).encode('utf-8'), pubkey))
        url_password = parse.quote_plus(hashed_password)
        url_username = parse.quote_plus(username)
        
        response = self.webhub.normal_login(url_username, url_password)
        
        while response.json()['code'] == -105:
            response = self.webhub.captcha_login(url_username, url_password)
        json_rsp = response.json()
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
            print("[{}] {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), '密码登陆成功'))
            return True
            
        else:
            print("[{}] 登录失败,错误信息为:{}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), json_rsp))
            return False
    
