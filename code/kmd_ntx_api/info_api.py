#!/usr/bin/env python3
from kmd_ntx_api.info import get_pages_index, get_mined_between_blocks, \
    get_mined_between_blocktimes, get_base_58_coin_params, get_balances, get_coins, \
    get_coin_prefixes, get_daemon_cli, get_dpow_server_coins_info, get_explorers, \
    get_coin_icons, get_electrums, get_electrums_ssl, get_launch_params, \
    get_coin_social_info, get_ltc_txid_list, get_nn_social_info, get_notary_icons, \
    get_notarised_coin_daily, get_notarised_count_daily, get_notarised_coins, \
    get_notarised_servers, get_notarisation_txid_list, get_notarised_txid, \
    get_notary_ltc_transactions, get_notary_ltc_txid, get_notary_nodes_info
from kmd_ntx_api.const import SINCE_INTERVALS
from kmd_ntx_api.helper import json_resp, get_page_server, get_time_since
from kmd_ntx_api.notary_seasons import get_page_season, get_season, get_seasons_info



def pages_index(request):
    resp = get_pages_index(request)
    filters = ['category', 'sidebar']
    return json_resp(resp, filters)


def mined_between_blocks(request):
    resp = get_mined_between_blocks(request)
    filters = ['min_block', 'max_block']
    return json_resp(resp, filters)


def mined_between_blocktimes(request):
    resp = get_mined_between_blocktimes(request)
    filters = ['min_blocktime', 'max_blocktime']
    return json_resp(resp, filters)


def base_58_coin_params(request):
    resp = get_base_58_coin_params(request)
    filters = ['coin']
    return json_resp(resp, filters)


def balances_info(request):
    resp = get_balances(request)
    filters = ['season', 'server', 'notary', 'coin']
    return json_resp(resp, filters)


def coins_info(request, coin=None):
    resp = get_coins(request, coin)
    filters = ['coin', 'dpow_active', 'mm2_active']
    return json_resp(resp, filters)


def coin_prefixes(request, coin=None):
    resp = get_coin_prefixes(request, coin)
    filters = ['coin']
    return json_resp(resp, filters)


def coin_daemon_cli(request):
    resp = get_daemon_cli(request)
    filters = ['coin']
    return json_resp(resp, filters)


def dpow_server_coins_info(request):
    resp = get_dpow_server_coins_info(request)
    filters = ['season', 'server', 'epoch', 'timestamp']
    return json_resp(resp, filters)


def coin_explorers(request):
    resp = get_explorers(request)
    filters = ['coin']
    return json_resp(resp, filters)


def coin_icons_info(request):
    resp = get_coin_icons(request)
    filters = ['coin']
    return json_resp(resp, filters)


def coin_electrums(request):
    resp = get_electrums(request)
    filters = ['coin']
    return json_resp(resp, filters)


def coin_electrums_ssl(request):
    resp = get_electrums_ssl(request)
    filters = ['coin']
    return json_resp(resp, filters)


def coin_launch_params(request):
    resp = get_launch_params(request)
    filters = ['coin']
    return json_resp(resp, filters)


def coin_social_info(request):
    resp = get_coin_social_info(request)
    filters = ['season', 'coin']
    return json_resp(resp, filters)


def ltc_txid_list(request):
    resp = get_ltc_txid_list(request)
    filters = ['season', 'notary', 'category', 'address']
    return json_resp(resp, filters)


def notary_icons_info(request):
    resp = get_notary_icons(request)
    filters = ['notary', 'season']
    return json_resp(resp, filters)


def nn_social_info(request):
    resp = get_nn_social_info(request)
    filters = ['season', 'notary']
    return json_resp(resp, filters)


def notarised_coin_daily_info(request):
    resp = get_notarised_coin_daily(request)
    filters = ['notarised_date']
    return json_resp(resp, filters)


def notarised_count_daily_info(request):
    resp = get_notarised_count_daily(request)
    filters = ['notarised_date']
    return json_resp(resp, filters)


def notarised_coins(request):
    resp = get_notarised_coins(request)
    filters = ['txid']
    return json_resp(resp, filters)


def notarised_servers(request):
    resp = get_notarised_servers(request)
    filters = ['txid']
    return json_resp(resp, filters)


def notarisation_txid_list(request):
    resp = get_notarisation_txid_list(request)
    filters = ['season', 'server', 'coin', 'notary']
    return json_resp(resp, filters)

    
def notarised_txid(request):
    resp = get_notarised_txid(request)
    print(resp)
    filters = ['txid']
    return json_resp(resp, filters)


def notary_ltc_transactions(request):
    resp = get_notary_ltc_transactions(request)
    filters = ['season', 'category', 'notary', 'address']
    return json_resp(resp, filters)


def notary_ltc_txid(request):
    resp = get_notary_ltc_txid(request)
    filters = ['txid']
    return json_resp(resp, filters)


def notary_nodes_info(request):
    resp = get_notary_nodes_info(request)
    filters = ['year']
    return json_resp(resp, filters)
