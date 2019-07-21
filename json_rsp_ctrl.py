import enum

import attr
import pampy


@enum.unique
class JsonRspType(enum.IntEnum):
    UNDEFINED = 0
    OK = 1
    LOGOUT = 2
    IGNORE = 3


class In:
    __slots__ = ('_value',)

    def __init__(self, value):
        self._value = value

    def __call__(self, value):
        return self._value in value


def patterns_actions(_, __, value):
    if isinstance(value, (tuple, list)):
        if not len(value) % 2:
            iterator = iter(value)
            for pattern, action in zip(iterator, iterator):
                if not isinstance(action, JsonRspType):
                    raise ValueError(f'action 必须为 JsonRspType({action})')
            return
        raise ValueError('必须 pattern、action 配对')
    raise ValueError('必须是 tuple 或 list')


DEFAULT_BASE_CTRL = (
    {'code': 1024}, JsonRspType.IGNORE,
    {'msg': In('操作太快')}, JsonRspType.IGNORE,
    {'msg': In('系统繁忙')}, JsonRspType.IGNORE,
    {'msg': In('过于频繁')}, JsonRspType.IGNORE,
)


@attr.s(slots=True, frozen=True)
class Ctrl:
    extend = attr.ib(
        validator=attr.validators.optional(patterns_actions))

    # 是否支持全局的那个配置（1024之类的）
    base = attr.ib(
        default=DEFAULT_BASE_CTRL,
        validator=attr.validators.optional(patterns_actions)
    )
    # 如果都不匹配该怎么办
    default = attr.ib(
        default=JsonRspType.IGNORE,
        validator=attr.validators.instance_of(JsonRspType)
    )

    def verify(self, dict_var: dict) -> JsonRspType:
        if self.base is not None:
            result = pampy.match(dict_var, *self.base, default=JsonRspType.UNDEFINED)
            if result != JsonRspType.UNDEFINED:
                return result

        if self.extend is not None:
            result = pampy.match(dict_var, *self.extend, default=JsonRspType.UNDEFINED)
            if result != JsonRspType.UNDEFINED:
                return result

        return self.default


# TODO: delete
# 这是为了过渡上一代的（code == 3 or code == -401 or code == 1003 or code == -101 or code == 401）这样的
TMP_DEFAULT_CTRL = Ctrl(
    extend=(
        {'code': 3}, JsonRspType.LOGOUT,
        {'code': -401}, JsonRspType.LOGOUT,
        {'code': 1003}, JsonRspType.LOGOUT,
        {'code': -101}, JsonRspType.LOGOUT,
        {'code': 401}, JsonRspType.LOGOUT,
    ),
    base=DEFAULT_BASE_CTRL,
    default=JsonRspType.OK
)

ZERO_ONLY_CTRL = Ctrl(
    extend=(
        {'code': 0}, JsonRspType.OK,
    ),
    base=None,
    default=JsonRspType.IGNORE
)
