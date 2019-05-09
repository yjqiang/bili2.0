from enum import IntEnum


class TaskType(IntEnum):
    FORCED_TASK = 0
    SCHED_TASK = 1


class ForcedTask:
    TASK_TYPE = TaskType.FORCED_TASK
    TASK_NAME = 'null'  # task的名字，这样舒服一点


class SchedTask:
    TASK_TYPE = TaskType.SCHED_TASK
    TASK_NAME = 'null'  # task的名字，这样舒服一点
