import sqlite3  # sqlite是个很灵活的东西，会自动转换，但是如果错误type且无法转换那么也不报错,传说中的沙雕feature https://www.sqlite.org/faq.html#q3
from os import path
from .bili_data_types import DynRaffleStatus, DynRaffleJoined, DynRaffleResults


# 设计理由是execute script from another directory时，保证仍然可以正确执行（与conf读取设计一致，后续config读取也将自己控制，不再由main控制）
conn = sqlite3.connect(f'{path.dirname(path.realpath(__file__))}/data.db')


class OthersTable:
    def __init__(self):
        sql_create_table = (
            'CREATE TABLE IF NOT EXISTS others ('
            'key_word TEXT NOT NULL,'
            'value TEXT NOT NULL,'
            'PRIMARY KEY (key_word)'
            '); '
        )
        conn.execute(sql_create_table)
        self.conn = conn

    def insert_or_replace(self, key_word, value):
        with self.conn:
            self.conn.execute('INSERT OR REPLACE INTO others (key_word, value) VALUES '
                              '(?,  ?)', (str(key_word), str(value)))

    def select_by_primary_key(self, key_word):
        cursor = self.conn.execute('SELECT value FROM others WHERE key_word=?', (str(key_word),))
        result = cursor.fetchone()
        return result


