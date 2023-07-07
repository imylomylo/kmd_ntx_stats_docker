#!/usr/bin/env python3
import os
import csv
import sys
import json
import time
import requests
import sqlite3
from dotenv import load_dotenv
from lib_db import CONN, CURSOR
from psycopg2.extras import execute_values

import requests
import logging
import logging.handlers

from lib_helper import *
import lib_validate as validate
import lib_electrum as electrum

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d-%b-%y %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

VERSION_TIMESPANS_URL = "https://raw.githubusercontent.com/KomodoPlatform/dPoW/master/doc/seed_version_epochs.json"
VERSION_DATA = requests.get(VERSION_TIMESPANS_URL).json()
SCRIPT_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

# Date:   Mon Nov 14 13:40:18 2022 +0300 6e4de5d21
# Date:   Wed Aug 10 18:42:54 2022 +0700 0f6c72615
# Date:   Mon Jul 11 11:11:34 2022 +0300 ce32ab8da
# Date:   Tue Jun 21 15:04:00 2022 +0700 b8598439a

'''
This script collects seednode stats for notaries using the correct version.
At the end of the season, or after an update, run with the `rectify_scores` param to update the scores.
'''

# ENV VARS
load_dotenv()
MM2_USERPASS = os.getenv("MM2_USERPASS")
MM2_IP = "http://127.0.0.1:7783"
DB_PATH = os.getenv("DB_PATH")

