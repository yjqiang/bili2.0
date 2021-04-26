import sqlite3  # sqlite是个很灵活的东西，会自动转换，但是如果错误type且无法转换那么也不报错,传说中的沙雕feature https://www.sqlite.org/faq.html#q3
import os
import sys

from .bili_data_types import \
    SubstanceRaffleStatus, SubstanceRaffleJoined, SubstanceRaffleResults, SubstanceRaffleLuckydog
appPath = ""
if hasattr(sys, '_MEIPASS'):
    # PyInstaller会创建临时文件夹temp
    # 并把路径存储在_MEIPASS中
    appPath = os.path.dirname(os.path.realpath(sys.executable))
else:
    appPath, filename = os.path.split(os.path.abspath(__file__))
# 设计理由是execute script from another directory时，保证仍然可以正确执行（与conf读取设计一致，后续config读取也将自己控制，不再由main控制）
conn = sqlite3.connect(f'{appPath}/data.db')


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
class SubstanceRaffleStatusTable:
    def __init__(self):
        sql_create_table = (
            'CREATE TABLE IF NOT EXISTS substanceraffle_status ('
            'aid TEXT NOT NULL,'
            'number TEXT NOT NULL,'
            'describe TEXT NOT NULL,'
            'join_start_time INTEGER NOT NULL,'  # 时间这里很简单就能比较
            'join_end_time INTEGER NOT NULL, '
            
            'handle_status INTEGER NOT NULL,'

            'prize_cmt TEXT NOT NULL,'

            'PRIMARY KEY (aid, number)'
            '); '
        )
        conn.execute(sql_create_table)
        self.conn = conn

    def as_bili_data(self, row):
        *info, prize_cmt = row
        list_prize_cmt = [i for i in prize_cmt.split(' ')]  # 半角空格分割
        return SubstanceRaffleStatus(*info, list_prize_cmt)

    def insert_element(self, substance_raffle_status: SubstanceRaffleStatus):
        # ?,?,?这种可以对应type，否则很难折腾
        with self.conn:
            self.conn.execute('INSERT INTO substanceraffle_status VALUES (?, ?, ?, ?, ?, ?, ?)',
                              substance_raffle_status.as_sql_values())

    def select_all(self):
        results = []
        for row in self.conn.execute('SELECT * FROM substanceraffle_status'):
            results.append(self.as_bili_data(row))
        return results

    def select_by_primary_key(self, aid, number):
        cursor = self.conn.execute(
            'SELECT * FROM substanceraffle_status WHERE aid=? AND number=?', (str(aid), str(number)))
        result = cursor.fetchone()
        if result is None:
            return None
        return self.as_bili_data(result)

    def del_by_primary_key(self, aid, number):
        with self.conn:
            self.conn.execute('DELETE FROM substanceraffle_status WHERE aid=? AND number=?', (str(aid), str(number)))

    # tuple_join_time_range硬造的一个Tuple[int, int]，表示介于join_start_time与join_end_time之间
    def select(self, handle_status, tuple_join_time_range, join_end_time_r):
        assert handle_status is not None
        results = []
        if tuple_join_time_range is None and join_end_time_r is not None:
            sql = 'SELECT * FROM substanceraffle_status WHERE join_end_time <= ? AND handle_status = ?'
            parameters = (int(join_end_time_r), int(handle_status))
        elif tuple_join_time_range is not None and join_end_time_r is None:
            sql = 'SELECT * FROM substanceraffle_status ' \
                  'WHERE join_start_time <= ? AND join_end_time >= ? AND handle_status = ?'
            join_start_time_r, join_end_time_l = tuple_join_time_range
            parameters = (int(join_start_time_r), int(join_end_time_l), int(handle_status))
        elif tuple_join_time_range is not None and join_end_time_r is not None:
            sql = 'SELECT * FROM substanceraffle_status ' \
                  'WHERE join_start_time <= ?  AND (join_end_time BETWEEN ? AND ?) AND (handle_status = ?)'
            join_start_time_r, join_end_time_l = tuple_join_time_range
            parameters = (int(join_start_time_r), int(join_end_time_l), int(join_end_time_r), int(handle_status))
        else:
            sql = 'SELECT * FROM substanceraffle_status WHERE handle_status = ?'
            parameters = (int(handle_status),)

        for row in self.conn.execute(sql, parameters):
            results.append(self.as_bili_data(row))
        return results

    # 与bili_statistics的api名字相同
    def is_raffleid_duplicate(self, aid, number):
        cursor = self.conn.execute(
            'SELECT 1 FROM substanceraffle_status WHERE aid=? AND number=?', (str(aid), str(number)))
        return bool(cursor.fetchone())


