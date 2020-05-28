import time
import datetime
from django.db.models import Count, Min, Max, Sum
import logging
import random
import requests
from .models import *
from .query_lib import *
from .helper_lib import *
logger = logging.getLogger("mylogger")

url = "https://raw.githubusercontent.com/gcharang/data/master/info/ecosystem.json"
r = requests.get(url)
eco_data = r.json()

 # Need to confirm and fill this in correctly later...
seasons_info = {
    "Season_1": {
            "start_block":1,
            "end_block":1,
            "start_time":1,
            "end_time":1530921600,
            "notaries":[]
        },
    "Season_2": {
            "start_block":1,
            "end_block":1,
            "start_time":1530921600,
            "end_time":1563148799,
            "notaries":[]
        },
    "Season_3": {
            "start_block":1444000,
            "end_block":1921999,
            "start_time":1563148800,
            "end_time":1592146799,
            "notaries":[]
        },
    "Season_4": {
            "start_block":1922000,
            "end_block":2444000,
            "start_time":1592146800,
            "end_time":1751328000,
            "notaries":[]
        }
}

def get_season(time_stamp):
    for season in seasons_info:
        if time_stamp >= seasons_info[season]['start_time'] and time_stamp <= seasons_info[season]['end_time']:
            return season
    return "season_undefined"


def get_regions_info(notary_list):
    notary_list.sort()
    regions_info = {
        'AR':{ 
            "name":"Asia and Russia",
            "nodes":[]
            },
        'EU':{ 
            "name":"Europe",
            "nodes":[]
            },
        'NA':{ 
            "name":"North America",
            "nodes":[]
            },
        'SH':{ 
            "name":"Southern Hemisphere",
            "nodes":[]
            },
        'DEV':{ 
            "name":"Developers",
            "nodes":[]
            }
    }
    for notary in notary_list:
        region = notary.split('_')[-1]
        regions_info[region]['nodes'].append(notary)
    return regions_info

def region_sort(notary_list):
    new_list = []
    for region in ['AR','EU','NA','SH','DEV']:
        for notary in notary_list:
            if notary.endswith(region):
                new_list.append(notary)
    return new_list

def get_eco_data_link():
    item = random.choice(eco_data)
    ad = random.choice(item['ads'])
    while ad['frequency'] == "never":
        item = random.choice(eco_data)
        ad = random.choice(item['ads'])
    link = ad['data']['string1']+" <a href="+ad['data']['link']+"> " \
          +ad['data']['anchorText']+"</a> "+ad['data']['string2']
    return link

def get_premining_ntx_score(btc_ntx, main_ntx, third_party_ntx):
    return btc_ntx*0.5 + main_ntx*0.25 + third_party_ntx*0.25

def get_nn_social(notary_name=None):
    season = get_season(int(time.time()))
    nn_social_info = {}
    if notary_name:
        nn_social_data = nn_social.objects.filter(season=season, notary=notary_name).values()
    else:
        nn_social_data = nn_social.objects.all().values()
    for item in nn_social_data:
        nn_social_info.update(items_row_to_dict(item,'notary'))
    return nn_social_info

