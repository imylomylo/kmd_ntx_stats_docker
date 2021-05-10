#!/usr/bin/env python3
import os
import json
from psycopg2.extras import execute_values
from lib_const import *

#### ADRESSES TABLE

def update_addresses_row(row_data):
    try:
        sql = f"INSERT INTO addresses \
                    (season, server, notary, notary_id, \
                    address, pubkey, chain) \
                VALUES (%s, %s, %s, %s, %s, %s, %s) \
                ON CONFLICT ON CONSTRAINT unique_season_chain_address \
                DO UPDATE SET \
                    server='{row_data[1]}', notary='{row_data[2]}', \
                    notary_id='{row_data[3]}', address='{row_data[4]}', \
                    pubkey='{row_data[5]}', chain='{row_data[6]}';"
        CURSOR.execute(sql, row_data)
        CONN.commit()
    except Exception as e:
        logger.error(f"Exception in [update_addresses_row]: {e}")
        logger.error(f"[update_addresses_row] sql: {sql}")
        logger.error(f"[update_addresses_row] row_data: {row_data}")
        CONN.rollback()


def delete_addresses_row(season, chain, address):
    CURSOR.execute(f"DELETE FROM addresses WHERE \
        season = '{season}', \
        chain = '{chain}', \
        address = '{address}' \
        ;")
    CONN.commit()


#### BALANCES TABLE

def update_balances_row(row_data):
    try:
        sql = f"INSERT INTO balances \
                (season, server, notary, \
                address, chain, balance, update_time) \
            VALUES (%s, %s, %s, %s, %s, %s, %s) \
            ON CONFLICT ON CONSTRAINT unique_chain_address_season_balance DO UPDATE SET \
                balance={row_data[5]}, \
                server='{row_data[1]}', \
                update_time={row_data[6]};"
        CURSOR.execute(sql, row_data)
        CONN.commit()
    except Exception as e:
        logger.error(f"Exception in [update_balances_row]: {e}")
        logger.error(f"[update_balances_row] sql: {sql}")
        logger.error(f"[update_balances_row] row_data: {row_data}")
        CONN.rollback()


def delete_balances_row(chain, address, season):
    try:
        sql = f"DELETE FROM balances WHERE chain='{chain}' and address='{address}' and season={season};"
        CURSOR.execute(sql)
        CONN.commit()
    except Exception as e:
        logger.error(f"Exception in [delete_balances_row]: {e}")
        CONN.rollback()






def update_rewards_row(row_data):
    try:
        sql = "INSERT INTO rewards \
            (address, notary, utxo_count, eligible_utxo_count, \
            oldest_utxo_block, balance, rewards, update_time) \
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
            ON CONFLICT ON CONSTRAINT unique_reward_address DO UPDATE SET \
            notary='"+str(row_data[1])+"', utxo_count="+str(row_data[2])+", \
            eligible_utxo_count="+str(row_data[3])+", oldest_utxo_block="+str(row_data[4])+", \
            balance="+str(row_data[5])+", rewards="+str(row_data[6])+", \
            update_time="+str(row_data[7])+";"
        CURSOR.execute(sql, row_data)
        CONN.commit()
        return 1
    except Exception as e:
        if str(e).find('Duplicate') == -1:
            logger.debug(e)
            logger.debug(row_data)
        CONN.rollback()
        return 0


def update_ntx_row(row_data):
    sql = f"INSERT INTO notarised (chain, block_height, \
                                block_time, block_datetime, block_hash, \
                                notaries, notary_addresses, ac_ntx_blockhash, ac_ntx_height, \
                                txid, opret, season, server, scored, score_value, epoch) \
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                ON CONFLICT ON CONSTRAINT unique_txid DO UPDATE SET \
                season='{row_data[11]}', server='{row_data[12]}', scored='{row_data[13]}', \
                notaries=ARRAY{row_data[5]}, notary_addresses=ARRAY{row_data[6]}, \
                score_value={row_data[14]}, epoch='{row_data[15]}';"
    try:
        CURSOR.execute(sql, row_data)
        CONN.commit()
    except Exception as e:
        if str(e).find('duplicate') == -1:
            logger.debug(e)
            logger.debug(row_data)
        CONN.rollback()