class SubstanceRaffleJoinedTable:
    def __init__(self):
        # uid + orig_substanceid 唯一
        sql_create_table = (
            'CREATE TABLE IF NOT EXISTS substanceraffle_joined ('
            'uid TEXT NOT NULL, '
            'aid TEXT NOT NULL, '  # 比如关注人等信息都存在第一个表里面，不再加冗余
            'number TEXT NOT NULL,'
            'PRIMARY KEY (uid, aid, number)'
            '); '
        )
        conn.execute(sql_create_table)
        self.conn = conn

    def as_bili_data(self, row):
        return SubstanceRaffleJoined(*row)

    def insert_element(self, substance_raffle_joined: SubstanceRaffleJoined):
        with self.conn:
            self.conn.execute('INSERT INTO substanceraffle_joined VALUES (?, ?, ?)',
                              substance_raffle_joined.as_sql_values())

    def select_all(self):
        results = []
        for row in self.conn.execute('SELECT * FROM substanceraffle_joined'):
            results.append(self.as_bili_data(row))
        return results

    def select_by_primary_key(self, uid, aid, number):
        cursor = self.conn.execute('SELECT * FROM substanceraffle_joined WHERE uid = ? AND aid = ? AND number=?',
                                   (str(uid), str(aid), str(number)))
        result = cursor.fetchone()
        if result is None:
            return None
        return self.as_bili_data(result)

    def del_by_primary_key(self, uid, aid, number):
        with self.conn:
            self.conn.execute('DELETE FROM substanceraffle_joined WHERE uid = ? AND aid = ? AND number=?',
                              (str(uid), str(aid), str(number)))


# substanceraffle_results 存储结果，其实这个表与第一个表格略微重合，但是感觉没必要去折腾第一个表格，因为结果这里存储数据没必要过于详细
class SubstanceRaffleResultsTable:
    def __init__(self):
        sql_create_table = (
            'CREATE TABLE IF NOT EXISTS substanceraffle_results ('
            'aid TEXT NOT NULL,'
            'number TEXT NOT NULL,'
            'describe TEXT NOT NULL,'
            'join_start_time INTEGER NOT NULL,'  # 时间这里很简单就能比较
            'join_end_time INTEGER NOT NULL, '

            'prize_cmt TEXT NOT NULL,'           
            'prize_list TEXT NOT NULL,'
            'PRIMARY KEY (aid, number)'
            '); '
        )
        conn.execute(sql_create_table)
        self.conn = conn

    def as_bili_data(self, row):
        *info, prize_cmt, prize_list = row
        list_prize_cmt = [i for i in prize_cmt.split(' ')]
        list_prize_list = [int(i) for i in prize_list.split(' ')]
        return SubstanceRaffleResults(*info, list_prize_cmt, list_prize_list)

    def insert_element(self, substance_raffle_results: SubstanceRaffleResults):
        # ?,?,?这种可以对应type，否则很难折腾
        with self.conn:
            self.conn.execute(
                'INSERT INTO substanceraffle_results VALUES (?, ?, ?, ?, ?, ?, ?)',
                substance_raffle_results.as_sql_values()
            )

    def select_all(self):
        results = []
        for row in self.conn.execute('SELECT * FROM substanceraffle_results'):
            results.append(self.as_bili_data(row))
        return results

    def select_by_primary_key(self, aid, number):
        cursor = self.conn.execute(
            'SELECT * FROM substanceraffle_results WHERE aid=? AND number=?', (str(aid), str(number)))
        result = cursor.fetchone()
        if result is None:
            return None
        return self.as_bili_data(result)

    def del_by_primary_key(self, aid, number):
        with self.conn:
            self.conn.execute('DELETE FROM substanceraffle_results WHERE aid=? AND number=?', (str(aid), str(number)))


class SubstanceRaffleLuckydogTable:
    def __init__(self):
        # uid + orig_substanceid 唯一
        sql_create_table = (
            'CREATE TABLE IF NOT EXISTS substanceraffle_luckydog ('
            'uid TEXT NOT NULL, '
            'aid TEXT NOT NULL, '  # 比如关注人等信息都存在第一个表里面，不再加冗余
            'number TEXT NOT NULL,'
            'PRIMARY KEY (uid, aid, number)'
            '); '
        )
        conn.execute(sql_create_table)
        self.conn = conn

    def as_bili_data(self, row):
        return SubstanceRaffleLuckydog(*row)

    def insert_element(self, substance_raffle_luckydog: SubstanceRaffleLuckydog):
        with self.conn:
            self.conn.execute('INSERT INTO substanceraffle_luckydog VALUES (?, ?, ?)',
                              substance_raffle_luckydog.as_sql_values())

    def select_all(self):
        results = []
        for row in self.conn.execute('SELECT * FROM substanceraffle_luckydog'):
            results.append(self.as_bili_data(row))
        return results

    def select_by_primary_key(self, uid, aid, number):
        cursor = self.conn.execute('SELECT * FROM substanceraffle_luckydog WHERE uid = ? AND aid = ? AND number=?',
                                   (str(uid), str(aid), str(number)))
        result = cursor.fetchone()
        if result is None:
            return None
        return self.as_bili_data(result)

    def del_by_primary_key(self, uid, aid, number):
        with self.conn:
            self.conn.execute('DELETE FROM substanceraffle_luckydog WHERE uid = ? AND aid = ? AND number=?',
                              (str(uid), str(aid), str(number)))