# 删除先删joined再删除status
class DynRaffleStatusTable:
    def __init__(self):
        sql_create_table = (
            'CREATE TABLE IF NOT EXISTS dynraffle_status ('
            'dyn_id TEXT NOT NULL,'
            'doc_id TEXT NOT NULL UNIQUE,'
            'describe TEXT NOT NULL,'
            'uid TEXT NOT NULL,'
            'post_time INTEGER NOT NULL,'  # 时间这里很简单就能比较
            'lottery_time INTEGER NOT NULL, '

            'at_num INTEGER NOT NULL,'
            'feed_limit INTEGER NOT NULL,'  # 0/1 表示bool型
            
            'prize_cmt_1st TEXT NOT NULL,'
            'prize_cmt_2nd TEXT,'
            'prize_cmt_3rd TEXT,'
            'PRIMARY KEY (dyn_id)'
            '); '
        )
        conn.execute(sql_create_table)
        self.conn = conn

    def as_bili_data(self, row):
        return DynRaffleStatus(*row)

    def insert_element(self, dyn_raffle_status: DynRaffleStatus):
        # ?,?,?这种可以对应type，否则很难折腾
        with self.conn:
            self.conn.execute('INSERT INTO dynraffle_status VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                              dyn_raffle_status.as_sql_values())

    def select_all(self):
        results = []
        for row in self.conn.execute('SELECT * FROM dynraffle_status'):
            results.append(self.as_bili_data(row))
        return results

    def select_by_primary_key(self, dyn_id):
        cursor = self.conn.execute('SELECT * FROM dynraffle_status WHERE dyn_id=?', (str(dyn_id),))
        result = cursor.fetchone()
        if result is None:
            return None
        return self.as_bili_data(result)

    def del_by_primary_key(self, dyn_id):
        with self.conn:
            self.conn.execute('DELETE FROM dynraffle_status WHERE dyn_id=?', (str(dyn_id),))

    def select_bytime(self, curr_time):
        results = []
        for row in self.conn.execute(f'SELECT * FROM dynraffle_status WHERE lottery_time < ?', (int(curr_time),)):
            results.append(self.as_bili_data(row))
        return results

    # 与bili_statistics的api名字相同
    def is_raffleid_duplicate(self, dyn_id: str):
        cursor = self.conn.execute('SELECT 1 FROM dynraffle_status WHERE dyn_id = ?', (dyn_id,))
        return bool(cursor.fetchone())


class DynRaffleJoinedTable:
    def __init__(self):
        # uid + orig_dynid 唯一
        sql_create_table = (
            'CREATE TABLE IF NOT EXISTS dynraffle_joined ('
            'uid TEXT NOT NULL, '
            'dyn_id TEXT NOT NULL, '  # 比如关注人等信息都存在第一个表里面，不再加冗余
            'orig_dynid TEXT NOT NULL,'
            'PRIMARY KEY (uid, orig_dynid)'
            '); '
        )
        conn.execute(sql_create_table)
        self.conn = conn

    def as_bili_data(self, row):
        return DynRaffleJoined(*row)

    def insert_element(self, dyn_raffle_joined: DynRaffleJoined):
        with self.conn:
            self.conn.execute('INSERT INTO dynraffle_joined VALUES (?, ?, ?)',
                              dyn_raffle_joined.as_sql_values())

    def select_all(self):
        results = []
        for row in self.conn.execute('SELECT * FROM dynraffle_joined'):
            results.append(self.as_bili_data(row))
        return results

    def select_by_primary_key(self, uid, orig_dynid):
        cursor = self.conn.execute('SELECT * FROM dynraffle_joined WHERE uid = ? AND orig_dynid = ?',
                                   (str(uid), str(orig_dynid)))
        result = cursor.fetchone()
        if result is None:
            return None
        return self.as_bili_data(result)

    def del_by_primary_key(self, uid, orig_dynid):
        with self.conn:
            self.conn.execute('DELETE FROM dynraffle_joined WHERE uid = ? AND orig_dynid = ?',
                              (str(uid), str(orig_dynid)))


# dynraffle_results 存储结果，其实这个表与第一个表格略微重合，但是感觉没必要去折腾第一个表格，因为结果这里存储数据没必要过于详细
class DynRaffleResultsTable:
    def __init__(self):
        sql_create_table = (
            'CREATE TABLE IF NOT EXISTS dynraffle_results ('
            'dyn_id TEXT NOT NULL, '
            'doc_id TEXT NOT NULL UNIQUE, '
            'describe TEXT NOT NULL, '
            'uid TEXT NOT NULL, '
            'post_time TEXT NOT NULL, '
            'lottery_time TEXT NOT NULL, '

            'prize_cmt_1st TEXT NOT NULL,'
            'prize_list_1st TEXT NOT NULL,'  # 使用长str描述，间隔为空格
            'prize_cmt_2nd TEXT,'
            'prize_list_2nd TEXT,'
            'prize_cmt_3rd TEXT,'
            'prize_list_3rd TEXT,'
            'PRIMARY KEY (dyn_id)'
            '); '
        )
        conn.execute(sql_create_table)
        self.conn = conn

    def as_bili_data(self, row):
        *dyn_info, prize_cmt_1st, prize_list_1st, prize_cmt_2nd, prize_list_2nd, prize_cmt_3rd, prize_list_3rd = row
        list_prize_list_1st = [int(i) for i in prize_list_1st.split()]
        list_prize_list_2nd = [int(i) for i in prize_list_2nd.split()]
        list_prize_list_3rd = [int(i) for i in prize_list_3rd.split()]
        dyn_result = \
            prize_cmt_1st, list_prize_list_1st, prize_cmt_2nd, list_prize_list_2nd, prize_cmt_3rd, list_prize_list_3rd
        return DynRaffleResults(*dyn_info, *dyn_result)

    def insert_element(self, dyn_raffle_reuslts: DynRaffleResults):
        # ?,?,?这种可以对应type，否则很难折腾
        with self.conn:
            self.conn.execute(
                'INSERT INTO dynraffle_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                dyn_raffle_reuslts.as_sql_values()
            )

    def select_all(self):
        results = []
        for row in self.conn.execute('SELECT * FROM dynraffle_results'):
            results.append(self.as_bili_data(row))
        return results

    def select_by_primary_key(self, dyn_id):
        cursor = self.conn.execute('SELECT * FROM dynraffle_results WHERE dyn_id = ?', (str(dyn_id),))
        result = cursor.fetchone()
        if result is None:
            return None
        return self.as_bili_data(result)

    def del_by_primary_key(self, dyn_id):
        with self.conn:
            self.conn.execute('DELETE FROM dynraffle_results WHERE dyn_id = ?', (str(dyn_id),))


dynraffle_status_table = DynRaffleStatusTable()
dynraffle_joined_table = DynRaffleJoinedTable()
dynraffle_results_table = DynRaffleResultsTable()
other_table = OthersTable()


def insert_dynraffle_status_table(dyn_raffle_status: DynRaffleStatus):
    dynraffle_status_table.insert_element(dyn_raffle_status)


def insert_dynraffle_joined_table(dyn_raffle_joined: DynRaffleJoined):
    dynraffle_joined_table.insert_element(dyn_raffle_joined)


def insert_dynraffle_results_table(dyn_raffle_result: DynRaffleResults):
    dynraffle_results_table.insert_element(dyn_raffle_result)


def del_from_dynraffle_status_table(dyn_id):
    dynraffle_status_table.del_by_primary_key(dyn_id)


def del_from_dynraffle_joind_table(uid, orig_dynid):
    dynraffle_joined_table.del_by_primary_key(uid, orig_dynid)


def del_from_dynraffle_results_table(dyn_id):
    dynraffle_results_table.del_by_primary_key(dyn_id)


def select_by_primary_key_from_dynraffle_joined_table(uid, orig_dynid):
    return dynraffle_joined_table.select_by_primary_key(uid, orig_dynid)


def is_raffleid_duplicate(dyn_id):
    return dynraffle_status_table.is_raffleid_duplicate(str(dyn_id))


# 先del，再查询
def should_unfollowed(uid, orig_uid):
    sql_select = 'SELECT 1 FROM dynraffle_status WHERE dyn_id = ' \
                 '(SELECT orig_dynid FROM dynraffle_joined WHERE uid = ?) ' \
                 'AND feed_limit = 1 AND uid = ?'
    return not conn.execute(sql_select, (str(uid), str(orig_uid))).fetchone()


# 全部删除了之后，删除status内的数据
def should_del_from_dynraffle_status_table(orig_dynid):
    cursor = conn.execute('SELECT 1 FROM dynraffle_joined WHERE orig_dynid = ?', (str(orig_dynid),))
    return not cursor.fetchone()


def select_bytime(curr_time):
    return dynraffle_status_table.select_bytime(curr_time)


# 从三个表里查最新数据
def init_docid() -> int:
    result = other_table.select_by_primary_key('init_docid')
    if result is not None:
        init_docid0 = int(result[0])
    else:
        init_docid0 = -1

    sql_select = 'SELECT doc_id FROM dynraffle_status'
    select_results = conn.execute(sql_select).fetchall()
    print(0, select_results)
    list_int_results = [int(i[0]) for i in select_results]
    init_docid1 = max(list_int_results, default=-1)

    sql_select = 'SELECT doc_id FROM dynraffle_results'
    select_results = conn.execute(sql_select).fetchall()
    print(1, select_results)
    list_int_results = [int(i[0]) for i in select_results]
    init_docid2 = max(list_int_results, default=-1)
    print(init_docid0, init_docid1, init_docid2)
    return max(init_docid0, init_docid1, init_docid2)


def insert_or_replace_other_able(key_word, value):  # 'init_docid'
    other_table.insert_or_replace(key_word, value)
