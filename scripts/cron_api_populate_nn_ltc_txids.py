#!/usr/bin/env python3
import json
import time
import logging
import logging.handlers
import requests
from decimal import *
from datetime import datetime as dt
import datetime
import dateutil.parser as dp

from lib_notary import get_new_nn_ltc_txids, get_notary_from_ltc_address, get_notary_last_ntx, get_season_from_ltc_addresses

from lib_table_update import update_nn_ltc_tx_notary_from_addr
from lib_table_select import get_existing_nn_ltc_txids

from lib_api import get_ltc_tx_info

from models import ltc_tx_row, last_notarised_row, ntx_records_row

from lib_const import LTC_NTX_ADDR, NOTARY_LTC_ADDRESSES, NN_LTC_ADDRESSES_DICT, ALL_SEASON_NOTARY_LTC_ADDRESSES, ALL_SEASON_NOTARIES, ALL_SEASON_NN_LTC_ADDRESSES_DICT, THIS_SERVER
from lib_db import CONN, CURSOR
from known_txids import *

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d-%b-%y %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def get_linked_addresses(addr=None, notary=None):
    linked_addresses = {}
    sql = f"SELECT DISTINCT address, notary from nn_ltc_tx"
    conditions = [f"address='{addr}'"]
    if notary:
        conditions = [f"notary = '{notary}' or notary = '{notary} (linked)'"]

    if len(conditions) > 0:
        sql += " where "
        sql += " and ".join(conditions)    
    sql += ";"

    CURSOR.execute(sql)
    address_rows = CURSOR.fetchall()

    if len(address_rows) > 0:

        for row in address_rows:
            address = row[0]
            notary = row[1].replace(" (linked)", "")

            if notary in ALL_SEASON_NOTARIES:

                if notary not in linked_addresses:
                    if addr not in LL_SEASON_NN_BTC_ADDRESSES_DICT:
                        linked_addresses.update({notary:[address]})

                else:
                    linked_addresses[notary].append(address)

    return linked_addresses

def is_linked_address(addr, notary=None):
    linked_addresses = get_linked_addresses(addr, notary)
    if len(linked_addresses) > 0:
        return True
    else:
        return False

def is_notary_address(addr):
    if addr in ALL_SEASON_NOTARY_LTC_ADDRESSES:
        return True
    return False

def detect_ntx(vins, vouts):
    logger.info(f"LTC_NTX_ADDR {LTC_NTX_ADDR}")
    logger.info(f"addresses {addresses}")
    logger.info(f"len(vouts) {len(vouts)}")

    if LTC_NTX_ADDR in addresses and len(vouts) == 2:
        for vin in vins:
            logger.info(vin["output_value"])
            if vin["output_value"] != 10000:
                logger.info('vin["output_value"] != 10000')
                return False
            logger.info(vin["addresses"][0])
            logger.info(ALL_SEASON_NOTARY_LTC_ADDRESSES)
            if vin["addresses"][0] not in ALL_SEASON_NOTARY_LTC_ADDRESSES:
                logger.info('vin["addresses"][0] not in ALL_SEASON_NOTARY_LTC_ADDRESSES')
                return False

        for vout in vouts:
            logger.info(f"LTC_NTX_ADDR {LTC_NTX_ADDR}")
            logger.info(f"vout['addresses'] {vout['addresses']}")
            if vout["addresses"] is not None:
                if vout["addresses"][0] != LTC_NTX_ADDR:
                    logger.info('vout["addresses"] != LTC_NTX_ADDR')
                    return False
        return True
    else:
        return False

