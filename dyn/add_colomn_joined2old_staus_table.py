"""这是为了把第一代数据库迁移到新的数据。
请更新本次commit后，在确定data.db的存在时，首先运行一次此文件。
可以重复运行，不会出错但是没必要反复运行。
"""
import sys
import sqlite3
from os import path


path_db = f'{path.dirname(path.realpath(__file__))}/data.db'
if not path.isfile(path_db):
    print('未找到数据库，请仔细查看本代码开头注释内容', file=sys.stderr)
    sys.exit(-1)

conn = sqlite3.connect(path_db)
colomns = conn.execute('PRAGMA table_info("dynraffle_status")').fetchall()
for colomn in colomns:
    if colomn[1] == 'handle_status':
        print('您已经是最新数据库无需迁移')
        break
else:
    print('检测到老数据库，正在准备迁移，请稍后')
    with conn:
        sql_rename_old_table = 'ALTER TABLE dynraffle_status RENAME TO tmp_dynraffle_status'
        sql_create_new_table = (
            'CREATE TABLE dynraffle_status ('
            'dyn_id TEXT NOT NULL,'
            'doc_id TEXT NOT NULL UNIQUE,'
            'describe TEXT NOT NULL,'
            'uid TEXT NOT NULL,'
            'post_time INTEGER NOT NULL,'  # 时间这里很简单就能比较
            'lottery_time INTEGER NOT NULL, '

            'at_num INTEGER NOT NULL,'
            'feed_limit INTEGER NOT NULL,'  # 0/1 表示bool型
            'handle_status INTEGER NOT NULL,'

            'prize_cmt_1st TEXT NOT NULL,'
            'prize_cmt_2nd TEXT,'
            'prize_cmt_3rd TEXT,'
            'PRIMARY KEY (dyn_id)'
            '); '
        )
        sql_move = 'INSERT INTO dynraffle_status ' \
                   'SELECT dyn_id, doc_id, describe, uid, post_time, lottery_time, at_num, feed_limit, ?, prize_cmt_1st, prize_cmt_2nd, prize_cmt_3rd FROM tmp_dynraffle_status'
        sql_drop_old_table = 'DROP TABLE tmp_dynraffle_status'
        conn.execute(sql_rename_old_table)
        conn.execute(sql_create_new_table)
        conn.execute(sql_move, (1,))
        conn.execute(sql_drop_old_table)

conn.close()
print('DONE')
