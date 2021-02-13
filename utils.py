import time
import string
from typing import Callable, Dict


# 半角字符Printable characters(' '-'~')
# 对应的全角字符('　' + '！'-'～')
_table_hwid2fwid = str.maketrans(
    ''.join(chr(i) for i in range(32, 127)),
    '　' + ''.join(chr(i) for i in range(65281, 65375))
    )
    

# 中英文对齐（半角转全角）
def hwid2fwid(orig_text: str, format_control=10) -> str:
    new_text = orig_text.translate(_table_hwid2fwid)
    return f'{new_text:　^{format_control}}'


# 清理空白字符，比起 str.maketrans 在短的 whitespace 时挺占优势
def clear_whitespace(orig_text: str, more_whitespace: str = '') -> str:
    whitespace = f'{string.whitespace}　{more_whitespace}'
    text = orig_text
    for i in whitespace:
        text = text.replace(i, '')
    return text


async def wrap_func_as_coroutine(function: Callable, *args, **kwargs):
    return function(*args, **kwargs)
    

def print_progress(finished_exp, sum_exp, num_sum=30) -> str:
    num_arrow = int(finished_exp / sum_exp * num_sum)
    num_line = num_sum - num_arrow
    percent = finished_exp / sum_exp * 100
    return f'[{">" * num_arrow}{"-" * num_line}] ' \
        f'({finished_exp} / {sum_exp} = {percent:.2f}%)'
    
    
def curr_time() -> int:
    return int(time.time())


def prepare_params(dict_params: Dict[str, str]):
    return "&".join(f'{key}={value}' for key, value in dict_params.items())
