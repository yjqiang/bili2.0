import time
from datetime import datetime


def seconds_until_tomorrow():
    dt = datetime.now()
    return (23 - dt.hour) * 3600 + (59 - dt.minute) * 60 + 60 - dt.second
     
    
def adjust_for_chinese(orig_str, format_control=10):
    # Printable characters(' '-'~')(range开闭区间问题)
    west = ''.join(chr(i) for i in range(32, 127))
    # 对应的全角字符('　' + '！'-'～')
    east = '　' + ''.join(chr(i) for i in range(65281, 65375))
    table = str.maketrans(west, east)
    new_str = orig_str.translate(table)
    return f'{new_str:　^{format_control}}'
    

def print_progress(finished_exp, sum_exp, num_sum=30):
    num_arrow = int(finished_exp / sum_exp * num_sum)
    num_line = num_sum - num_arrow
    percent = finished_exp / sum_exp * 100
    process_bar = f'[{">" * num_arrow}{"-" * num_line}] {percent:.2f}%'
    print(process_bar)
    
    
def curr_time():
    return int(time.time())