def get_nn_ntx_summary(notary):
    season = get_season(int(time.time()))
    now = int(time.time())
    day_ago = now - 24*60*60
    week_ago = now - 24*60*60*7

    today = datetime.date.today()
    delta = datetime.timedelta(days=1)
    week_ago = today-delta*7

    ntx_summary = {
        "today":{
            "btc_ntx":0,
            "main_ntx":0,
            "third_party_ntx":0,
            "most_ntx":str(0)+" ("+str('-')+")"
        },
        "season":{
            "btc_ntx":0,
            "main_ntx":0,
            "third_party_ntx":0,
            "most_ntx":str(0)+" ("+str('-')+")"
        },
        "time_since_last_kmd_ntx":-1,
        "time_since_last_ntx":-1,
        "last_ntx_chain":'-',
        "premining_ntx_score":0,
    }

    # today's ntx stats
    ntx_today = notarised.objects.filter()
    ntx_today = notarised_count_daily.objects.filter(notarised_date=str(today), 
                                             season=season, notary=notary) \
                                            .values()
    if len(ntx_today) > 0:
        chains_ntx_today = ntx_today[0]['chain_ntx_counts']
        today_max_chain = max(chains_ntx_today, key=chains_ntx_today.get) 
        today_max_ntx = chains_ntx_today[today_max_chain]
        ntx_summary['today'].update({
            'most_ntx':today_max_chain+" ("+str(today_max_ntx)+")",
            "btc_ntx":ntx_today[0]['btc_count'],
            "main_ntx":ntx_today[0]['antara_count'],
            "third_party_ntx":ntx_today[0]['third_party_count']
        })

    # season ntx stats
    ntx_season = notarised_count_season.objects \
                                    .filter(season=season, notary=notary) \
                                    .values()
    if len(ntx_season) > 0:
        chains_ntx_season = ntx_season[0]['chain_ntx_counts']
        season_max_chain = max(chains_ntx_season, key=chains_ntx_season.get) 
        season_max_ntx = chains_ntx_season[season_max_chain]
        if season_max_chain == 'KMD':
            season_max_chain = 'BTC'

        ntx_summary['season'].update({
            "btc_ntx":ntx_season[0]['btc_count'],
            "main_ntx":ntx_season[0]['antara_count'],
            "third_party_ntx":ntx_season[0]['third_party_count'],
            "most_ntx":season_max_chain+" ("+str(season_max_ntx)+")"
        })
        ntx_summary.update({
            "premining_ntx_score":get_premining_ntx_score(
                ntx_season[0]['btc_count'],
                ntx_season[0]['antara_count'],
                ntx_season[0]['third_party_count']
            ),
        })

    #last ntx data
    ntx_last = last_notarised.objects \
                             .filter(season=season, notary=notary) \
                             .values()
    last_chain_ntx_times = {}
    for item in ntx_last:
        last_chain_ntx_times.update({item['chain']:item['block_time']})

    if len(last_chain_ntx_times) > 0:
        max_last_ntx_chain = max(last_chain_ntx_times, key=last_chain_ntx_times.get) 
        max_last_ntx_time = last_chain_ntx_times[max_last_ntx_chain]
        time_since_last_ntx = int(time.time()) - int(max_last_ntx_time)
        time_since_last_ntx = day_hr_min_sec(time_since_last_ntx)
        last_chain_ntx_times.update({item['chain']:item['block_time']})
        if max_last_ntx_chain == 'KMD':
            max_last_ntx_chain = 'BTC'
        ntx_summary.update({
            "time_since_last_ntx":time_since_last_ntx,
            "last_ntx_chain":max_last_ntx_chain,
        })

    #last btc ntx data
    btc_ntx_last = last_btc_notarised.objects \
                             .filter(season=season, notary=notary) \
                             .values()

    max_kmd_ntx_time = 0
    for item in btc_ntx_last:
        max_kmd_ntx_time = item['block_time']

    if max_kmd_ntx_time > 0:
        time_since_last_kmd_ntx = int(time.time()) - int(max_kmd_ntx_time)
        print(time.time())
        print(max_kmd_ntx_time)
        print(time_since_last_kmd_ntx)
        time_since_last_kmd_ntx = day_hr_min_sec(time_since_last_kmd_ntx)
        print(time_since_last_kmd_ntx)
        ntx_summary.update({
            "time_since_last_kmd_ntx":time_since_last_kmd_ntx,
        })


    logger.info(ntx_summary)
    return ntx_summary