seednodes = {
    "Season_6": {
        "alien_EU": {
            "IP": "alien-eu.techloverhd.com",
            "PeerID": "12D3KooWSCmjGYjmjEEiMYZyCZVuEYmGQCAtrMdpWcGSbGG39aHv"
        },
        "alien_NA": {
            "IP": "alien-na.techloverhd.com",
            "PeerID": "12D3KooWA9bym7s8gMdPVHcX872yjrz6Sq5rjpZAKBVFyoeWpJie"
        },
        "alien_SH": {
            "IP": "alien-sh.techloverhd.com",
            "PeerID": "12D3KooWBcVknefLZ3ZEfbFUHzfB2HzUjW4WLVDTe7TBqPmap9Cy"
        },
        "alienx_EU": {
            "IP": "alienx-eu.techloverhd.com",
            "PeerID": "12D3KooWJtcEna77ntbQA4wxr8NWSFP14dmK746C34tTkdSiJJcr"
        },
        "alienx_NA": {
            "IP": "alienx-na.techloverhd.com",
            "PeerID": "12D3KooWBXS7vcjYGQ5vy7nZj65FicpdxXsavPdLYB8gN7Ai3ruA"
        },
        "chmex_NA": {
            "IP": "1.na.seed.adex.dexstats.info",
            "PeerID": "12D3KooWDNUgDwAAuJbyoS5DiRbhvMSwrUh1yepKsJH8URcFwPp3"
        },
        "cipi_1_EU": {
            "IP": "cipi_eu.cipig.net",
            "PeerID": "12D3KooWBhGrTVfaK9v12eA3Et84Y8Bc6ixfZVVGShsad2GBWzm3"
        },
        "cipi_2_EU": {
            "IP": "cipi2_eu.cipig.net",
            "PeerID": "12D3KooWRRmHVy9PWAtED4XS5Ys6V653ERgtgcimyCYVGGRgbM9d"
        },
        "cipi_AR": {
            "IP": "cipi_ar.cipig.net",
            "PeerID": "12D3KooWMsfmq3bNNPZTr7HdhTQvxovuR1jo5qvM362VQZorTk3F"
        },
        "cipi_NA": {
            "IP": "cipi_na.cipig.net",
            "PeerID": "12D3KooWBoQYTPf4q2bnsw8fUA2LKoknccVLrAcF1caCa48ev8QU"
        },
        "dragonhound_DEV": {
            "IP": "dev3p.smk.dog",
            "PeerID": "12D3KooWEnrvbqvtTowYMR8FnBeKtryTj9RcXGx8EPpFZHou2ruP"
        },
        "dragonhound_NA": {
            "IP": "na3p.smk.dog",
            "PeerID": "12D3KooWPSJv1jvZTgw6wYuYjsEu1Dq5KV7v1tKrtZRGNYANzKqW"
        },
        "fediakash_AR": {
            "IP": "fediakash.mooo.com",
            "PeerID": "12D3KooWCSidNncnbDXrX5G6uWdFdCBrMpaCAqtNxSyfUcZgwF7t"
        },
        "gcharang_DEV": {
            "IP": "3p.dev.lordofthechains.com",
            "PeerID": "12D3KooWH3p4ysSPRK6t12HpMkQkwXHtXbjwyKstAst4CRBjrJXe"
        },
        "gcharang_SH": {
            "IP": "3p.sh.lordofthechains.com",
            "PeerID": "12D3KooWK9nDcy9EYQEKedsZd749RKQ1SWJ9v34aDMKvdBjJfZTF"
        },
        "komodopioneers_EU": {
            "IP": "eu.komodopioneers.org",
            "PeerID": "12D3KooWMy5dwrAjbMmGwTFBLtfiYcwH35RL3kFiBCtDgPHTjJhD"
        },
        "metaphilibert_SH": {
            "IP": "mm2.komodochainz.info",
            "PeerID": "12D3KooWSxNXYpQtk7yUrstfXFDmvf5tKHosotyBnJTtBn2NhRsW"
        },
        "smdmitry_AR": {
            "IP": "mm2-smdmitry-ar.smdmitry.com",
            "PeerID": "12D3KooWJ3dEWK7ym1uwc5SmwbmfFSRmELrA9aPJYxFRrQCCNdwF"
        },
        "smdmitry_EU": {
            "IP": "mm2-smdmitry-eu.smdmitry.com",
            "PeerID": "12D3KooWJTYiU9CqVyycpMnGC96WyP1GE62Ng5g93AUe9wRx5g7W"
        },
        "smdmitry_SH": {
            "IP": "mm2-smdmitry-sh.smdmitry.com",
            "PeerID": "12D3KooWQP7PNNX5DSyhPX5igPQKQhet4KX7YaDqiGuNnarr4vRX"
        },
        "strob_SH": {
            "IP": "sh.strobfx.com",
            "PeerID": "12D3KooWFY5TmKpusUJ3jJBYK4va8xQchnJ6yyxCD7wZ2pWVK23p"
        },
        "strobnidan_SH": {
            "IP": "nidansh.strobfx.com",
            "PeerID": "12D3KooWH19JG75SJ6s5USwThxeArEuFnpeSFcUFCSrue1rdyAtM"
        },
        "yurii-khi_DEV": {
            "IP": "3p.yurii-khi.com",
            "PeerID": "12D3KooWLvPafSXHqLSzxKBsx2VhXPBvUYUxbCxuaR81usSLL7bE"
        },
        "nutellalicka_SH": {
            "IP": "vegemitegurgler.smk.dog",
            "PeerID": "12D3KooWJYhLQ2Zg6XLYYKiA713ZfyHcRCTq137ctygzb4iyWUs3"
        },
        "chmex_AR": {
            "IP": "1.ar.seed.adex.dexstats.info",
            "PeerID": "12D3KooWD3uwYqzDygMvU3jaJozEXfZiiRFnkVVwUgpu9kGqa5Yg"
        },
        "chmex_EU": {
            "IP": "1.eu.seed.adex.dexstats.info",
            "PeerID": "12D3KooWGP4ryfJHXjfnbXUWP6FJeDLiif8jMT8obQvCKMSPUB8X"
        },
        "chmex_SH": {
            "IP": "1.sh.seed.adex.dexstats.info",
            "PeerID": "12D3KooWE8Ju9SZyZrfkUgi25gFKv1Yc6zcQZ5GXtEged8rmLW3t"
        },
        "chmex1_SH": {
            "IP": "2.sh.seed.adex.dexstats.info",
            "PeerID": "12D3KooWRv8zmiGRUaqSdSPWu7xtxmKx8ebgco4RaufaNYnFhfpo"
        },
        "kolo_AR": {
            "IP": "ar.mm2.kolo.dev",
            "PeerID": "12D3KooWChiA68CtLcJELhdqeCu5vgn7QHwqHdbV6MwCVZYYvarD"
        },
        "kolo_EU": {
            "IP": "eu.mm2.kolo.dev",
            "PeerID": "12D3KooWSHaMt7fJME3hdwqHuBcP7oYrkK8DucPKU4urHdYa4wzc"
        },
        "kolox_AR": {
            "IP": "arx.mm2.kolo.dev",
            "PeerID": "12D3KooWRz5Xgc6uS4QPqtGBWS7drr6npTZsNU9VMcEy96eunT9w"
        },
        "nutellalicka_AR": {
            "IP": "dutchwink.smk.dog",
            "PeerID": "12D3KooWDr5DXt1Lww18q9QnkeU8yDYpeFrKmitEjSCD6cGdXxxQ"
        },
        "marmarachain_EU": {
            "IP": "mm2.marmara.io",
            "PeerID": "12D3KooWSuiC4ndibj47LQHLFFcipJFgKXvg1rqTh9hzW7k2u2Ni"
        },
        "who-biz_NA": {
            "IP": "adex.blur.cash",
            "PeerID": "12D3KooWQp97gsRE5LbcUPjZcP7N6qqk2YbxJmPRUDeKVM5tbcQH"
        },
        "webworker01_EU": {
            "IP": "eu2.webworker.sh",
            "PeerID": "12D3KooWGF5siktvWLtXoRKgbzPYHn4rib9Fu8HHJEECRcNbNoAs"
        },
        "webworker01_NA": {
            "IP": "na2.webworker.sh",
            "PeerID": "12D3KooWRiv4gFUUSy2772YTagkZYdVkjLwiXkdcrtDQQuEqQaJ9"
        },
        "ptyx_NA": {
            "IP": "kmdnn1.bfch.xyz",
            "PeerID": "12D3KooWRbTgCH4nU2XPU2thU8pFrUMFKvLjpkSxsMV84YCP6BVm"
        },
        "ptyx2_NA": {
            "IP": "kmdnn2.bfch.xyz",
            "PeerID": "12D3KooWPz265GktGEEKtv9oRKSVUc1LYGqEYDnMjCanm4mjL2ks"
        },
        "blackice_AR": {
            "IP": "shadowbit-ar.mm2.kmd.sh",
            "PeerID": "12D3KooWShhz3vfTqUXXVb9ivHeGBEEeMJvoda2ta8CVMhrX8RbZ"
        },
        "blackice_DEV": {
            "IP": "shadowbit-dev.mm2.kmd.sh",
            "PeerID": "12D3KooWDDZiyNn92StCdKXLLdxuYmkjJGPL5ezzyiJ2YVLMK56N"
        },
        "blackice_EU": {
            "IP": "shadowbit-eu.mm2.kmd.sh",
            "PeerID": "12D3KooWBT1UXwjqyavsDTVgWGeJkvrr8QgMScKpJF4oTLLgSk7k"
        },
        "ocean_AR": {
            "IP": "ocean-ar.mm2.kmd.sh",
            "PeerID": "12D3KooWBDHkhSVFe7YnGcZFrY8gaUUrpV2J8FwF3STqvBXCwFz8"
        },
        "computergenie_EU": {
            "IP": "cgeu.computergenie.gay",
            "PeerID": "12D3KooWGkPFi43Nq6cAcc3gib1iECZijnKZLgEf1q1MBRKLczJF"
        },
        "computergenie_NA": {
            "IP": "cg.computergenie.gay",
            "PeerID": "12D3KooWCJWT5PAG1jdYHyMnoDcxBKMpPrUVi9gwSvVLjLUGmtQg"
        },
        "van_EU": {
            "IP": "van.computergenie.gay",
            "PeerID": "12D3KooWMX4hEznkanh4bTShzCZNx8JJkvGLETYtdVw8CWSaTUfQ"
        },
        "sheeba_SH": {
            "IP": "sheeba.computergenie.gay",
            "PeerID": "12D3KooWC1P69a5TwpNisZYBXRgkrJDjGfn4QZ2L4nHZDGjcdR2N"
        },
        "nodeone_NA": {
            "IP": "nodeone.computergenie.gay",
            "PeerID": "12D3KooWBTNDr6ih5efzVSxXtDv9wcVxHNj8RCvUnpKfKb6eUYet"
        },
        "mcrypt_AR": {
            "IP": "mcrypt1.v6.rocks",
            "PeerID": "12D3KooWR3fgLdkKeU8mCkvN5ZeDBm9WtD1k8RAZYqSyAxLr3KZP"
        },
        "mcrypt_SH": {
            "IP": "mcrypt2.v6.rocks",
            "PeerID": "12D3KooWCDAPYXtNzC3x9kYuZySSf1WtxjGgasxapHEdFWs8Bep3"
        },
        "tonyl_AR": {
            "IP": "ar.farting.pro",
            "PeerID": "12D3KooWEMTeavnNtPPYr1u4aPFB6U39kdMD32SU1EpHGWqMpUJk"
        },
        "tonyl_DEV": {
            "IP": "dev.farting.pro",
            "PeerID": "12D3KooWDubAUWDP2PgUXHjEdN3SGnkszcyUgahALFvaxgp9Jcyt"
        }
    },
    "Season_7": {
        "dragonhound_AR": {
            "IP": "ar.smk.dog",
            "PeerID": "12D3KooWSUABQ2beSQW2nXLiqn4DtfXyqbJQDd2SvmgoVwXjrd9c"
        },
        "dragonhound_EU": {
            "IP": "eu.smk.dog",
            "PeerID": "12D3KooWDgFfyAzbuYNLMzMaZT9zBJX9EHd38XLQDRbNDYAYqMzd"
        },
        "dragonhound_NA": {
            "IP": "na.smk.dog",
            "PeerID": "12D3KooWSmizY35qrfwX8qsuo8H8qrrvDjXBTMRBfeYsRQoybHaA"
        },
        "dragonhound_DEV": {
            "IP": "dev.smk.dog",
            "PeerID": "12D3KooWNGGBfPWQbubupECdkYhj1VomMLUUAYpsR2Bo3R4NzHju"
        }
    }
}

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()


