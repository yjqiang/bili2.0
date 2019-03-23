from enum import IntEnum
import attr


@attr.s(slots=True, frozen=True)
class In:
    key = attr.ib(validator=attr.validators.instance_of(str))
    value = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)))

    def match(self, dict_var: dict):
        if self.key in dict_var:
            value = dict_var[self.key]
            if self.value is None:
                return True
            if isinstance(value, str):
                return self.value in value
        return False


@attr.s(slots=True, frozen=True)
class Equal:
    key = attr.ib(validator=attr.validators.instance_of(str))
    value = attr.ib()

    def match(self, dict_var: dict):
        return self.key in dict_var and self.value == dict_var[self.key]


@attr.s(slots=True, frozen=True)
class DeepIn:
    keys = attr.ib(validator=attr.validators.deep_iterable(
        member_validator=attr.validators.instance_of(str),
        iterable_validator=None))
    value = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)))

    def match(self, dict_var: dict):
        tracking = dict_var
        for key in self.keys:
            if isinstance(tracking, dict) and key in tracking:
                tracking = tracking[key]
            else:
                return False
        if self.value is None:
            return True
        if isinstance(tracking, str):
            return self.value in tracking
        return False


@attr.s(slots=True, frozen=True)
class DeepEqual:
    keys = attr.ib(validator=attr.validators.deep_iterable(
        member_validator=attr.validators.instance_of(str),
        iterable_validator=None))
    value = attr.ib()

    def match(self, dict_var: dict):
        tracking = dict_var
        for key in self.keys:
            if isinstance(tracking, dict) and key in tracking:
                tracking = tracking[key]
            else:
                return False
        return self.value == tracking


# others内元素判断是AND，必须全部满足才match
@attr.s(slots=True, frozen=True)
class CtrlElem:
    code = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(int)))

    others = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of((Equal, In, DeepEqual, DeepIn)),
            iterable_validator=None)))

    def match(self, dict_var: dict) -> bool:
        if self.code is not None and self.code != dict_var['code']:
            return False
        if self.others is None:
            return True
        for i in self.others:
            if not i.match(dict_var):
                return False
        return True


class JsonRspType(IntEnum):
    NONE = 0
    OK = 1
    LOGOUT = 2
    IGNORE = 3


# 这里面的verifier(例如ok_verifiers有很多verifier)之间关系为OR，一个满足就可以了
@attr.s(slots=True, frozen=True)
class BaseCtrl:
    # 可以直接返回
    ok_verifiers = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(CtrlElem),
            iterable_validator=None)))
    # 忽略可以直接retry(1024、频繁等)，建议sleep 1s
    ignore_verifiers = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(CtrlElem),
            iterable_validator=None)))
    # raise登出
    logout_verifiers = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(CtrlElem),
            iterable_validator=None)))

    def verify(self, dict_var: dict) -> JsonRspType:
        if self.ok_verifiers is not None:
            for verifier in self.ok_verifiers:
                if verifier.match(dict_var):
                    return JsonRspType.OK
        if self.ignore_verifiers is not None:
            for verifier in self.ignore_verifiers:
                if verifier.match(dict_var):
                    return JsonRspType.IGNORE
        if self.logout_verifiers is not None:
            for verifier in self.logout_verifiers:
                if verifier.match(dict_var):
                    return JsonRspType.LOGOUT
        return JsonRspType.NONE


# 一个全局的ctrl，所有的ctrl都要基于这个
DEFAULT_BASE_CTRL = BaseCtrl(
    ignore_verifiers=[CtrlElem(code=1024)],
)


@attr.s(slots=True, frozen=True)
class Ctrl:
    verifiers = attr.ib(
        validator=attr.validators.instance_of(BaseCtrl))

    # 是否支持全局的那个配置（1024之类的）
    global_verifiers = attr.ib(
        default=DEFAULT_BASE_CTRL,
        validator=attr.validators.optional(
            attr.validators.instance_of(BaseCtrl))
    )
    # 如果都不匹配该怎么办
    default_result = attr.ib(
        default=JsonRspType.IGNORE,
        validator=attr.validators.instance_of(JsonRspType)
    )

    def verify(self, dict_var: dict) -> JsonRspType:
        if self.global_verifiers is not None:
            result = self.global_verifiers.verify(dict_var)
            if result != JsonRspType.NONE:
                return result

        result = self.verifiers.verify(dict_var)
        return result if result != JsonRspType.NONE else self.default_result


DEFAULT_CTRL = Ctrl(
    verifiers=DEFAULT_BASE_CTRL,
    global_verifiers=None,
    default_result=JsonRspType.OK
)


# TODO: delete
# 这是为了过渡上一代的（code == 3 or code == -401 or code == 1003 or code == -101 or code == 401）这样的
TMP_DEFAULT_CTRL = Ctrl(
    verifiers=BaseCtrl(
        logout_verifiers=[
            CtrlElem(code=3),
            CtrlElem(code=-401),
            CtrlElem(code=1003),
            CtrlElem(code=-101),
            CtrlElem(code=401),
            # CtrlElem(code=-500),
        ]),
    global_verifiers=DEFAULT_BASE_CTRL,
    default_result=JsonRspType.OK
)