def detect_replenish(vins, vouts):

    vin_notaries = []
    vin_non_notary_addresses = []
    for vin in vins:
        address = vin["addresses"][0]
        if is_notary_address(address):
            notary = ALL_SEASON_NN_LTC_ADDRESSES_DICT[address]
            vin_notaries.append(notary)
        elif is_linked_address(address, "dragonhound_NA"):
            notary = "dragonhound_NA"
            vin_notaries.append(notary)
        else:
            vin_non_notary_addresses.append(address)
    
    replenish_vin = False
    if len(list(set(vin_notaries))) == 1:
        if vin_notaries[0] == "dragonhound_NA":
            replenish_vin = True

    vout_notaries = []
    vout_non_notary_addresses = []
    for vout in vouts:
        if vout["addresses"]:
            sats = vout["value"]
            address = vout["addresses"][0]
            if is_notary_address(address):
                if sats >= 1000000:
                    notary = ALL_SEASON_NN_LTC_ADDRESSES_DICT[address]
                    if notary != "dragonhound_NA":
                        vout_notaries.append(notary)
            elif not is_linked_address(address):
                vout_non_notary_addresses.append(address)

    replenish_vout = False
    if len(vout_notaries) > 0:
        replenish_vout = True

    if replenish_vin and replenish_vout:
        for addr in vin_non_notary_addresses:
            if addr not in LL_SEASON_NN_BTC_ADDRESSES_DICT:
                update_nn_ltc_tx_notary_from_addr("dragonhound_NA (linked)", addr)
        for addr in vout_non_notary_addresses:

            if addr not in LL_SEASON_NN_BTC_ADDRESSES_DICT:
                update_nn_ltc_tx_notary_from_addr("dragonhound_NA (linked)", addr)
        return True
    return False

def detect_consolidate(vins, vouts):
    vin_notaries = []
    vin_non_notary_addresses = []
    for vin in vins:
        address = vin["addresses"][0]
        if is_notary_address(address):
            notary = ALL_SEASON_NN_LTC_ADDRESSES_DICT[address]
            vin_notaries.append(notary)
        else:
            vin_non_notary_addresses.append(address)

    if len(list(set(vin_notaries))) == 1:
        notary = vin_notaries[0]

        vout_notaries = []
        vout_non_notary_addresses = []
        for vout in vouts:
            address = vout["addresses"][0]
            if is_notary_address(address):
                notary = ALL_SEASON_NN_LTC_ADDRESSES_DICT[address]
                vout_notaries.append(notary)
            else:
                vout_non_notary_addresses.append(address)

        if len(list(set(vout_notaries))) == 1 and is_notary_address(vouts[0]["addresses"][0]):
            if notary == vout_notaries[0]:
                for addr in vin_non_notary_addresses:
                    if addr not in ALL_SEASON_NN_LTC_ADDRESSES_DICT:
                        update_nn_ltc_tx_notary_from_addr(f"{notary} (linked)", addr)
                for addr in vout_non_notary_addresses:
                    if addr not in ALL_SEASON_NN_LTC_ADDRESSES_DICT:
                        update_nn_ltc_tx_notary_from_addr(f"{notary} (linked)", addr)
                return True

    return False

def update_notary_linked_vins(vins):
    vin_notaries = []
    vin_non_notary_addresses = []
    for vin in vins:
        address = vin["addresses"][0]
        if is_notary_address(address):
            notary = ALL_SEASON_NN_LTC_ADDRESSES_DICT[address]
            vin_notaries.append(notary)
        else:
            vin_non_notary_addresses.append(address)

    if len(list(set(vin_notaries))) == 1 and len(vin_non_notary_addresses) > 0:
        for addr in vin_non_notary_addresses:
            if addr not in LL_SEASON_NN_BTC_ADDRESSES_DICT:
                update_nn_ltc_tx_notary_from_addr(f"{notary} (linked)", address)


def detect_intra_notary(vins, vouts):
    for vin in vins:
        address = vin["addresses"][0]
        if is_notary_address(address):
            notary = ALL_SEASON_NN_LTC_ADDRESSES_DICT[address]
        else:
            return False

    for vout in vouts:
        address = vout["addresses"][0]
        if is_notary_address(address):
            notary = ALL_SEASON_NN_LTC_ADDRESSES_DICT[address]
        else:
            return False

    return True