def get_nn_mining_summary(notary):
    season = get_season(int(time.time()))
    now = int(time.time())
    day_ago = now - 24*60*60
    week_ago = now - 24*60*60*7

    mining_summary = {
        "mined_last_24hrs": 0,
        "season_value_mined": 0,
        "season_blocks_mined": 0,
        "season_largest_block": 0,
        "largest_block_height": 0,
        "last_mined_datetime": -1,
        "time_since_mined": -1,
    }
    notary_mined = mined.objects.filter(season=season, name=notary)

    mined_last_24hrs = notary_mined.filter(block_time__gte=str(day_ago), block_time__lte=str(now)) \
                      .values('name').annotate(mined_24hrs=Sum('value'))

    if len(mined_last_24hrs) > 0:
        mining_summary.update({
            "mined_last_24hrs": float(mined_last_24hrs[0]['mined_24hrs'])
        })



    mined_this_season = notary_mined.filter(block_time__gte=seasons_info[season]['start_time'],
                                          block_time__lte=str(now)) \
                                         .values('name').annotate(season_value_mined=Sum('value'),\
                                                            season_blocks_mined=Count('value'),
                                                            season_largest_block=Max('value'),
                                                            last_mined_datetime=Max('block_datetime'),
                                                            last_mined_block=Max('block_height'),
                                                            last_mined_time=Max('block_time'))
    if len(mined_last_24hrs) > 0:
        time_since_mined = int(time.time()) - int(mined_this_season[0]['last_mined_time'])
        time_since_mined = day_hr_min_sec(time_since_mined)
        mining_summary.update({
            "season_value_mined": float(mined_this_season[0]['season_value_mined']),
            "season_blocks_mined": int(mined_this_season[0]['season_blocks_mined']),
            "season_largest_block": float(mined_this_season[0]['season_largest_block']),
            "last_mined_datetime": mined_this_season[0]['last_mined_datetime'],
            "time_since_mined": time_since_mined,
            "largest_block_height": int(mined_this_season[0]['last_mined_block']),
        })
    logger.info(mining_summary)
    return mining_summary

