#!/usr/bin/env python3
import table_lib

conn = table_lib.connect_db()
cursor = conn.cursor()

#table = 'balances'
#table = 'coin_social'
#table = 'funding_transactions'
#table = 'last_notarised'
#table = 'notarised_chain_season'
table = 'nn_social'


cursor.execute("SELECT * FROM "+table+";")
print(cursor.fetchall())

cursor.execute("SELECT COUNT(*) FROM "+table+";")
print(cursor.fetchall())

cursor.close()

conn.close()