def update_server_notarised_tbl(old_server, server, chain=None):
    sql = f"UPDATE notarised SET \
          server='{server}' \
          WHERE server='{old_server}';"
    try:
        CURSOR.execute(sql)
        CONN.commit()
        print(f"{old_server} reclassed as {server}")
    except Exception as e:
        logger.debug(e)
        CONN.rollback()

def update_chain_server_season_notarised_tbl(server, season, chain):
    sql = f"UPDATE notarised SET \
          server='{server}' \
          WHERE season='{season}'\
          AND chain='{chain}';"
    try:
        CURSOR.execute(sql)
        CONN.commit()
        print(f"{old_server} reclassed as {server}")
    except Exception as e:
        logger.debug(e)
        CONN.rollback()

def update_unofficial_chain_notarised_tbl(season, chain):
    sql = f"UPDATE notarised SET \
          season='Unofficial', server='Unofficial', epoch='Unofficial' \
          WHERE season='{season}'\
          AND chain='{chain}';"
    try:
        CURSOR.execute(sql)
        CONN.commit()
        print(f"Unofficial chain {chain} updated for {season}")
    except Exception as e:
        logger.debug(e)
        CONN.rollback()

def update_chain_score_notarised_tbl(chain, score_value, scored, min_time=None, max_time=None, season=None, server=None, epoch=None):
    sql = f"UPDATE notarised SET scored={scored}, score_value={score_value}"
    conditions = []
    if chain:
        conditions.append(f"chain = '{chain}'")
    if min_time:
        conditions.append(f"block_time >= {min_time}")
    if max_time:
        conditions.append(f"block_time <= {max_time}")
    if season:
        conditions.append(f"season = '{season}'")
    if server:
        conditions.append(f"server = '{server}'")
    if epoch:
        conditions.append(f"epoch = '{epoch}'")
    if len(conditions) > 0:
        sql += " WHERE "
        sql += " AND ".join(conditions)    
    sql += ";"

    try:
        CURSOR.execute(sql)
        CONN.commit()
        logger.info(f"UPDATED [notarised]: Set score_value to {score_value} WHERE {conditions}")
    except Exception as e:
        logger.debug(e)
        CONN.rollback()

def update_txid_score_notarised_tbl(txid, scored, score_value):
    sql = f"UPDATE notarised SET \
          scored={scored}, score_value={score_value} \
          WHERE txid='{txid}';"
    try:
        CURSOR.execute(sql)
        CONN.commit()
        print(f"{txid} tagged as {scored} ({score_value})")
    except Exception as e:
        logger.debug(e)
        CONN.rollback()

def update_season_server_addresses_notarised_tbl(txid, season, server, addresses=None):
    if addresses:
        sql = f"UPDATE notarised SET \
              notary_addresses=ARRAY{addresses},  \
              season='{season}', server='{server}' \
              WHERE txid='{txid}';"
    else:
        sql = f"UPDATE notarised SET \
              season='{season}', server='{server}' \
              WHERE txid='{txid}';"

    print(sql)
    try:
        CURSOR.execute(sql)
        CONN.commit()
        print(f"{txid} tagged as {season}")
    except Exception as e:
        logger.debug(e)
        CONN.rollback()



def delete_txid_from_notarised_tbl(txid):
    CURSOR.execute(f"DELETE FROM notarised WHERE txid = '{txid}';")
    CONN.commit()

def update_coins_row(row_data):
    try:
        sql = "INSERT INTO coins \
            (chain, coins_info, electrums, electrums_ssl, explorers, dpow, dpow_tenure, dpow_active, mm2_compatible) \
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) \
            ON CONFLICT ON CONSTRAINT unique_chain_coin DO UPDATE SET \
            coins_info='"+str(row_data[1])+"', \
            electrums='"+str(row_data[2])+"', \
            electrums_ssl='"+str(row_data[3])+"', \
            explorers='"+str(row_data[4])+"', \
            dpow='"+str(row_data[5])+"', \
            dpow_tenure='"+str(row_data[6])+"', \
            dpow_active='"+str(row_data[7])+"', \
            mm2_compatible='"+str(row_data[8])+"';"
        CURSOR.execute(sql, row_data)
        CONN.commit()
        return 1
    except Exception as e:
        logger.debug(e)
        if str(e).find('Duplicate') == -1:
            logger.debug(row_data)
        CONN.rollback()
        return 0
        