def mm2_proxy(method, params=None):
    if not params:
        params = {}
    params.update({
        "method": method,
        "userpass": MM2_USERPASS,
        })
    r = requests.post(MM2_IP, json.dumps(params))
    print(r.json())
    return r


def get_active_mm2_versions(ts):
    active_versions = []
    for version in VERSION_DATA:
        if int(ts) < VERSION_DATA[version]["end"]:
            active_versions.append(version)
    return active_versions


def add_notaries():
    # Add to tracking
    for season in seednodes:
        for notary in seednodes[season]:
            params = {
                "mmrpc": "2.0",
                "params": {
                    "name": notary,
                    "address": seednodes[season][notary]["IP"],
                    "peer_id": seednodes[season][notary]["PeerID"]
                }
            }
            print(notary)
            r = mm2_proxy('add_node_to_version_stat', params)

def remove_notaries():
    # Add to tracking
    for season in seednodes:
        for notary in seednodes[season]:
            params = {
                "mmrpc": "2.0",
                "params": {
                    "name": notary
                }
            }
            print(notary)
            r = mm2_proxy('remove_node_from_version_stat', params)


def get_local_version():
    return mm2_proxy('version')


def start_stats_collection():
    # set to every 30 minutes
    params = {
        "mmrpc": "2.0",
        "params": {
            "interval":1800,
        }
    }
    print("Starting stats collection...")
    r = mm2_proxy('start_version_stat_collection', params)


