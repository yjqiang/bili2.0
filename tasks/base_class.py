from enum import IntEnum


class TaskType(IntEnum):
    FORCED_TASK = 0
    SCHED_TASK = 1


class ForcedTask:
    TASK_TYPE = TaskType.FORCED_TASK


class SchedTask:
    TASK_TYPE = TaskType.SCHED_TASK