def update_mined_row(row_data):
    try:
        sql = "INSERT INTO mined \
            (block_height, block_time, block_datetime, \
             value, address, name, txid, season) \
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
            ON CONFLICT ON CONSTRAINT unique_block DO UPDATE SET \
            block_time='"+str(row_data[1])+"', \
            block_datetime='"+str(row_data[2])+"', \
            value="+str(row_data[3])+", \
            address='"+str(row_data[4])+"', \
            name='"+str(row_data[5])+"', \
            txid='"+str(row_data[6])+"', \
            season='"+str(row_data[7])+"';"
        CURSOR.execute(sql, row_data)
        CONN.commit()
    except Exception as e:
        logger.debug(e)
        if str(e).find('Duplicate') == -1:
            logger.debug(row_data)
        CONN.rollback()

def update_season_mined_count_row(row_data):
    try:
        sql = f"INSERT INTO mined_count_season \
            (name, season, address, blocks_mined, sum_value_mined, \
            max_value_mined, max_value_txid, last_mined_blocktime, last_mined_block, \
            time_stamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
            ON CONFLICT ON CONSTRAINT unique_name_season_mined DO UPDATE SET \
            address='{row_data[2]}', blocks_mined={row_data[3]}, sum_value_mined={row_data[4]}, \
            max_value_mined={row_data[5]}, max_value_txid='{row_data[6]}', last_mined_blocktime={row_data[7]}, \
            last_mined_block={row_data[8]}, time_stamp={row_data[9]};"
        CURSOR.execute(sql, row_data)
        CONN.commit()
        return 1
    except Exception as e:
        if str(e).find('Duplicate') == -1:
            logger.debug(e)
            logger.debug(row_data)
        CONN.rollback()
        return 0

def update_season_notarised_chain_row(row_data):
    sql = "INSERT INTO notarised_chain_season \
         (chain, ntx_count, block_height, kmd_ntx_blockhash,\
          kmd_ntx_txid, kmd_ntx_blocktime, opret, ac_ntx_blockhash, \
          ac_ntx_height, ac_block_height, ntx_lag, season, server) \
          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
          ON CONFLICT ON CONSTRAINT unique_notarised_chain_season_server DO UPDATE \
          SET ntx_count="+str(row_data[1])+", block_height="+str(row_data[2])+", \
          kmd_ntx_blockhash='"+str(row_data[3])+"', kmd_ntx_txid='"+str(row_data[4])+"', \
          kmd_ntx_blocktime="+str(row_data[5])+", opret='"+str(row_data[6])+"', \
          ac_ntx_blockhash='"+str(row_data[7])+"', ac_ntx_height="+str(row_data[8])+", \
          ac_block_height='"+str(row_data[9])+"', ntx_lag='"+str(row_data[10])+"';"
         
    CURSOR.execute(sql, row_data)
    CONN.commit()

def update_season_notarised_count_row(row_data): 
    sql = "INSERT INTO notarised_count_season \
        (notary, btc_count, antara_count, \
        third_party_count, other_count, \
        total_ntx_count, chain_ntx_counts, season_score, \
        chain_ntx_pct, time_stamp, season) \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
        ON CONFLICT ON CONSTRAINT unique_notary_season DO UPDATE SET \
        btc_count="+str(row_data[1])+", antara_count="+str(row_data[2])+", \
        third_party_count="+str(row_data[3])+", other_count="+str(row_data[4])+", \
        total_ntx_count="+str(row_data[5])+", chain_ntx_counts='"+str(row_data[6])+"', \
        season_score='"+str(row_data[7])+"', chain_ntx_pct='"+str(row_data[8])+"', \
        time_stamp="+str(row_data[9])+";"
    CURSOR.execute(sql, row_data)
    CONN.commit()