def empty_pg_table():
    rows = CURSOR.execute("DELETE FROM seednode_version_stats;")
    CONN.commit()
    print('Deleted', CURSOR.rowcount, 'records from seednode_version_stats PgSQL table.')


def empty_sqlite_table(table):
    rows = cursor.execute(f"DELETE FROM {table};")
    conn.commit()
    print('Deleted', cursor.rowcount, 'records from the table.')


def get_version_stats_from_sqlite_db(from_time=0, version=None):
    sql = f"SELECT * FROM stats_nodes WHERE version = '{version}' and timestamp > {from_time}"
    if not version:
        sql = f"SELECT * FROM stats_nodes WHERE version != '' and timestamp > {from_time}"
    print(sql)
    rows = cursor.execute(sql).fetchall()
    resp = []
    for row in rows:
        resp.append(dict(row))
    print(f"{len(resp)} records returned")
    return resp


def get_version_stats_from_db():
    rows = cursor.execute("SELECT * FROM stats_nodes WHERE version != ''").fetchall()
    for row in rows:
        print(dict(row))


def get_registered_nodes_from_db():
    rows = cursor.execute("SELECT * FROM nodes;").fetchall()
    print("---------")
    for row in rows:
        print(dict(row))    
    print("---------")

def deregister_nodes_from_db():
    for season in seednodes:
        for notary in seednodes[season]:
            cursor.execute(f"DELETE FROM nodes where name = '{notary}';")
            cursor.commit()

