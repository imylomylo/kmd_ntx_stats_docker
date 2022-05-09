#!/usr/bin/env python3
import requests
import datetime as dt
from datetime import datetime, timezone
from django.shortcuts import render
from kmd_ntx_api.lib_const import *
import kmd_ntx_api.lib_helper as helper
import kmd_ntx_api.lib_testnet as testnet


def testnet_ntx_scoreboard_view(request):
    context = helper.get_base_context(request)
    year = helper.get_or_none(request, "year", VOTE_YEAR)
    season = f"{year}_Testnet"
 
    testnet_ntx_counts = testnet.get_api_testnet(request)
    num_notaries = len(testnet_ntx_counts)

    combined_total = 0
    combined_total_24hr = 0

    for notary in testnet_ntx_counts:
        combined_total += testnet_ntx_counts[notary]["Total"]
        combined_total_24hr += testnet_ntx_counts[notary]["24hr_Total"]
    average_score = combined_total / num_notaries
    average_score_24hr = combined_total_24hr / num_notaries

    context = helper.get_base_context(request)
    context.update({
        "average_score": average_score,
        "year": year,
        "average_score_24hr": average_score_24hr,
        "testnet_ntx_counts": testnet_ntx_counts
    })
    return render(request, 'views/vote/testnet_scoreboard.html', context)


def notary_vote_view(request):
    context = helper.get_base_context(request)
    year = helper.get_or_none(request, "year", VOTE_YEAR)
    max_block = helper.get_or_none(request, "max_block", VOTE_PERIODS[year]["max_block"])

    url = f"{THIS_SERVER}/api/info/notary_vote_stats"
    params = f'?year={year}&max_block={max_block}'
    notary_vote_table = requests.get(f"{url}/{params}").json()

    if 'results' in notary_vote_table:
        notary_vote_table = notary_vote_table["results"]

    context.update({
        "params": params,
        "year": year,
        "notary_vote_table": notary_vote_table
    })

    return render(request, 'views/vote/notary_vote.html', context)


def notary_vote_detail_view(request):
    context = helper.get_base_context(request)
    year = helper.get_or_none(request, "year", VOTE_YEAR)
    candidate = helper.get_or_none(request, "candidate")
    max_block = helper.get_or_none(request, "max_block", VOTE_PERIODS[year]["max_block"])


    url = f"{THIS_SERVER}/api/table/notary_vote"
    params = f'?year={year}&max_block={max_block}'
    notary_vote_detail_table = requests.get(f"{url}/{params}").json()

    if 'results' in notary_vote_detail_table:
        notary_vote_detail_table = notary_vote_detail_table["results"]

    for item in notary_vote_detail_table:
        date_time = datetime.fromtimestamp(item["block_time"])

        item.update({"block_time_human":date_time.strftime("%m/%d/%Y, %H:%M:%S")})

    candidate = request.GET["candidate"].replace(".", "-")

    context.update({
        "candidate": candidate,
        "params": params,
        "year": year,
        "notary_vote_detail_table": notary_vote_detail_table
    })

    return render(request, 'views/vote/notary_vote_detail.html', context)


def s5_address_confirmation(request):
    # Populate sidebar
    context = helper.get_base_context(request)

    addr_confirmed_in_PR = [
        "alien_AR",
        "alien_EU",
        "alien_NA",
        "alienx_EU",
        "alienx_NA",
        "computergenie_NA",
        "dappvader_SH",
        "drkush_SH",
        "goldenman_AR",
        "kolo_AR",
        "node-9_EU",
        "node-9_NA",
        "nodeone_NA",
        "nutellaLicka_SH",
        "ptyx_NA",
        "phit_SH",
        "sheeba_SH",
        "slyris_EU",
        "strob_SH",
        "strob_NA",
        "strobnidan_SH",
        "tonyl_AR",
        "tonyl_DEV",
        "strobnidan_SH",
        "webworker01_NA",
        "van_EU"
    ]
    pub_confirmed_in_PR = [
        "alien_AR",
        "alien_EU",
        "alien_NA",
        "alienx_EU",
        "alienx_NA",
        "artem_DEV",
        "artempikulin_AR",
        "ca333_EU",
        "chmex_AR",
        "chmex_EU",
        "chmex_SH",
        "cipi_EU",
        "cipi_AR",
        "cipi_NA",
        "cipi2_EU",
        "collider_SH",
        "karasugoi_NA",
        "komodopioneers_EU",
        "madmax_AR",
        "madmax_EU",
        "madmax_NA",
        "marmarachain_EU",
        "majora31_SH",
        "karasugoi_NA",
        "metaphilibert_SH",
        "mrlynch_AR",
        "metaphilibert_SH",
        "pbca26_NA",
        "pbca26_SH",
        "smdmitry_AR",
        "smdmitry_EU",
        "pbca26_SH",
        "mcrypt_AR",
        "mcrypt_SH",
        "yurii_DEV"
    ]
    pub_confirmed_in_DM = [
        "gcharang_DEV",
        "mylo_SH",
        "hyper_NA",
        "tokel_AR",
        "shadowbit_AR",
        "shadowbit_EU",
        "shadowbit_DEV",
        "ocean_AR",
        "alrighttt_DEV",
        "ca333_DEV"
    ]
    addr_confirmed_in_DM = [
        "dragonhound_DEV",
        "dragonhound_NA",
    ]

    kmd_addresses = requests.get(f"{THIS_SERVER}/api/table/addresses/?season=Season_5&coin=KMD").json()["results"]
    ltc_addresses = requests.get(f"{THIS_SERVER}/api/table/addresses/?season=Season_5&coin=LTC&server=Main").json()["results"]
    addresses = kmd_addresses + ltc_addresses

    for item in addresses:
        if item["notary"] in pub_confirmed_in_PR:
            item.update({"confirmed":"Pubkey (PR)"})
        elif item["notary"] in addr_confirmed_in_PR:
            item.update({"confirmed":"Address (PR)"})
        elif item["notary"] in pub_confirmed_in_DM:
            item.update({"confirmed":"Pubkey (DM)"})
        elif item["notary"] in addr_confirmed_in_DM:
            item.update({"confirmed":"Address (DM)"})

    context.update({
        "page_title": "Address Confirmation",
        "addresses": addresses,
    })

    return render(request, 'views/vote/s5_address_confirmation.html', context)