def update_daily_mined_count_row(row_data):
    try:
        sql = "INSERT INTO mined_count_daily \
            (notary, blocks_mined, sum_value_mined, \
            mined_date, time_stamp) VALUES (%s, %s, %s, %s, %s) \
            ON CONFLICT ON CONSTRAINT unique_notary_daily_mined \
            DO UPDATE SET \
            blocks_mined="+str(row_data[1])+", \
            sum_value_mined='"+str(row_data[2])+"';"
        CURSOR.execute(sql, row_data)
        CONN.commit()
        return 1
    except Exception as e:
        if str(e).find('Duplicate') == -1:
            logger.debug(e)
            logger.debug(row_data)
        CONN.rollback()
        return 0

def update_daily_notarised_chain_row(row_data):
    sql = f"INSERT INTO notarised_chain_daily \
          (season, server, chain, ntx_count, notarised_date) \
          VALUES (%s, %s, %s, %s, %s) \
          ON CONFLICT ON CONSTRAINT unique_notarised_chain_daily DO UPDATE \
          SET ntx_count={row_data[3]};"
    CURSOR.execute(sql, row_data)
    CONN.commit()

def update_daily_notarised_count_row(row_data): 
    sql = "INSERT INTO notarised_count_daily \
        (notary, btc_count, antara_count, \
        third_party_count, other_count, \
        total_ntx_count, chain_ntx_counts, \
        chain_ntx_pct, time_stamp, season, notarised_date) \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
        ON CONFLICT ON CONSTRAINT unique_notary_date DO UPDATE SET \
        btc_count="+str(row_data[1])+", antara_count="+str(row_data[2])+", \
        third_party_count="+str(row_data[3])+", other_count="+str(row_data[4])+", \
        total_ntx_count="+str(row_data[5])+", chain_ntx_counts='"+str(row_data[6])+"', \
        chain_ntx_pct='"+str(row_data[7])+"', time_stamp="+str(row_data[8])+",  \
        season='"+str(row_data[9])+"', notarised_date='"+str(row_data[10])+"';"
    CURSOR.execute(sql, row_data)
    CONN.commit()

def update_table(table, update_str, condition):
    try:
        sql = "UPDATE "+table+" \
               SET "+update_str+" WHERE "+condition+";"

        CURSOR.execute(sql)
        CONN.commit()
        return 1
    except Exception as e:
        logger.debug(e)
        logger.debug(sql)
        CONN.rollback()
        return 0

def update_sync_tbl(row_data):
    try:
        sql = "INSERT INTO chain_sync \
            (chain, block_height, sync_hash, explorer_hash) \
            VALUES (%s, %s, %s, %s) \
            ON CONFLICT ON CONSTRAINT unique_chain_sync DO UPDATE SET \
            block_height='"+str(row_data[1])+"', \
            sync_hash='"+str(row_data[2])+"', \
            explorer_hash='"+str(row_data[3])+"';"
        CURSOR.execute(sql, row_data)
        CONN.commit()
        return 1
    except Exception as e:
        if str(e).find('Duplicate') == -1:
            logger.debug(e)
            logger.debug(row_data)
        CONN.rollback()
        return 0

def update_nn_social_row(row_data):
    try:
        sql = "INSERT INTO  nn_social \
            (notary, twitter, youtube, email, discord, \
            telegram, github, keybase, \
            website, icon, season) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
            ON CONFLICT ON CONSTRAINT unique_notary_season_social DO UPDATE SET \
            twitter='"+str(row_data[1])+"', youtube='"+str(row_data[2])+"', \
            email='"+str(row_data[3])+"', discord='"+str(row_data[4])+"', \
            telegram='"+str(row_data[5])+"', github='"+str(row_data[6])+"', \
            keybase='"+str(row_data[7])+"', website='"+str(row_data[8])+"', \
            icon='"+str(row_data[9])+"', season='"+str(row_data[10])+"';"
        CURSOR.execute(sql, row_data)
        CONN.commit()
        return 1
    except Exception as e:
        if str(e).find('Duplicate') == -1:
            logger.debug(e)
            logger.debug(row_data)
        CONN.rollback()
        return 0

