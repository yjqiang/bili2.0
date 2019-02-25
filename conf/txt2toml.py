"""本脚本单独运行，目的是将商用的批量txt文件转化为本项目可用的toml格式。"""


import os
from re import compile
import toml


path_curr = os.path.dirname(os.path.realpath(__file__))
path_txt = f'{path_curr}/accounts.txt'
path_toml = f'{path_curr}/orig_user.toml'


# split_str只填一个字符就行，不需要全写全了。但是split_str禁止存在于密码与用户名中，空格也禁止
def txt2toml(split_str=None):
    if split_str is None:
        split_str = '-'
    assert len(split_str) == 1
    split_elements = f'{split_str} 　'
    split_pattern = compile(f'(.+?)[{split_elements}]+(.+)')
    valid_pattern = compile(f'[{split_elements}]+')
    
    list_users = []
    with open(path_txt, 'r', encoding='utf-8') as f:
        for line in f.read().splitlines():
            if not line:
                continue
            result = split_pattern.search(line)
            username = result.group(1)
            password = result.group(2)
            
            print(f'原数据:|{line}|')
            print(f'分割　:|{username}|{password}|', end='\n\n')
            
            assert valid_pattern.search(username) is None
            assert valid_pattern.search(password) is None
            
            dict_user = {}
            dict_user['username'] = username
            dict_user['password'] = password
            dict_user['access_key'] = ''
            dict_user['cookie'] = ''
            dict_user['csrf'] = ''
            dict_user['uid'] = ''
            dict_user['refresh_token'] = ''
            list_users.append(dict_user)
            
    dict_users = {'users': list_users}
  
    with open(path_toml, 'w', encoding='utf-8') as f:
        toml.dump(dict_users, f)
   
txt2toml()
