"""本数据设计是用于非数据库之外的交互以及数据库转非数据库，而insert数据库时需要手动执行，这傻逼的自动类型转换是坑
"""
import attr


@attr.s(frozen=True)
class DynRaffleStatus:
    # 这部分保证方便迅速定位某条动态（手动）
    dyn_id = attr.ib(converter=int)
    doc_id = attr.ib(converter=int)
    describe = attr.ib(validator=attr.validators.instance_of(str))
    uid = attr.ib(converter=int)
    post_time = attr.ib(converter=int)
    lottery_time = attr.ib(converter=int)

    # 参与抽奖使用
    at_num = attr.ib(converter=int)
    feed_limit = attr.ib(converter=bool)

    # 一些其他信息
    prize_cmt_1st = attr.ib(validator=attr.validators.instance_of(str))  # 奖品描述这里必须str，下同，且不提供type转换
    prize_cmt_2nd = attr.ib(default='', validator=attr.validators.instance_of(str))
    prize_cmt_3rd = attr.ib(default='', validator=attr.validators.instance_of(str))

    # 命名模仿attrs的astuple，非数据库数据转化为数据库数据直接使用，无需在sqlite内再次转换类型
    def as_sql_values(self):
        dyn_id = str(self.dyn_id)  # str 怕超出sql的int限制长度；如果使用sqlite的默认int转str，这sb先损失精度，再存为str（mdzz）!!!!!!!
        doc_id = str(self.doc_id)
        describe = self.describe[:20]  # 截断数据，防止描述过长
        uid = str(self.uid)
        post_time = self.post_time
        lottery_time = self.lottery_time

        at_num = self.at_num
        feed_limit = int(self.feed_limit)

        prize_cmt_1st = self.prize_cmt_1st[:20]
        prize_cmt_2nd = self.prize_cmt_2nd[:20]
        prize_cmt_3rd = self.prize_cmt_3rd[:20]

        return \
            dyn_id, doc_id, describe, uid, post_time, lottery_time,\
            at_num, feed_limit, prize_cmt_1st, prize_cmt_2nd, prize_cmt_3rd


@attr.s(frozen=True)
class DynRaffleJoined:
    uid = attr.ib(converter=int)
    dyn_id = attr.ib(converter=int)
    orig_dynid = attr.ib(converter=int)

    def as_sql_values(self):
        uid = str(self.uid)
        dyn_id = str(self.dyn_id)
        orig_dynid = str(self.orig_dynid)

        return uid, dyn_id, orig_dynid


@attr.s(frozen=True)
class DynRaffleResults:
    dyn_id = attr.ib(converter=int)
    doc_id = attr.ib(converter=int)
    describe = attr.ib(validator=attr.validators.instance_of(str))
    uid = attr.ib(converter=int)
    post_time = attr.ib(converter=int)
    lottery_time = attr.ib(converter=int)

    # 最终获奖情况
    prize_cmt_1st = attr.ib(validator=attr.validators.instance_of(str))  # 不提供type转换
    prize_list_1st = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(int),
            iterable_validator=attr.validators.instance_of(list)
        )
    )
    prize_cmt_2nd = attr.ib(default='', validator=attr.validators.instance_of(str))
    prize_list_2nd = attr.ib(
        default=attr.Factory(list),
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(int),
            iterable_validator=attr.validators.instance_of(list)
        )
    )
    prize_cmt_3rd = attr.ib(default='', validator=attr.validators.instance_of(str))
    prize_list_3rd = attr.ib(
        default=attr.Factory(list),
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(int),
            iterable_validator=attr.validators.instance_of(list)
        )
    )

    def as_sql_values(self):
        dyn_id = str(self.dyn_id)  # str 怕超出sql的int限制长度；如果使用sqlite的默认int转str，这sb先损失精度，再存为str（mdzz）!!!!!!!
        doc_id = str(self.doc_id)
        describe = self.describe[:20]  # 截断数据，防止描述过长
        uid = str(self.uid)
        post_time = self.post_time
        lottery_time = self.lottery_time

        prize_cmt_1st = self.prize_cmt_1st
        prize_list_1st = ' '.join([str(i) for i in self.prize_list_1st])
        prize_cmt_2nd = self.prize_cmt_2nd
        prize_list_2nd = ' '.join([str(i) for i in self.prize_list_2nd])
        prize_cmt_3rd = self.prize_cmt_3rd
        prize_list_3rd = ' '.join([str(i) for i in self.prize_list_3rd])

        return \
            dyn_id, doc_id, describe, uid, post_time, lottery_time,\
            prize_cmt_1st, prize_list_1st,  prize_cmt_2nd, prize_list_2nd, prize_cmt_3rd, prize_list_3rd


@attr.s(frozen=True)
class DynRaffleLuckydog:
    uid = attr.ib(converter=int)
    dyn_id = attr.ib(converter=int)
    orig_dynid = attr.ib(converter=int)
    following_uid = attr.ib(converter=int)

    def as_sql_values(self):
        uid = str(self.uid)
        dyn_id = str(self.dyn_id)
        orig_dynid = str(self.orig_dynid)
        following_uid = str(self.following_uid)

        return uid, dyn_id, orig_dynid, following_uid
