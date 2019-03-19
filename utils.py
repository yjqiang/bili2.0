import time
from datetime import datetime


# 半角字符Printable characters(' '-'~')
# 对应的全角字符('　' + '！'-'～')
_table_hwid2fwid = str.maketrans(
    ''.join(chr(i) for i in range(32, 127)),
    '　' + ''.join(chr(i) for i in range(65281, 65375))
    )
    

# 中英文对齐（半角转全角）
def hwid2fwid(orig_text, format_control=10):
    new_text = orig_text.translate(_table_hwid2fwid)
    return f'{new_text:　^{format_control}}'


def seconds_until_tomorrow():
    dt = datetime.now()
    return (23 - dt.hour) * 3600 + (59 - dt.minute) * 60 + 60 - dt.second
    

def print_progress(finished_exp, sum_exp, num_sum=30):
    num_arrow = int(finished_exp / sum_exp * num_sum)
    num_line = num_sum - num_arrow
    percent = finished_exp / sum_exp * 100
    process_bar = f'[{">" * num_arrow}{"-" * num_line}] {percent:.2f}%'
    print(process_bar)
    
    
def curr_time():
    return int(time.time())
