#!/usr/bin/env python3
from lib_const import *
import lib_api
import lib_electrum
import lib_query
from lib_helper import is_postseason, handle_translate_coins


def check_excluded_coins(season, server, coin):
    if season in DPOW_EXCLUDED_COINS: 
        if coin in DPOW_EXCLUDED_COINS[season]:
            return "Unofficial", "Unofficial"
    return season, server


def validate_epoch_coins(epoch_coins, season):
    if len(epoch_coins) == 0:
        return False
    for coin in epoch_coins:
        if season in DPOW_EXCLUDED_COINS:
            if coin in DPOW_EXCLUDED_COINS[season]:
                logger.warning(f"{coin} in DPOW_EXCLUDED_COINS[{season}]")
                return False
    return True

def get_season_from_block(block):
    if not isinstance(block, int):
        block = int(block)
    for season in SEASONS_INFO:
        if season.find("Testnet") == -1:
            start_block = SEASONS_INFO[season]['start_block']
            end_block = SEASONS_INFO[season]['end_block']
            if block >= start_block and block <= end_block:
                return season
    return None


def get_coin_epoch_at(season, server, coin, timestamp):
    if season in DPOW_EXCLUDED_COINS: 
        if coin not in DPOW_EXCLUDED_COINS[season]:
            if int(timestamp) >= SEASONS_INFO[season]["start_time"]:
                if int(timestamp) <= SEASONS_INFO[season]["end_time"]:
                    if coin in ["KMD", "BTC", "LTC"]:
                            if int(timestamp) <= SEASONS_INFO[season]["end_time"]:
                                return f"{coin}"

            epochs = lib_query.get_epochs(season, server)
            for epoch in epochs:
                if coin in epoch["epoch_coins"]:
                    if int(timestamp) >= epoch["epoch_start"]:
                        if int(timestamp) <= epoch["epoch_end"]:
                            return epoch["epoch"]

    return "Unofficial"


def validate_season_server_epoch(season, server, notary_addresses, block_time, coin):
    if season in DPOW_EXCLUDED_COINS:
        if coin in DPOW_EXCLUDED_COINS[season]:
            season = "Unofficial"
            server = "Unofficial"
            epoch = "Unofficial"
    season, server = get_season_server_from_addresses(notary_addresses, coin)
    epoch = get_coin_epoch_at(season, server, coin, block_time)
    return season, server, epoch


def get_server_from_kmd_address(season, address):
    if server in SEASONS_INFO:
        for server in ["Main", "Third_Party"]:
            if server in SEASONS_INFO[season]:
                if address in SEASONS_INFO[season]["servers"][server]["addresses"]["KMD"]:
                    return server
    return "Unofficial"


def handle_dual_server_coins(server, coin, addr=None):
    coin = handle_translate_coins(coin)

    if coin in ["GLEEC-OLD"]:
        server = "Third_Party"
        
    if coin in ["GLEEC"]:
        if server == "Third_Party":
            coin ="GLEEC-OLD"

    return server, coin


def get_scored(score_value):
    if score_value > 0:
        return True
    else:
        return False


def get_coin_epoch_score_at(season, server, coin, timestamp):
    if season in DPOW_EXCLUDED_COINS: 
        if coin not in DPOW_EXCLUDED_COINS[season]:
            if coin in ["BTC", "LTC"]:
                return 0
            if coin in ["KMD"]:
                season_start = SEASONS_INFO[season]["start_time"]
                season_end = SEASONS_INFO[season]["end_time"]
                if int(timestamp) >= season_start and int(timestamp) <= season_end:
                    return 0.0325
                return 0

            active_coins, num_coins = get_server_active_scoring_dpow_coins_at_time(
                                            season, server, timestamp
                                        )
            if coin in active_coins:
                return calc_epoch_score(server, num_coins)
    return 0


def calc_epoch_score(server, num_coins):
    if server == "Main":
        return round(0.8698/num_coins, 8)
    elif server == "Third_Party":
        return round(0.0977/num_coins, 8)
    elif server == "KMD":
        return round(0.0325/num_coins, 8)
    elif server == "Testnet":
        return round(0.0977/num_coins, 8)
    else:
        return 0