def detect_spam(txid_data, addresses):
    if '1See1xxxx1memo1xxxxxxxxxxxxxBuhPF' in addresses:        
        txid_data.input_sats = 0
        txid_data.output_sats = 0
        txid_data.input_index = 0
        txid_data.output_index = 0
        txid_data.category = "SPAM"
        for vout in vouts:
            txid_data.address = addresses[0]
            txid_data.notary = get_notary_from_ltc_address(txid_data.address, txid_data.season)
            if txid_data.notary != "non-NN":
                txid_data.update()
        return True
    return False

def detect_cipi_faucet(txid_data, addresses, vins):
    if vins[0]["addresses"][0] == CIPI_FAUCET_ADDR and len(addresses) == 2:
        addresses.remove(CIPI_FAUCET_ADDR)
        txid_data.category = "cipi_faucet"
        txid_data.input_sats = -99
        txid_data.output_sats = -99
        txid_data.input_index = -99
        txid_data.output_index = -99
        txid_data.address = addresses[0]
        txid_data.notary = get_notary_from_ltc_address(txid_data.address, txid_data.season)
        txid_data.update()
        return True
    return False

def detect_split(txid_data, addresses):
    if len(addresses) == 1:
        txid_data.category = "Split"
        txid_data.input_sats = -99
        txid_data.output_sats = -99
        txid_data.input_index = -99
        txid_data.output_index = -99
        txid_data.address = addresses[0]
        txid_data.notary = get_notary_from_ltc_address(txid_data.address, txid_data.season)
        txid_data.update()
        return True
    return False

season = "Season_5_Testnet"
i = 0
num_addr = len(NOTARY_LTC_ADDRESSES[season])


notary_last_ntx = get_notary_last_ntx("LTC")

