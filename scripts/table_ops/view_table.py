#!/usr/bin/env python3
import table_lib

conn = table_lib.connect_db()
cursor = conn.cursor()

#table = 'balances'
#table = 'coin_social'
#table = 'funding_transactions'
#table = 'last_notarised'
#table = 'notarised_chain_season'
#table = 'nn_social'
#table = 'notarised_count_season'
#table = 'coins'
table = 'notarised_btc'

cursor.execute("SELECT * FROM "+table+";")

results = cursor.fetchone()
print(results)
print(len(results))




cursor.close()

conn.close()