def get_season_server_from_addresses(address_list, coin):

    if len(address_list) == 13:

        for address in address_list:
            if address not in KNOWN_ADDRESSES:
                return "Unofficial", "Unofficial"

        tx_coin = "KMD"
        if coin in ["BTC", "KMD", "LTC"]:
            tx_coin = coin

        for season in SEASONS_INFO:
            notary_seasons = []
            for server in SEASONS_INFO[season]["servers"]:
                if server != "Unofficial":
                    if coin == "OOT":
                        print(SEASONS_INFO[season]["servers"][server]["addresses"].keys())
                    if coin in SEASONS_INFO[season]["servers"][server]["addresses"]:
                        for address in address_list:
                            if address in SEASONS_INFO[season]["servers"][server]["addresses"][tx_coin]:
                                notary_seasons.append(season)
                                if len(notary_seasons) == 13:
                                    if len(set(notary_seasons)) == 1:
                                        if coin in ["BTC", "KMD", "LTC"]:
                                            return notary_seasons[0], coin
                                        else:
                                            return notary_seasons[0], server

    return "Unofficial", "Unofficial"


def get_balance(coin, pubkey, addr):
    balance = -1
    if coin in ELECTRUMS:
        balance = lib_electrum.get_full_electrum_balance(pubkey, coin)

    if balance == -1:
        balance = lib_api.get_dexstats_balance(coin, addr)
        
    if balance == -1:
        if coin == "AYA":
            url = 'https://explorer.aryacoin.io/ext/getaddress/'+addr
            r = requests.get(url)
            if 'balance' in r.json():
                balance = r.json()['balance']
            else:
                balance = -1
                logger.warning(">>>>> "+coin+" via explorer.aryacoin.io FAILED | addr: "+addr+" | "+str(r.text))

    return balance


def get_server_active_scoring_dpow_coins_at_time(season, server, timestamp):
    url = get_notarised_tenure_table_url(season, server)
    r = requests.get(url)
    tenure = r.json()["results"]
    server_active_scoring_dpow_coins = []
    count = 0
    for item in tenure:
        if timestamp >= item["official_start_block_time"]:
            if timestamp <= item["official_end_block_time"]:
                coin = item["chain"]
                if coin not in ["BTC", "LTC", "KMD"] and coin not in DPOW_EXCLUDED_COINS[season]:
                    server_active_scoring_dpow_coins.append(coin)
    server_active_scoring_dpow_coins = list(set(server_active_scoring_dpow_coins))
    return server_active_scoring_dpow_coins, len(server_active_scoring_dpow_coins)


def get_coin_server(coin, season):
    if coin in ["KMD", "LTC", "BTC"]:
        return coin
    else:
        dpow_main_coins = SEASONS_INFO[season]["servers"]["Main"]["coins"]
        dpow_3p_coins = SEASONS_INFO[season]["servers"]["Third_Party"]["coins"]

    if coin in dpow_main_coins:
        return "Main"
    elif coin in dpow_3p_coins:
        return "Third_Party"
    else:
        return "Unofficial"

 
def get_season(time_stamp=None):

    if not time_stamp:
        time_stamp = int(time.time())
    time_stamp = int(time_stamp)

    # detect & convert js timestamps
    if round((time_stamp/1000)/time.time()) == 1:
        time_stamp = time_stamp/1000

    for season in SEASONS_INFO:

        if season.find("Testnet") == -1:
            if is_postseason(time_stamp):
                end_time = SEASONS_INFO[season]['post_season_end_time']
            else:
                end_time = SEASONS_INFO[season]['end_time']

        if time_stamp >= SEASONS_INFO[season]['start_time'] and time_stamp <= end_time:
            return season

    return "Unofficial"


def get_name_from_address(address):
    if address in KNOWN_ADDRESSES:
        return KNOWN_ADDRESSES[address]
    return address