def update_seednode_version_stats_row(row_data):
    try:
        timestamp = row_data[3]
        season = validate.get_season(timestamp)
        sql = f"INSERT INTO seednode_version_stats \
                    (name, season, version, timestamp, error, score) \
                VALUES (%s, %s, %s, %s, %s, %s) \
                ON CONFLICT ON CONSTRAINT unique_mm2_version_stat \
                DO UPDATE SET \
                    season='{season}', version='{row_data[2]}', \
                    timestamp='{timestamp}', error='{row_data[4]}', \
                    score='{row_data[5]}';"

        CURSOR.execute(sql, row_data)
        CONN.commit()

    except Exception as e:
        logger.error(f"Exception in [update_seednode_version_stats_row]: {e}")
        logger.error(f"[update_seednode_version_stats_row] sql: {sql}")
        logger.error(f"[update_seednode_version_stats_row] row_data: {row_data}")
        CONN.rollback()

def rectify_scores():
    for commithash in VERSION_DATA:
        start_time = VERSION_DATA[commithash]["start"]
        end_time = VERSION_DATA[commithash]["end"]
        print(f"\n======= commithash: {commithash} =======")
        print(f"start_time: {start_time}")
        print(f"end_time: {end_time}")

        sql = f"SELECT * FROM seednode_version_stats WHERE version LIKE '%{commithash}%' AND timestamp < {end_time} AND timestamp > {start_time};"
        CURSOR.execute(sql)
        print(f"Records valid for scoring: {CURSOR.rowcount}")
        sql = f"UPDATE seednode_version_stats SET score = 0.2 WHERE version LIKE '%{commithash}%' AND timestamp < {end_time} AND timestamp > {start_time};"
        CURSOR.execute(sql)
        CONN.commit()

        sql = f"SELECT * FROM seednode_version_stats WHERE version LIKE '%{commithash}%' AND timestamp > {end_time};"
        CURSOR.execute(sql)
        print(f"Records after end time: {CURSOR.rowcount}")
        sql = f"UPDATE seednode_version_stats SET score = 0 WHERE version LIKE '%{commithash}%' AND timestamp > {end_time};"
        CURSOR.execute(sql)
        CONN.commit()


def get_version_stats_from_pgsql_db():
    sql = f"SELECT * FROM seednode_version_stats;"
    CURSOR.execute(sql)
    return get_results_or_none(CURSOR)


def get_version_list_from_pgsql_db():
    sql = f"SELECT DISTINCT version FROM seednode_version_stats;"
    CURSOR.execute(sql)
    return get_results_or_none(CURSOR)


def get_pgsql_latest():
    sql = f"SELECT MAX(timestamp) FROM seednode_version_stats;"
    CURSOR.execute(sql)
    try:
        results = CURSOR.fetchone()[0]
        return results
    except:
        return 0


def round_ts_to_hour(timestamp):
    return round(int(timestamp)/3600)*3600


def get_version_score(version, timestamp, notary, season, wss_detected=False):
    active_versions_at = get_active_mm2_versions(timestamp)
    print(f"mm2 active versions: {active_versions_at}")
    for v in active_versions_at:
        if version.find(v) > -1:
            if wss_detected:
                return 0.2
            if test_wss(notary, season):
                return 0.2
            return 0.01
    return 0