substanceraffle_status_table = SubstanceRaffleStatusTable()
substanceraffle_joined_table = SubstanceRaffleJoinedTable()
substanceraffle_results_table = SubstanceRaffleResultsTable()
substanceraffle_luckydog_table = SubstanceRaffleLuckydogTable()
other_table = OthersTable()


def insert_substanceraffle_status_table(substance_raffle_status: SubstanceRaffleStatus):
    substanceraffle_status_table.insert_element(substance_raffle_status)


def insert_substanceraffle_joined_table(substance_raffle_joined: SubstanceRaffleJoined):
    substanceraffle_joined_table.insert_element(substance_raffle_joined)


def insert_substanceraffle_results_table(substance_raffle_result: SubstanceRaffleResults):
    substanceraffle_results_table.insert_element(substance_raffle_result)


def insert_substanceraffle_luckydog_table(substance_raffle_luckydog: SubstanceRaffleLuckydog):
    substanceraffle_luckydog_table.insert_element(substance_raffle_luckydog)


def select_by_primary_key_from_substanceraffle_joined_table(uid, aid, number):
    return substanceraffle_joined_table.select_by_primary_key(uid, aid, number)


def del_from_substanceraffle_status_table(aid, number):
    substanceraffle_status_table.del_by_primary_key(aid, number)


def is_raffleid_duplicate(aid, number):
    return substanceraffle_status_table.is_raffleid_duplicate(aid, number)


def del_from_substanceraffle_joind_table(uid, aid, number):
    substanceraffle_joined_table.del_by_primary_key(uid, aid, number)


# 从三个表里查最新数据
def init_id() -> int:
    result = other_table.select_by_primary_key('init_id')
    if result is not None:
        init_docid0 = int(result[0])
    else:
        init_docid0 = -1

    sql_select = 'SELECT aid FROM substanceraffle_status'
    select_results = conn.execute(sql_select).fetchall()
    print(0, select_results)
    list_int_results = [int(i[0]) for i in select_results]
    init_docid1 = max(list_int_results, default=-1)

    sql_select = 'SELECT aid FROM substanceraffle_results'
    select_results = conn.execute(sql_select).fetchall()
    print(1, select_results)
    list_int_results = [int(i[0]) for i in select_results]
    init_docid2 = max(list_int_results, default=-1)
    print(init_docid0, init_docid1, init_docid2)
    return max(init_docid0, init_docid1, init_docid2)


def insert_or_replace_other_able(key_word, value):
    other_table.insert_or_replace(key_word, value)


def set_rafflestatus_handle_status(handle_status: int, aid, number):
    with conn:
        conn.execute('UPDATE substanceraffle_status SET handle_status = ? WHERE  aid=? AND number=?', (handle_status, str(aid), str(number)))


def select_rafflestatus(handle_status, tuple_join_time_range=None, join_end_time_r=None):
    return substanceraffle_status_table.select(handle_status, tuple_join_time_range, join_end_time_r)


'''
a = SubstanceRaffleStatus(
    aid=3, number=4, describe='323', join_start_time=21, join_end_time=2332, prize_cmt=['12', 'we ds'], handle_status=0)
print(a)
# substanceraffle_status_table.insert_element(a)
a0 = substanceraffle_status_table.select_by_primary_key(aid=3, number=4)
print(a0)
print(a == a0)

b = SubstanceRaffleJoined(uid='1213', aid='3', number='4')
print(b)
# substanceraffle_joined_table.insert_element(b)
b0 = substanceraffle_joined_table.select_by_primary_key(uid=1213, aid=3, number=4)
print(b0)
print(b == b0)

c = SubstanceRaffleResults(
    aid=3, number=4, describe='323', join_start_time=21, join_end_time=2332,
    prize_cmt=['12', 'we ds'], prize_list=[12, 22])
print(c)
# substanceraffle_results_table.insert_element(c)
c0 = substanceraffle_results_table.select_by_primary_key(aid=3, number=4)
print(c0)
print(c == c0)


d = SubstanceRaffleLuckydog(uid='1213', aid='3', number='4')
print(d)
# substanceraffle_luckydog_table.insert_element(d)
d0 = substanceraffle_luckydog_table.select_by_primary_key(uid=1213, aid=3, number=4)
print(d0)
print(d == d0)

print(init_id())
'''
