#!/usr/bin/env python3
import time
import math
import lib_electrum
import logging
import logging.handlers
from lib_notary import *
from lib_rpc import def_credentials
import threading
from lib_const import *

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                               datefmt='%d-%b-%y %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

rpc = def_credentials("KMD")

'''
This script checks notary balances for all dpow coins via electrum servers,
and any pending KMD rewards then stores data in db
It should be run as a cronjob every hour or so (takes about an 10 min to run).
'''

class electrum_thread(threading.Thread):
    def __init__(self, conn, cursor, notary, chain, pubkey, addr, season):
        threading.Thread.__init__(self)
        self.conn = conn
        self.cursor = cursor
        self.notary = notary
        self.chain = chain
        self.pubkey = pubkey
        self.addr = addr
        self.season = season
    def run(self):
        thread_electrum(self.conn, self.cursor, self.notary,
                        self.chain, self.pubkey, self.addr, self.season)

def thread_electrum(conn, cursor, notary, chain, pubkey, addr, season):
    if season.lower().find("third") != -1:
        node = 'third party'
    else:
        node = 'main'
    if season.find("Season_3") != -1:
        season = "Season_3"
    if season.find("Season_4") != -1:
        season = "Season_4"
    balance = lib_electrum.get_balance(chain, pubkey, addr, notary, node)
    if balance != -1:
        row_data = (notary, chain, balance, addr,
                    season, node, int(time.time()))
        update_balances_tbl(conn, cursor, row_data)
        logger.info("["+chain+"] ["+season+"] ["+node+"] [" \
                +str(balance)+"] ["+notary+"] ["+addr+"]")

conn = connect_db()
cursor = conn.cursor()

KOMODO_ENDOFERA = 7777777
LOCKTIME_THRESHOLD = 500000000
MIN_SATOSHIS = 1000000000
ONE_MONTH_CAP_HARDFORK = 1000000
ONE_HOUR = 60
ONE_MONTH = 31 * 24 * 60
ONE_YEAR = 365 * 24 * 60
DEVISOR = 10512000

tiptime = rpc.getinfo()['tiptime']

def get_kmd_rewards(season):
    nn_utxos = {}
    bitcoin.params = coin_params["KMD"]
    for notary in NOTARY_PUBKEYS[season]:
        addr = str(P2PKHBitcoinAddress.from_pubkey(x(NOTARY_PUBKEYS[season][notary])))
        utxos = rpc.getaddressutxos({"addresses": [addr]})
        notary = known_addresses[addr]
        utxo_count = len(utxos)
        update_time = int(time.time())
        nn_utxos.update({
            addr:{
                "notary":notary,
                "utxo_count": utxo_count,
                "eligible_utxos":{},
                "update_time": update_time
            }
        })
        total_rewards = 0
        balance = 0
        oldest_utxo_block = 99999999999
        for utxo in utxos:
            balance += utxo['satoshis']/100000000
            if utxo['height'] < oldest_utxo_block:
                oldest_utxo_block = utxo['height']
            if utxo['height'] < KOMODO_ENDOFERA and utxo['satoshis'] >= MIN_SATOSHIS:
                try:
                    locktime = rpc.getrawtransaction(utxo["txid"], 1)['locktime']
                    coinage = math.floor((tiptime-locktime)/ONE_HOUR)
                    if coinage >= ONE_HOUR and locktime >= LOCKTIME_THRESHOLD:
                        limit = ONE_YEAR
                        if utxo['height'] >= ONE_MONTH_CAP_HARDFORK:
                            limit = ONE_MONTH
                        reward_period = min(coinage, limit) - 59
                        rewards = math.floor(utxo['satoshis']/DEVISOR)*reward_period
                        if rewards < 0:
                            logger.info("Rewards should never be negative!")
                        nn_utxos[addr]['eligible_utxos'].update({
                            utxo['txid']:{
                                "locktime":locktime,
                                "sat_rewards":rewards,
                                "kmd_rewards":rewards/100000000,
                                "satoshis":utxo['satoshis'],
                                "block_height":utxo['height']
                            }
                        })
                        total_rewards += rewards/100000000
                except:
                    pass
        eligible_utxo_count = len(nn_utxos[addr]['eligible_utxos'])
        if oldest_utxo_block == 99999999999:
            oldest_utxo_block = 0
        nn_utxos[addr].update({
            "eligible_utxo_count":eligible_utxo_count,
            "oldest_utxo_block":oldest_utxo_block,
            "kmd_balance":balance,
            "total_rewards":total_rewards
        })
        utxo_txids = list(nn_utxos[addr]['eligible_utxos'].keys())
        logger.info(notary+": "+str(balance)+" KMD balance, " \
               +str(total_rewards)+" rewards")
        logger.info("Oldest block: "+str(oldest_utxo_block))
        row_data = (addr, notary, utxo_count, eligible_utxo_count,
                   oldest_utxo_block, balance, total_rewards,
                   update_time)

        update_rewards_tbl(conn, cursor, row_data)

def get_balances(this_season):
    thread_list = {}

    for season in notary_addresses:

        # update only current season
        if season.find(this_season) != -1:

            for notary in notary_addresses[season]:
                thread_list.update({notary:[]})

                for chain in notary_addresses[season][notary]:
                    addr = notary_addresses[season][notary][chain]
                    pubkey = NOTARY_PUBKEYS[season][notary]

                    # check only notarising addresses
                    if season.find("third_party") == -1:
                        if chain not in third_party_coins:
                            check_bal = True
                    elif chain in third_party_coins or chain == "KMD":
                        check_bal = True

                    if check_bal:
                        thread_list[notary].append(electrum_thread(conn, cursor, notary, chain, pubkey, addr, season))

                for thread in thread_list[notary]:
                    thread.start()
                time.sleep(4) # 4 sec sleep = 15 min runtime.

season = get_season(int(time.time()))

get_balances(season)
get_kmd_rewards(season)

cursor.close()
conn.close()