NOTARY_LTC_ADDRESSES[season].reverse()
for notary_address in NOTARY_LTC_ADDRESSES[season]:
    i += 1

    if notary_address in NN_LTC_ADDRESSES_DICT[season]:
        notary_name = NN_LTC_ADDRESSES_DICT[season][notary_address]
    else:
        notary_name = "non-NN"

    existing_txids = get_existing_nn_ltc_txids(notary_address)
    txids = get_new_nn_ltc_txids(existing_txids, notary_address)
    # txids = ["a91ee826138ac209e1c03ea599d86918ece7bed436b14dbeb231e98a82d16317"]

    logger.info(f"{len(existing_txids)} EXIST IN DB FOR {notary_address} | {notary_name} {season} ({i}/{num_addr})")
    logger.info(f"{len(txids)} NEW TXIDs TO PROCESS FOR {notary_address} | {notary_name} {season} ({i}/{num_addr})")

    num_txids = len(txids)

    j = 0
    for txid in txids:
        j += 1
        # Get tx data from Blockcypher API
        logger.info(f">>> Processing txid {j}/{num_txids}")
        tx_info = get_ltc_tx_info(txid)
        if 'fees' in tx_info:
            txid_data = ltc_tx_row()
            txid_data.txid = txid
            txid_data.address = notary_address
            txid_data.fees = tx_info['fees']

            txid_data.num_inputs = tx_info['vin_sz']
            txid_data.num_outputs = tx_info['vout_sz']

            txid_data.block_hash = tx_info['block_hash']
            txid_data.block_height = tx_info['block_height']

            block_time_iso8601 = tx_info['confirmed']
            parsed_time = dp.parse(block_time_iso8601)
            txid_data.block_time = parsed_time.strftime('%s')
            txid_data.block_datetime = dt.utcfromtimestamp(int(txid_data.block_time))

            addresses = tx_info['addresses']
            txid_data.season = get_season_from_ltc_addresses(addresses[:], txid_data.block_time)

            vouts = tx_info["outputs"]
            vins = tx_info["inputs"]
            update_notary_linked_vins(vins)

            ## CATEGORIES ##
            # SPAM index/outputs = 0
            # NTX
            # SPLIT index/outputs = -99
            # CONSOLIDATE (Add Later)
            #   - vins from notary or linked address, to same notary or linked address. If single non-NN vout, tag as NN-linked.
            #   - Could be confused with REPLENISH, make sure no other notaries involved.
            # REPLENISH (Add Later)
            #   - large sat value (0.01 LTC or higher) to multiple notaries, generally from dragonhound or dragonhound linked address. Single non-NN vout, tag as dragonhound linked.
            #   - very large sat value to dragonhound (0.4 LTC or higher). tag vins as REPLENISH SOURCE.
            # OTHER (FALL BACK)

            # Detect Split (single row only)
            if detect_split(txid_data, addresses):
                logger.info("SPLIT detected")

            else:                    
                if detect_ntx(vins, vouts):
                    txid_data.category = "NTX"
                elif detect_replenish(vins, vouts):
                    txid_data.category = "Replenish"
                elif detect_consolidate(vins, vouts) or txid in dragonhound_consolidate or txid in strob_consolidate or txid in webworker_2step_consolidate:
                    txid_data.category = "Consolidate"
                elif detect_intra_notary(vins, vouts):
                    txid_data.category = "Intra-Notary"
                else:
                    txid_data.category = "Other"

                input_index = 0
                for vin in vins:
                    txid_data.output_sats = -1
                    txid_data.output_index = -1
                    txid_data.input_sats = vin['output_value']
                    txid_data.input_index = input_index
                    txid_data.address = vin["addresses"][0]
                    txid_data.notary = get_notary_from_ltc_address(txid_data.address, txid_data.season)
                    txid_data.update()
                    input_index += 1

                output_index = 0
                for vout in vouts:
                    if vout["addresses"] is not None:
                        txid_data.input_index = -1
                        txid_data.input_sats = -1
                        txid_data.address = vout["addresses"][0]
                        txid_data.notary = get_notary_from_ltc_address(txid_data.address, txid_data.season)
                        txid_data.output_sats = vout['value']
                        txid_data.output_index = output_index
                        txid_data.update()
                        output_index += 1

                # update notary_last_ntx
                if txid_data.category == "NTX":
                    notary_list = []
                    notary_addresses = []
                    for vin in vins:
                        row = last_notarised_row()
                        row.notary = get_notary_from_ltc_address(vin["addresses"][0], season)
                        notary_list.append(row.notary)
                        notary_addresses.append(vin["addresses"][0])
                        if row.notary in notary_last_ntx:
                            last_ltc_ntx_ht = notary_last_ntx[row.notary]["LTC"]
                        else:
                            last_ltc_ntx_ht = 0
                        if last_ltc_ntx_ht < txid_data.block_height:
                            row.season = season
                            row.chain = "LTC"
                            row.txid = txid_data.txid
                            row.block_height = txid_data.block_height
                            row.block_time = txid_data.block_time
                            row.update()
                    for vout in vouts:
                        if 'data_hex' in vout:
                            opret = vout['data_hex']

                            r = requests.get(f'{THIS_SERVER}/api/tools/decode_opreturn/?OP_RETURN={opret}')
                            kmd_ntx_info = r.json()

                            ac_ntx_height = kmd_ntx_info['notarised_block']
                            ac_ntx_blockhash = kmd_ntx_info['notarised_blockhash']

                            # Update "notarised" table
                            row = ntx_records_row()
                            row.chain = "LTC"
                            row.block_height = txid_data.block_height
                            row.block_time = txid_data.block_time
                            row.block_datetime = txid_data.block_datetime
                            row.block_hash = txid_data.block_hash
                            row.notaries = notary_list
                            row.notary_addresses = notary_addresses
                            row.ac_ntx_blockhash = ac_ntx_blockhash
                            row.ac_ntx_height = ac_ntx_height
                            row.txid = txid_data.txid
                            row.opret = opret
                            row.season = txid_data.season
                            row.server = "testnet"
                            row.scored = True
                            row.btc_validated = "N/A"
                            row.update()

            logger.info(f"TXID: {txid} ({txid_data.category})")
        else:
            logger.warning(f"Fees not in txinfo for {txid}! Likely unconfirmed...")

CURSOR.close()
CONN.close()