def get_nn_health():
    coins_data = coins.objects.filter(dpow_active=1).values('chain')
    chains_list = []
    for item in coins_data:
        # ignore BTC, OP RETURN lists ntx to BTC as "KMD"
        if item['chain'] not in chains_list and item['chain'] != 'BTC':
            chains_list.append(item['chain'])

    sync_matches = []
    sync_mismatches = []
    sync_no_exp = []
    sync_no_sync = []
    sync = chain_sync.objects.all().values()
    for item in sync:
        if item['sync_hash'] == item['explorer_hash']:
            sync_matches.append(item['chain'])
        else:
            if item['explorer_hash'] != 'no exp data' and item['sync_hash'] != 'no sync data':
                sync_mismatches.append(item['chain'])
            if item['sync_hash'] == 'no sync data':
                sync_no_sync.append(item['chain'])
            if item['explorer_hash'] == 'no exp data':
                sync_no_exp.append(item['chain'])    
    sync_count = len(sync_matches)
    no_sync_count = len(sync_mismatches)
    sync_pct = round(sync_count/(len(sync))*100,2)

    sync_tooltip = "<h4 class='kmd_teal'>"+str(sync_count)+"/"+str(len(sync))+" ("+str(sync_pct)+"%) recent sync hashes matching</h4>\n"
    if len(sync_mismatches) > 0:
        sync_tooltip += "<h5 class='kmd_secondary_red'>"+str(sync_mismatches)+" have mismatched hashes </h5>\n"
    if len(sync_no_sync) > 0:
        sync_tooltip += "<h5 class='kmd_secondary_red'>"+str(sync_no_sync)+" are not syncing </h5>\n"
    if len(sync_no_exp) > 0:
        sync_tooltip += "<h5 class='kmd_secondary_red'>"+str(sync_no_exp)+" have no explorer </h5>\n"

    season = get_season(int(time.time()))
    notary_list = get_notary_list(season)

    timenow = int(time.time())
    day_ago = timenow-60*60*24

    filter_kwargs = {
        'block_time__gte':day_ago,
        'block_time__lte':timenow
    }

    ntx_data = notarised.objects.filter(**filter_kwargs)
    ntx_chain_24hr = ntx_data.values('chain') \
                     .annotate(max_ntx_time=Max('block_time'))

    ntx_chains = []
    for item in ntx_chain_24hr:
        ntx_chains.append(item['chain'])
    ntx_chains = list(set(ntx_chains))

    ntx_node_24hr = ntx_data.values('notaries')
    ntx_nodes = []
    for item in ntx_node_24hr:
        ntx_nodes += item['notaries']
    ntx_nodes = list(set(ntx_nodes))

    mining_data = mined.objects.filter(**filter_kwargs) \
                 .values('name') \
                 .annotate(num_mined=Count('name'))
    mining_nodes = []
    for item in mining_data:
        if item['name'] in notary_list:
            mining_nodes.append(item['name'])

    season = get_season(int(time.time()))
    filter_kwargs = {'season':season}
    balances_dict = get_balances_dict(filter_kwargs) 

    # some chains do not have a working electrum, so balances ignored
    ignore_chains = ['K64', 'PGT', 'GIN']
    low_balances = get_low_balances(notary_list, balances_dict, ignore_chains)
    low_balances_dict = low_balances[0]
    low_balance_count = low_balances[1]
    sufficient_balance_count = low_balances[2]
    low_balances_tooltip = get_low_balance_tooltip(low_balances, ignore_chains)
    low_balances_pct = round(sufficient_balance_count/(low_balance_count+sufficient_balance_count)*100,2)

    non_mining_nodes = list(set(notary_list)- set(mining_nodes))
    non_ntx_nodes = list(set(notary_list).symmetric_difference(set(ntx_nodes)))
    non_ntx_chains = list(set(chains_list).symmetric_difference(set(ntx_chains)))
    mining_nodes_pct = round(len(mining_nodes)/len(notary_list)*100,2)
    ntx_nodes_pct = round(len(ntx_nodes)/len(notary_list)*100,2)
    ntx_chains_pct = round(len(ntx_chains)/len(chains_list)*100,2)


    mining_tooltip = "<h4 class='kmd_teal'>"+str(len(mining_nodes))+"/"+str(len(non_mining_nodes)+len(mining_nodes))+" ("+str(mining_nodes_pct)+"%) mined 1+ block in last 24hrs</h4>\n"
    mining_tooltip += "<h5 class='kmd_secondary_red'>"+str(non_mining_nodes)+" are not mining! </h5>\n"

    ntx_nodes_tooltip = "<h4 class='kmd_teal'>"+str(len(ntx_nodes))+"/"+str(len(non_ntx_nodes)+len(ntx_nodes))+" ("+str(ntx_nodes_pct)+"%) notarised 1+ times in last 24hrs</h4>\n"
    ntx_nodes_tooltip += "<h5 class='kmd_secondary_red'>"+str(non_ntx_nodes)+" are not notarising! </h5>\n"

    ntx_chains_tooltip = "<h4 class='kmd_teal'>"+str(len(ntx_chains))+"/"+str(len(non_ntx_chains)+len(ntx_chains))+" ("+str(ntx_chains_pct)+"%) notarised 1+ times in last 24hrs</h4>\n"
    ntx_chains_tooltip += "<h5 class='kmd_secondary_red'>"+str(non_ntx_chains)+" are not notarising! </h5>\n"

    regions_info = get_regions_info(notary_list)
    sync_no_exp = []
    sync_no_sync = []
    nn_health = {
        "sync_pct":sync_pct,
        "regions_info":regions_info,
        "sync_tooltip":sync_tooltip,
        "low_balances_dict":low_balances_dict,
        "low_balances_tooltip":low_balances_tooltip,
        "low_balance_count":low_balance_count,
        "sufficient_balance_count":sufficient_balance_count,
        "balance_pct":low_balances_pct,
        "non_mining_nodes":non_mining_nodes,
        "mining_nodes":mining_nodes,
        "mining_tooltip":mining_tooltip,
        "non_mining_nodes":non_mining_nodes,
        "mining_nodes_pct":mining_nodes_pct,
        "ntx_nodes":ntx_nodes,
        "non_ntx_nodes":non_ntx_nodes,
        "ntx_nodes_pct":ntx_nodes_pct,
        "ntx_chains_tooltip":ntx_chains_tooltip,
        "chains_list":chains_list,
        "ntx_chains":ntx_chains,
        "non_ntx_chains":non_ntx_chains,
        "ntx_chains_pct":ntx_chains_pct,
        "ntx_nodes_tooltip":ntx_nodes_tooltip
    }
    return nn_health