def test_wss(notary, season):
    
    if season in seednodes:
        url = seednodes[season][notary]["IP"]
        peer_id = seednodes[season][notary]["PeerID"]
        data = {"userpass": "userpass"}
        resp = electrum.get_from_electrum_ssl(url, 38900, "version", data)
        if str(resp).find("read operation timed out") > -1:
            print(f"{notary}: WSS connection detected...")
            return True
        else:
            print(f"{notary}: {resp}")
        return False


def migrate_sqlite_to_pgsql(ts):
    print(f"Migrating to pgsql from {ts}")
    wss_confirmed = []
    rows = get_version_stats_from_sqlite_db()

    if ts:
        rows = get_version_stats_from_sqlite_db(ts)

    for row in rows:
        print(row)
        if row["version"] != '':
            wss_detected = False
            hr_timestamp = round_ts_to_hour(row["timestamp"])   
            season = validate.get_season(hr_timestamp)

            if row["name"] not in wss_confirmed:
                if test_wss(row["name"], season):
                    wss_confirmed.append(row["name"])

            if row["name"] in wss_confirmed:
                wss_detected = True
            
            score = get_version_score(row["version"], hr_timestamp, row["name"], season, wss_detected)
            row_data = (row["name"], season, row["version"], hr_timestamp, row["error"], score)

            print(row_data)
            update_seednode_version_stats_row(row_data)

def import_seednode_stats(season):
    resp = requests.get("http://stats.kmd.io/api/source/seednode_version_stats/").json()

    for i in resp["results"]:
        row_data = (i["name"], i["season"], i["version"], i["timestamp"], i["error"], i["score"])
        print(row_data)
        update_seednode_version_stats_row(row_data)

    if resp["next"]:
        while resp["next"]:
            resp = requests.get(resp["next"]).json()

            for i in resp["results"]:
                row_data = (i["name"], i["season"], i["version"], i["timestamp"], i["error"], i["score"])
                print(row_data)
                update_seednode_version_stats_row(row_data)




if __name__ == '__main__':

    active_versions = get_active_mm2_versions(time.time())
    logger.info(f"Local MM2 version: {get_local_version().json()}")
    print(f"active_versions: {active_versions}")

    if len(sys.argv) > 1:

        # Clears tables
        if sys.argv[1] == 'empty':
            empty_pg_table()

        # Starts stats collection in sqliteDB
        # mm2 Dockerfile takes care of this in init.sh
        elif sys.argv[1] == 'start':
            start_stats_collection()

        # Returns registered nodes
        elif sys.argv[1] == 'nodes':
            get_registered_nodes_from_db()

        # Run manually to register nodes via JSON file
        elif sys.argv[1] == 'register':
            remove_notaries()
            add_notaries()

        # This is what gets cron'd
        elif sys.argv[1] == 'migrate':
            latest_record = get_pgsql_latest()
            logger.info(f"Latest entry in pgsql db: {latest_record}")
            migrate_sqlite_to_pgsql(latest_record)

        # outputs SQLite data
        elif sys.argv[1] == 'sqlite_data':
            sqlite_version_stats = get_version_stats_from_sqlite_db(0)
            print(f"sqlite_version_stats: {sqlite_version_stats}")

        # outputs pgSQL data
        elif sys.argv[1] == 'pgsql_data':
            pgsql_version_stats = get_version_stats_from_pgsql_db()
            print(f"pgsql_version_stats: {pgsql_version_stats}")

        # outputs pgSQL data
        elif sys.argv[1] == 'versions_list':
            pgsql_version_list = get_version_list_from_pgsql_db()
            print(f"pgsql_version_list: {pgsql_version_list}")

        # outputs pgSQL data
        elif sys.argv[1] == 'rectify_scores':
            result = rectify_scores()

        # tests WSS connection
        elif sys.argv[1] == 'wss_test':
            for season in seednodes:
                for notary in seednodes[season]:
                    test_wss(notary, season)
                
        # import data from other server
        elif sys.argv[1] == 'import':
            for season in seednodes:
                import_seednode_stats(season)

        else:
            print("invalid param, must be in [empty, start, nodes, register, migrate, sqlite_data, pgsql_data, wss_test, import]")

    else:
        print("no param given, must be in [empty, start, nodes, register, migrate, sqlite_data, pgsql_data, wss_test, import]")

    #get_version_stats_from_db()
    conn.close()
    CONN.close()