def update_coin_social_row(row_data):
    try:
        sql = "INSERT INTO  coin_social \
            (chain, twitter, youtube, discord, \
            telegram, github, explorer, \
            website, icon, season) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
            ON CONFLICT ON CONSTRAINT unique_chain_season_social DO UPDATE SET \
            twitter='"+str(row_data[1])+"', \
            youtube='"+str(row_data[2])+"', discord='"+str(row_data[3])+"', \
            telegram='"+str(row_data[4])+"', github='"+str(row_data[5])+"', \
            explorer='"+str(row_data[6])+"', website='"+str(row_data[7])+"', \
            icon='"+str(row_data[8])+"', season='"+str(row_data[9])+"';"
        CURSOR.execute(sql, row_data)
        CONN.commit()
        return 1
    except Exception as e:
        if str(e).find('Duplicate') == -1:
            logger.debug(e)
            logger.debug(row_data)
        CONN.rollback()
        return 0

def update_last_ntx_row(row_data):
    try:
        sql = "INSERT INTO last_notarised \
            (notary, chain, txid, block_height, \
            block_time, season, server) VALUES (%s, %s, %s, %s, %s, %s, %s) \
            ON CONFLICT ON CONSTRAINT unique_notary_season_server_chain DO UPDATE SET \
            txid='"+str(row_data[2])+"', \
            block_height='"+str(row_data[3])+"', \
            block_time='"+str(row_data[4])+"', \
            season='"+str(row_data[5])+"', \
            server='"+str(row_data[6])+"';"
        CURSOR.execute(sql, row_data)
        CONN.commit()
        
        return 1
    except Exception as e:
        logger.debug(e)
        if str(e).find('Duplicate') == -1:
            logger.debug(row_data)
        CONN.rollback()
        return 0

def update_btc_address_deltas_tbl(row_data):
    try:
        sql = "INSERT INTO  btc_address_deltas \
            (notary, address, category, txid, block_time, \
             total_in, total_out, fees, vin_addr, vout_addr, season) \
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        CURSOR.execute(sql, row_data)
        CONN.commit()
        return 1
    except Exception as e:
        if str(e).find('Duplicate') == -1:
            logger.debug(e)
            logger.debug(row_data)
        CONN.rollback()
        return 0

def update_funding_row(row_data):
    try:
        sql = "INSERT INTO  funding_transactions \
            (chain, txid, vout, amount, \
            block_hash, block_height, block_time, \
            category, fee, address, notary, season) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
            ON CONFLICT ON CONSTRAINT unique_category_vout_txid_funding DO UPDATE SET \
            chain='"+str(row_data[0])+"', \
            amount='"+str(row_data[3])+"', \
            block_hash='"+str(row_data[4])+"', \
            block_height='"+str(row_data[5])+"', \
            block_time='"+str(row_data[6])+"', \
            fee='"+str(row_data[8])+"', \
            address='"+str(row_data[9])+"', \
            notary='"+str(row_data[10])+"', \
            season='"+str(row_data[11])+"';"
        CURSOR.execute(sql, row_data)
        CONN.commit()
        return 1
    except Exception as e:
        if str(e).find('Duplicate') == -1:
            logger.debug(e)
            logger.debug(row_data)
        CONN.rollback()
        return 0

def ts_col_to_dt_col(ts_col, dt_col, table):
    sql = "UPDATE "+table+" SET "+dt_col+"=to_timestamp("+ts_col+");"
    CURSOR.execute(sql)
    CONN.commit()

def update_notarised_tenure_row(row_data):
    try:
        sql = "INSERT INTO notarised_tenure (chain, first_ntx_block, \
            last_ntx_block, first_ntx_block_time, last_ntx_block_time, \
            official_start_block_time, official_end_block_time, \
            unscored_ntx_count, scored_ntx_count, season, server) \
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
            ON CONFLICT ON CONSTRAINT unique_chain_season_server_tenure DO UPDATE SET \
            first_ntx_block='"+str(row_data[1])+"', last_ntx_block="+str(row_data[2])+", \
            first_ntx_block_time="+str(row_data[3])+", last_ntx_block_time="+str(row_data[4])+", \
            official_start_block_time="+str(row_data[5])+", official_end_block_time="+str(row_data[6])+", \
            unscored_ntx_count="+str(row_data[7])+", scored_ntx_count="+str(row_data[8])+", \
            server='"+str(row_data[10])+"';"
        CURSOR.execute(sql, row_data)
        CONN.commit()
        return 1
    except Exception as e:
        if str(e).find('Duplicate') == -1:
            logger.debug(e)
            logger.debug(row_data)
        CONN.rollback()
        return 0

