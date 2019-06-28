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
    def __init__(self, value):
        self._value = value

    def __call__(self, value):
        return self._value in value


def patterns_actions(_, __, value):
    if isinstance(value, tuple) or isinstance(value, list):
        if not len(value) % 2:
            for pattern, action in zip(value[0::2], value[1::2]):
                if not isinstance(pattern, dict) or not isinstance(action, JsonRspType):
                    raise ValueError('pattern必须为dict，action必须为JsonRspType')
            return
        else:
            raise ValueError('必须pattern、action配对')
    raise ValueError('必须是tuple或list')


DEFAULT_BASE_CTRL = (
    {'code': 1024}, JsonRspType.IGNORE,
    {'msg': In('操作太快')}, JsonRspType.IGNORE
)


@attr.s(slots=True, frozen=True)
class Ctrl:
    extend = attr.ib(
        validator=patterns_actions)

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

        result = pampy.match(dict_var, *self.extend, default=JsonRspType.UNDEFINED)
        return result if result != JsonRspType.UNDEFINED else self.default


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
