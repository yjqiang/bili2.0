from enum import IntEnum


class TaskType(IntEnum):
    FORCED = 0
    SCHED = 1
    CONSOLE = 2


# 强制性 Task，不受休眠影响而 cancel
class Forced:
    TASK_TYPE = TaskType.FORCED


# 可被休眠影响而被 cancel
class Sched:
    TASK_TYPE = TaskType.SCHED
    
    
# 控制台 Task
# cmd_console 与 web_console 合在一起，即一个 class 里有 cmdconsole_work 函数(log 打印)和 webconsole_work 函数(return 返回)
class Console:
    TASK_TYPE = TaskType.CONSOLE


# 控制如何执行 work 函数，以及执行中结果传递等
class How2Call(IntEnum):
    DONT_WAIT = 0
    WAIT = 1  # 动态这些，需要本次全完成后删除数据库的记录
    WAIT_AND_PASS = 2  # 累次投喂辣条


# 执行 work 函数时使用 loop.call_later 函数，一定无结果返回
class DontWait:
    HOW2CALL = How2Call.DONT_WAIT
    
    
# 执行 work 函数时，按用户顺序依次执行。
# 可以选择是否返回结果（本代码中 web_console 才返回,其余不返回。即无法手动指定）
# 由于 Wait 中间不可 cancel,所以执行 work 函数时类似于 forced 那样执行，即不可 cancel
class Wait:
    HOW2CALL = How2Call.WAIT
    

# 执行 work 函数时，按用户顺序依次执行；且互相之间有参数传递，运算结果的最后一个list/tuple作为参数(*args)传递给下一人
# 可以选择是否返回结果（本代码中 web_console 才返回,其余不返回。即无法手动指定）
# 若选择返回结果。运算结果中，除最后一个list/tuple外，其余均作为运算结果存储下来
# 由于 WaitAndPass 中间不可cancel,所以执行 work 函数时类似于 forced 那样执行，即不可 cancel
class WaitAndPass:
    HOW2CALL = How2Call.WAIT_AND_PASS
    
    
class UniqueType(IntEnum):
    MULTI = 0
    UNIQUE = 1
    

class Multi:
    UNIQUE_TYPE = UniqueType.MULTI

        
class Unique:
    UNIQUE_TYPE = UniqueType.UNIQUE