def get_coin_ntx_summary(coin):
    season = get_season(int(time.time()))
    now = int(time.time())
    day_ago = now - 24*60*60
    week_ago = now - 24*60*60*7

    today = datetime.date.today()
    delta = datetime.timedelta(days=1)
    week_ago = today-delta*7

    ntx_summary = {
        "today":{
            "btc_ntx":0,
            "main_ntx":0,
            "third_party_ntx":0,
            "most_ntx":str(0)+" ("+str('-')+")"
        },
        "season":{
            "btc_ntx":0,
            "main_ntx":0,
            "third_party_ntx":0,
            "most_ntx":str(0)+" ("+str('-')+")"
        },
        "time_since_last_kmd_ntx":-1,
        "time_since_last_ntx":-1,
        "last_ntx_chain":'-',
        "premining_ntx_score":0,
    }
    '''
    # today's ntx stats
    ntx_today = notarised.objects.filter()
    ntx_today = notarised_chain_daily.objects.filter(notarised_date=str(today), 
                                             season=season, chain=coin) \
                                            .values()
    if len(ntx_today) > 0:
        chains_ntx_today = ntx_today[0]['chain_ntx_counts']
        today_max_chain = max(chains_ntx_today, key=chains_ntx_today.get) 
        today_max_ntx = chains_ntx_today[today_max_chain]
        ntx_summary['today'].update({
            'most_ntx':today_max_chain+" ("+str(today_max_ntx)+")",
            "btc_ntx":ntx_today[0]['btc_count'],
            "main_ntx":ntx_today[0]['antara_count'],
            "third_party_ntx":ntx_today[0]['third_party_count']
        })

    # season ntx stats
    ntx_season = notarised_chain_season.objects \
                                    .filter(season=season, chain=coin) \
                                    .values()
    if len(ntx_season) > 0:
        chains_ntx_season = ntx_season[0]['chain_ntx_counts']
        season_max_chain = max(chains_ntx_season, key=chains_ntx_season.get) 
        season_max_ntx = chains_ntx_season[season_max_chain]
        if season_max_chain == 'KMD':
            season_max_chain = 'BTC'

        ntx_summary['season'].update({
            "btc_ntx":ntx_season[0]['btc_count'],
            "main_ntx":ntx_season[0]['antara_count'],
            "third_party_ntx":ntx_season[0]['third_party_count'],
            "most_ntx":season_max_chain+" ("+str(season_max_ntx)+")"
        })
        ntx_summary.update({
            "premining_ntx_score":get_premining_ntx_score(
                ntx_season[0]['btc_count'],
                ntx_season[0]['antara_count'],
                ntx_season[0]['third_party_count']
            ),
        })cou

    #last ntx data
    ntx_last = last_notarised.objects \
                             .filter(season=season, chain=coin) \
                             .values()
    last_chain_ntx_times = {}
    for item in ntx_last:
        last_chain_ntx_times.update({item['chain']:item['block_time']})

    if len(last_chain_ntx_times) > 0:
        max_last_ntx_chain = max(last_chain_ntx_times, key=last_chain_ntx_times.get) 
        max_last_ntx_time = last_chain_ntx_times[max_last_ntx_chain]
        time_since_last_ntx = int(time.time()) - int(max_last_ntx_time)
        time_since_last_ntx = day_hr_min_sec(time_since_last_ntx)
        last_chain_ntx_times.update({item['chain']:item['block_time']})
        if max_last_ntx_chain == 'KMD':
            max_last_ntx_chain = 'BTC'
        ntx_summary.update({
            "time_since_last_ntx":time_since_last_ntx,
            "last_ntx_chain":max_last_ntx_chain,
        })

    #last btc ntx data
    btc_ntx_last = last_btc_notarised.objects \
                             .filter(season=season) \
                             .values()

    max_kmd_ntx_time = 0
    for item in btc_ntx_last:
        max_kmd_ntx_time = item['block_time']

    if max_kmd_ntx_time > 0:
        time_since_last_kmd_ntx = int(time.time()) - int(max_kmd_ntx_time)
        print(time.time())
        print(max_kmd_ntx_time)
        print(time_since_last_kmd_ntx)
        time_since_last_kmd_ntx = day_hr_min_sec(time_since_last_kmd_ntx)
        print(time_since_last_kmd_ntx)
        ntx_summary.update({
            "time_since_last_kmd_ntx":time_since_last_kmd_ntx,
        })


    logger.info(ntx_summary)'''
    return ntx_summary

