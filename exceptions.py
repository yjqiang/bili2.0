from typing import Optional


class RspError(Exception):
    def __init__(self, msg: Optional[str] = None, others=None):
        self.msg = msg
        self.others = others


class LogoutError(RspError):
    pass


class ForbiddenError(RspError):
    pass
