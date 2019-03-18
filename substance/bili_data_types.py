import attr


@attr.s(frozen=True)
class SubstanceRaffleStatus:
    # 这部分保证方便迅速定位某条动态（手动）
    aid = attr.ib(converter=int)
    number = attr.ib(converter=int)
    describe = attr.ib(validator=attr.validators.instance_of(str))
    join_start_time = attr.ib(converter=int)
    join_end_time = attr.ib(converter=int)

    handle_status = attr.ib(validator=attr.validators.in_([-1, 0, 1]))  # -1 表示未参与，0表示正在参与， 1表示已经参与

    # 一些其他信息
    prize_cmt = attr.ib(
        default=attr.Factory(list),
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(str),
            iterable_validator=attr.validators.instance_of(list)
        )
    )

    # 命名模仿attrs的astuple，非数据库数据转化为数据库数据直接使用，无需在sqlite内再次转换类型
    def as_sql_values(self):
        aid = str(self.aid)  # str 怕超出sql的int限制长度；如果使用sqlite的默认int转str，这sb先损失精度，再存为str（mdzz）!!!!!!!
        number = str(self.number)
        describe = self.describe[:20]  # 截断数据，防止描述过长
        join_start_time = self.join_start_time
        join_end_time = self.join_end_time
        handle_status = self.handle_status

        prize_cmts = ' '.join([i.replace(' ', '　') for i in self.prize_cmt])  # 空格换成全角，用半角空格表示element之间间隔

        return aid, number, describe, join_start_time, join_end_time, handle_status, prize_cmts


@attr.s(frozen=True)
class SubstanceRaffleJoined:
    uid = attr.ib(converter=int)
    aid = attr.ib(converter=int)
    number = attr.ib(converter=int)

    def as_sql_values(self):
        uid = str(self.uid)
        aid = str(self.aid)
        number = str(self.number)
        return uid, aid, number


@attr.s(frozen=True)
class SubstanceRaffleResults:
    aid = attr.ib(converter=int)
    number = attr.ib(converter=int)
    describe = attr.ib(validator=attr.validators.instance_of(str))
    join_start_time = attr.ib(converter=int)
    join_end_time = attr.ib(converter=int)

    # 最终获奖情况
    # 一些其他信息
    prize_cmt = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(str),
            iterable_validator=attr.validators.instance_of(list)
        )
    )
    prize_list = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(int),
            iterable_validator=attr.validators.instance_of(list)
        )
    )

    def as_sql_values(self):
        aid = str(self.aid)  # str 怕超出sql的int限制长度；如果使用sqlite的默认int转str，这sb先损失精度，再存为str（mdzz）!!!!!!!
        number = str(self.number)
        describe = self.describe[:20]  # 截断数据，防止描述过长
        join_start_time = self.join_start_time
        join_end_time = self.join_end_time

        prize_cmts = ' '.join([i.replace(' ', '　') for i in self.prize_cmt])
        prize_list = ' '.join([str(i) for i in self.prize_list])

        return aid, number, describe, join_start_time, join_end_time, prize_cmts, prize_list


@attr.s(frozen=True)
class SubstanceRaffleLuckydog:
    uid = attr.ib(converter=int)
    aid = attr.ib(converter=int)
    number = attr.ib(converter=int)

    def as_sql_values(self):
        uid = str(self.uid)
        aid = str(self.aid)
        number = str(self.number)
        return uid, aid, number