def get_balances_dict(filter_kwargs):
    balances_dict = {}
    balances_data = balances.objects.filter(**filter_kwargs).order_by('notary', 'chain').values('notary', 'chain', 'balance')
    for item in balances_data:
        if item['notary'] not in balances_dict:
            balances_dict.update({item['notary']:{}})
        if item['chain'] not in balances_dict[item['notary']]:
            balances_dict[item['notary']].update({item['chain']:item['balance']})
        else:
            bal = balances_dict[item['notary']][item['chain']] + item['balance']
            balances_dict[item['notary']].update({item['chain']:bal})
    return balances_dict  

def get_low_balances(notary_list, balances_dict, ignore_chains):
    low_balances_dict = {}
    sufficient_balance_count = 0
    low_balance_count = 0
    for notary in notary_list:
        if notary in balances_dict:
            for chain in balances_dict[notary]:
                if chain not in ignore_chains:
                    bal = balances_dict[notary][chain]
                    if bal < 0.03:
                        if notary not in low_balances_dict:
                            low_balances_dict.update({notary:{}})
                        if chain not in low_balances_dict[notary]:
                                low_balances_dict[notary].update({chain:str(round(bal.normalize(),4))})
                        low_balance_count += 1
                    else:
                        sufficient_balance_count += 1
    return low_balances_dict, low_balance_count, sufficient_balance_count

def get_low_balance_tooltip(low_balances, ignore_chains):
    low_balances_dict = low_balances[0]
    low_balance_count = low_balances[1]
    sufficient_balance_count = low_balances[2]
    low_balances_pct = round(sufficient_balance_count/(low_balance_count+sufficient_balance_count)*100,2)
    low_balances_tooltip = "<h4 class='kmd_teal'>"+str(sufficient_balance_count)+"/"+str(low_balance_count+sufficient_balance_count)+" ("+str(low_balances_pct)+"%)</h4>\n"
    low_balances_tooltip += "<h6 class='kmd_ui_light1'>where balances < 0.03 </h6>\n"
    low_balances_tooltip += "<h6 class='kmd_ui_light1'>"+str(ignore_chains)+" ignored (no electrum) </h6>\n"
    # open container
    low_balances_tooltip += "<div class='container m-auto' style='width:100%;'>\n"
    i = 1
    notaries = list(low_balances_dict.keys())
    notaries.sort()
    notaries = region_sort(notaries)
    for notary in notaries:
        if i == 1:
            # open row
            low_balances_tooltip += "<div class='row m-auto py-1' style='width:100%;'>\n"
        # open col
        low_balances_tooltip += "<div class='col'><b class='kmd_teal'>"+notary.upper()+"</b><br />"
        if len(low_balances_dict[notary]) > 3:
            low_balances_tooltip += "<b class='kmd_secondary_red'>>3 CHAINS<br /> LOW BALANCE!!!<br /></b>"
        else:
            for chain in low_balances_dict[notary]:
                bal = low_balances_dict[notary][chain]
                low_balances_tooltip += "<b>"+chain+": </b>"+bal+"<br />"
        low_balances_tooltip += "</div>\n"
        # close col
        if i == 5 or notary == notaries[-1]:
            i = 0
            # close row
            low_balances_tooltip += "</div>\n"
        i += 1
    # close container
    low_balances_tooltip += "</div>"
    return low_balances_tooltip

def get_server_chains(coins_data):
    server_chains = {
        "Main":[],
        "Third Party":[]
    }
    for item in coins_data:
        server = item['dpow']['server']
        chain = item['chain']
        if server.lower() == 'dpow-mainnet':
            server_chains['main'].append(chain)
        elif server.lower() == 'dpow-3p':
            server_chains['third_party'].append(chain)
        else:
            logger.warning("Chain not in 3P or main?")
    return server_chains

def get_sidebar_links():
    coins_data = coins.objects.filter(dpow_active=1).values('chain', 'dpow')
    season = get_season(int(time.time()))
    notary_list = get_notary_list(season)
    region_notaries = get_regions_info(notary_list)
    server_chains = get_server_chains(coins_data)
    sidebar_links = {
        "chains_menu":server_chains,
        "notaries_menu":region_notaries,
    }
    return sidebar_links
