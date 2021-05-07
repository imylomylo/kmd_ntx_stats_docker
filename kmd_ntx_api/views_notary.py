#!/usr/bin/env python3

import time
from datetime import datetime as dt

from django.shortcuts import render

from kmd_ntx_api.lib_info import *
from kmd_ntx_api.lib_stats import *
from kmd_ntx_api.lib_graph import *

def notary_profile_view(request, notary=None, season=None):
    # Populate sidebar
    if not season:
        season = SEASON
    
    context = {
        "page_title":"Notary Profile Index",
        "season":season,
        "season_clean":season.replace("_"," "),
        "sidebar_links":get_sidebar_links(season),
        "eco_data_link":get_eco_data_link()
    }

    if notary:

        url = f"{THIS_SERVER}/api/table/notary_profile_summary"
        notary_profile_summary_table = requests.get(f"{url}/?season={season}&notary={notary}").json()['results']

        url = f"{THIS_SERVER}/api/table/balances"
        notary_balances = requests.get(f"{url}/?season={season}&notary={notary}").json()['results']

        notarised_count_season_data = notary_profile_summary_table['ntx_season_data'][0]
        notary_balances_list, notary_balances_graph = get_notary_balances_graph(notary, season)
        notarised_data_24hr = get_notarised_data_24hr(season, None, None, notary)
        notarisation_scores = get_notarisation_scores(season)
        main_notarised_24hr = notarised_data_24hr.filter(server='Main').count()
        third_notarised_24hr = notarised_data_24hr.filter(server='Third_Party').count()
        ltc_notarised_24hr = notarised_data_24hr.filter(server='KMD').count()
        region = get_notary_region(notary)

        season_score = 0
        last_ntx_time = 0
        last_btc_ntx_time = 0
        last_ntx_chain = ""
        for item in notary_profile_summary_table['ntx_summary_data']:
            season_score += item["chain_score"]
            if "last_block_time" in item:
                if item["chain"] == "LTC":
                    last_ltc_ntx_time = item["last_block_time"]
                if item["last_block_time"] > last_ntx_time:
                    last_ntx_time = item["last_block_time"]
                    last_ntx_chain = item["chain"]

        context.update({
            "page_title":f"{notary} Notary Profile",
            "notary_name": notary,
            "nn_social": get_nn_social(notary), # Social Media Links
            "season_btc_count": notarised_count_season_data['btc_count'],
            "season_main_count": notarised_count_season_data['antara_count'],
            "season_third_party_count": notarised_count_season_data['third_party_count'],
            "24hr_ltc_count": ltc_notarised_24hr,
            "24hr_main_count": main_notarised_24hr,
            "24hr_third_party_count": third_notarised_24hr,
            "season_score":season_score,
            "last_ltc_ntx_time":get_time_since(last_ltc_ntx_time)[1],
            "last_ntx_time":get_time_since(last_ntx_time)[1],
            "last_ntx_chain":last_ntx_chain,
            "mining_summary": get_nn_mining_summary(notary), #  Mining Summary
            "explorers": get_explorers(request), # For hyperlinking addresses
            "rank": get_region_rank(notarisation_scores[region], notarisation_scores[region][notary]['score']),
            "ntx_summary_data":notary_profile_summary_table['ntx_summary_data'],
            "notary_balances_graph_data": notary_balances_graph, # Balances in graph format
            "notary_balances": notary_balances, # Balances in table format
        })

        return render(request, 'notary_profile.html', context)

    else:
        context.update({
            "nn_social":get_nn_social(),
            "nn_info":get_nn_info()
        })

        return render(request, 'notary_profile_index.html', context)

def vote2021_view(request):
    # Populate sidebar
    season = None
    if "season" in request.GET:
        params = f'?season={request.GET["season"]}'
    else:
        season = SEASON
        logger.info(request.GET)
    logger.info(request.GET)

    context = {
        "season":season,
        "season_clean":season.replace("_"," "),
        "page_title":"Notary VOTE 2021",
        "sidebar_links":get_sidebar_links(season),
        "eco_data_link":get_eco_data_link()
    }


    if "max_locktime" in request.GET:
        params = f'?max_locktime={request.GET["max_locktime"]}'
    elif "max_block" in request.GET:
        params = f'?max_block={request.GET["max_block"]}'
    else:
        params = f'?max_locktime=1619179199'
    url = f"{THIS_SERVER}/api/info/vote2021_stats"
    vote2021_table = requests.get(f"{url}/{params}").json()
    if 'results' in vote2021_table:
        vote2021_table = vote2021_table["results"]

    context.update({
        "params": params,
        "vote2021_table": vote2021_table
    })

    return render(request, 'vote2021.html', context)

def vote2021_detail_view(request):
    # Populate sidebar
    season = None
    if "season" in request.GET:
        params = f'?season={request.GET["season"]}'
    else:
        season = SEASON
    
    context = {
        "season":season,
        "season_clean":season.replace("_"," "),
        "page_title":"Notary VOTE 2021",
        "sidebar_links":get_sidebar_links(season),
        "eco_data_link":get_eco_data_link()
    }

    candidate = None
    if "candidate" in request.GET:
        params = f'?candidate={request.GET["candidate"]}'
    else:
        return vote2021_view(request)
    if "max_locktime" in request.GET:
        params += f'&max_locktime={request.GET["max_locktime"]}'
    elif "max_block" in request.GET:
        params += f'&max_block={request.GET["max_block"]}'
    else:
        params += f'&max_locktime=1619179199'
    url = f"{THIS_SERVER}/api/table/vote2021"
    vote2021_detail_table = requests.get(f"{url}/{params}").json()
    if 'results' in vote2021_detail_table:
        vote2021_detail_table = vote2021_detail_table["results"]

    for item in vote2021_detail_table:
        date_time = dt.fromtimestamp(item["lock_time"])

        item.update({"lock_time_human":date_time.strftime("%m/%d/%Y, %H:%M:%S")})

    candidate = request.GET["candidate"].replace(".", "-")
    context.update({
        "candidate": candidate,
        "params": params,
        "vote2021_detail_table": vote2021_detail_table
    })

    return render(request, 'vote2021_detail.html', context)