def delete_nn_btc_tx_transaction(txid):
    CURSOR.execute(f"DELETE FROM nn_btc_tx WHERE txid='{txid}';")
    CONN.commit()

def update_nn_btc_tx_row(row_data):
    sql = "INSERT INTO nn_btc_tx (txid, block_hash, block_height, \
                                block_time, block_datetime, \
                                address, notary, season, category, \
                                input_index, input_sats, \
                                output_index, output_sats, fees, num_inputs, num_outputs) \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
        ON CONFLICT ON CONSTRAINT unique_btc_nn_txid DO UPDATE SET \
        notary='"+str(row_data[6])+"', category='"+str(row_data[8])+"';"
    try:
        CURSOR.execute(sql, row_data)
        CONN.commit()
    except Exception as e:
        logger.debug(e)
        if str(e).find('duplicate') == -1:
            logger.debug(row_data)
        CONN.rollback()

def insert_nn_btc_tx_row(row_data):
    sql = "INSERT INTO nn_btc_tx (txid, block_hash, block_height, \
                                block_time, block_datetime, \
                                address, notary, season, category, \
                                input_index, input_sats, \
                                output_index, output_sats, fees, num_inputs, num_outputs) \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
    try:
        CURSOR.execute(sql, row_data)
        CONN.commit()
    except Exception as e:
        logger.debug(e)
        if str(e).find('duplicate') == -1:
            logger.debug(row_data)
        CONN.rollback()

def update_nn_btc_tx_notary_from_addr(notary, addr):
    sql = f"UPDATE nn_btc_tx SET notary='{notary}' WHERE address='{addr}';"
    try:
        CURSOR.execute(sql)
        CONN.commit()
        logger.info(f"{addr} tagged as {notary} in DB")
    except Exception as e:
        logger.debug(e)
        CONN.rollback()

def update_nn_btc_tx_notary_category_from_addr(notary, category, addr):
    sql = f"UPDATE nn_btc_tx SET notary='{notary}', category='{category}' WHERE address='{addr}';"
    try:
        CURSOR.execute(sql)
        CONN.commit()
        logger.info(f"{addr} tagged as {notary} in DB")
    except Exception as e:
        logger.debug(e)
        CONN.rollback()

def update_nn_btc_tx_category_from_txid(category, txid):
    sql = f"UPDATE nn_btc_tx SET category='{category}' WHERE txid='{txid}';"
    try:
        CURSOR.execute(sql)
        CONN.commit()
        logger.info(f"{txid} tagged as {category} in DB")
    except Exception as e:
        logger.debug(e)
        CONN.rollback()

def update_nn_btc_tx_outindex_from_txid(outindex, txid):
    sql = f"UPDATE nn_btc_tx SET output_index='{outindex}' WHERE txid='{txid}';"
    try:
        CURSOR.execute(sql)
        CONN.commit()
        logger.info(f"{txid} tagged as {outindex} in DB")
    except Exception as e:
        logger.debug(e)
        CONN.rollback()

def delete_nn_btc_tx_row(txid, notary):
    sql = "DELETE FROM nn_btc_tx WHERE txid='"+str(txid)+"' and notary='"+str(notary)+"';"
    try:
        CURSOR.execute(sql)
        CONN.commit()
    except Exception as e:
        logger.debug(e)
        CONN.rollback()


#### LTC

def update_nn_ltc_tx_notary_from_addr(notary, addr):
    sql = f"UPDATE nn_ltc_tx SET notary='{notary}' WHERE address='{addr}';"
    try:
        CURSOR.execute(sql)
        CONN.commit()
        logger.info(f"{addr} tagged as {notary} in DB")
    except Exception as e:
        logger.debug(e)
        CONN.rollback()

