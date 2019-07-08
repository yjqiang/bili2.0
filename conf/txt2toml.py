"""本脚本单独运行，目的是将商用的批量txt文件转化为本项目可用的toml格式。"""


import os
from re import compile
from typing import Optional

import toml


path_curr = os.path.dirname(os.path.realpath(__file__))
path_txt = f'{path_curr}/accounts.txt'
path_toml = f'{path_curr}/orig_user.toml'


# split_str只填一个字符就行。但是split_str禁止存在于密码与用户名中，空格也禁止
# 每行数据的左右空白字符均会被删除
def txt2toml(split_str: Optional[str] = None):
    if split_str is None:
        split_str = '-'
    assert len(split_str) == 1
    split_elements = f'{split_str} 　'
    split_pattern = compile(
        f'([^{split_elements}]+)[{split_elements}]+([^{split_elements}]+)')
    
    list_users = []
    with open(path_txt, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            result = split_pattern.fullmatch(line)
            username = result.group(1)
            password = result.group(2)
            
            print(f'原数据:|{line}|')
            print(f'分割　:|{username}|{password}|', end='\n\n')
            
            dict_user = {
                'username': username,
                'password': password,
                'access_key': '',
                'cookie': '',
                'csrf': '',
                'uid': '',
                'refresh_token': ''
            }
            list_users.append(dict_user)
            
    dict_users = {'users': list_users}
  
    with open(path_toml, 'w', encoding='utf-8') as f:
        toml.dump(dict_users, f)

      
txt2toml()
