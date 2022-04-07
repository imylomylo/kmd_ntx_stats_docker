from django.urls import path
from kmd_ntx_api import views_atomicdex
from kmd_ntx_api import api_atomicdex

# AtomicDEX VIEWS
frontend_atomicdex_urls = [

    path('atomicdex/activation_commands/',
         views_atomicdex.activation_commands_view,
         name='activation_commands_view'),

    path('atomicdex/batch_activation_form/',
         views_atomicdex.batch_activation_form_view,
         name='batch_activation_form_view'),

    path('atomicdex/bestorders/',
         views_atomicdex.bestorders_view,
         name='bestorders_view'),

    path('atomicdex/gui_stats/',
          views_atomicdex.gui_stats_view,
          name='gui_stats_view'),

    path('atomicdex/last_200_swaps/',
         views_atomicdex.last_200_swaps_view,
         name='last_200_swaps_view'),

    path('atomicdex/last_200_failed_swaps/',
         views_atomicdex.last_200_failed_swaps_view,
         name='last_200_failed_swaps_view'),
    
    path('atomicdex/makerbot_config_form/',
          views_atomicdex.makerbot_config_form_view,
          name='makerbot_config_form_view'),

    path('atomicdex/orderbook/',
         views_atomicdex.orderbook_view,
         name='orderbook_view'),

    path('atomicdex/seednode_version_stats_hourly/',
         views_atomicdex.seednode_version_stats_hourly_table_view,
         name='seednode_version_stats_hourly_table_view'),

    path('atomicdex/seednode_version_stats_daily/',
         views_atomicdex.seednode_version_stats_daily_table_view,
         name='seednode_version_stats_daily_table_view'),

    path('atomicdex/seednode_version_stats_month/',
         views_atomicdex.seednode_version_stats_month_table_view,
         name='seednode_version_stats_month_table_view'),
]

# AtomicDEX API V2
api_atomicdex_urls = [
    path('api/atomicdex/seednode_version_stats/',
         api_atomicdex.seednode_version_stats_api,
         name='seednode_version_stats_api'),

    path('api/atomicdex/nn_seed_version_scores_table/',
         api_atomicdex.nn_seed_version_scores_table_api,
         name='nn_seed_version_scores_table_api'),

    path('api/atomicdex/seednode_version_stats_hourly/',
         api_atomicdex.seednode_version_stats_hourly_api,
         name='seednode_version_stats_hourly_api'),

    path('api/atomicdex/activation_commands/',
          api_atomicdex.activation_commands_api,
          name='activation_commands_api'),

    path('api/atomicdex/orderbook/',
         api_atomicdex.orderbook_api,
         name='orderbook_api'),

    path('api/atomicdex/bestorders/',
         api_atomicdex.bestorders_api,
         name='bestorders_api'),

    path('api/atomicdex/failed_swap/',
         api_atomicdex.failed_swap_api,
         name='failed_swap_api'),

    path('api/atomicdex/last_200_swaps/',
         api_atomicdex.last_200_swaps_api,
         name='last_200_swaps_api'),

    path('api/atomicdex/last_200_failed_swaps/',
         api_atomicdex.last_200_failed_swaps_api,
         name='last_200_failed_swaps_api'),

    path('api/atomicdex/swaps_gui_stats/',
          api_atomicdex.swaps_gui_stats_api,
          name='swaps_gui_stats_api'),

    path('api/atomicdex/swaps_pubkey_stats/',
          api_atomicdex.swaps_pubkey_stats_api,
          name='swaps_pubkey_stats_api'),
]