def update_nn_ltc_tx_row(row_data):
    sql = "INSERT INTO nn_ltc_tx (txid, block_hash, block_height, \
                                block_time, block_datetime, \
                                address, notary, season, category, \
                                input_index, input_sats, \
                                output_index, output_sats, fees, num_inputs, num_outputs) \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
        ON CONFLICT ON CONSTRAINT unique_ltc_nn_txid DO UPDATE SET \
        notary='"+str(row_data[6])+"', category='"+str(row_data[8])+"';"
    try:
        CURSOR.execute(sql, row_data)
        CONN.commit()
    except Exception as e:
        logger.debug(e)
        if str(e).find('duplicate') == -1:
            logger.debug(row_data)
        CONN.rollback()


def update_scoring_epoch_row(row_data):
    sql = f"INSERT INTO scoring_epochs \
                (season, server, epoch, epoch_start, epoch_end, \
                start_event, end_event, epoch_chains, score_per_ntx) \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) \
        ON CONFLICT ON CONSTRAINT unique_scoring_epoch DO UPDATE SET \
            epoch_start={row_data[3]}, \
            epoch_end={row_data[4]}, \
            start_event='{row_data[5]}', \
            end_event='{row_data[6]}', \
            epoch_chains=ARRAY{row_data[7]}, \
            score_per_ntx={row_data[8]};"
    try:
        CURSOR.execute(sql, row_data)
        CONN.commit()
    except Exception as e:
        logger.debug(e)
        if str(e).find('duplicate') == -1:
            logger.debug(row_data)
        CONN.rollback()

def update_notarised_epoch(actual_epoch, season=None, server=None, chain=None, txid=None):
    sql = f"UPDATE notarised SET epoch='{actual_epoch}'"
    conditions = []
    if season:
        conditions.append(f"season = '{season}'")
    if server:
        conditions.append(f"server = '{server}'")
    if chain:
        conditions.append(f"chain = '{chain}'")
    if txid:
        conditions.append(f"txid = '{txid}'") 
    if len(conditions) > 0:
        sql += " WHERE "
        sql += " AND ".join(conditions)    
    sql += ";"

    try:
        CURSOR.execute(sql)
        CONN.commit()
    except Exception as e:
        logger.debug(e)
        CONN.rollback()

def update_notarised_epoch_scores(chain, season, server, epoch, epoch_start, epoch_end, score_per_ntx, scored):
    sql = f"UPDATE notarised SET epoch='{epoch}', score_value={score_per_ntx}, scored={scored}"
    conditions = []
    if chain:
        conditions.append(f"chain = '{chain}'")
    if season:
        conditions.append(f"season = '{season}'")
    if server:
        conditions.append(f"server = '{server}'")
    if epoch_start:
        conditions.append(f"block_time >= {epoch_start}")
    if epoch_end:
        conditions.append(f"block_time <= {epoch_end}")
    if len(conditions) > 0:
        sql += " WHERE "
        sql += " AND ".join(conditions)    
    sql += ";"

    try:
        CURSOR.execute(sql)
        CONN.commit()
    except Exception as e:
        logger.debug(e)
        CONN.rollback()

def update_vote2021_row(row_data):
    sql = f"INSERT INTO vote2021 \
                (txid, block_hash, block_time, \
                lock_time, block_height, votes, \
                candidate, candidate_address, \
                mined_by, difficulty, notes) \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
        ON CONFLICT ON CONSTRAINT unique_vote_txid_candidate DO UPDATE SET \
            txid='{row_data[0]}', \
            block_hash='{row_data[1]}', \
            block_time={row_data[2]}, \
            lock_time={row_data[3]}, \
            block_height={row_data[4]}, \
            votes={row_data[5]}, \
            candidate='{row_data[6]}', \
            candidate_address='{row_data[7]}', \
            mined_by='{row_data[8]}', \
            difficulty='{row_data[9]}', \
            notes='{row_data[10]}';"
    try:
        CURSOR.execute(sql, row_data)
        CONN.commit()
    except Exception as e:
        logger.debug(e)
        if str(e).find('duplicate') == -1:
            logger.debug(row_data)
        CONN.rollback()