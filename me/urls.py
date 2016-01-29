# -*- coding: utf-8 -*-

from django.conf.urls import *

from cms.views import get_base_context
from ikwen.views import account_setup
from me.views import History, authorize_adult
from me.views import choose_retail_bundle, choose_vod_bundle

urlpatterns = patterns(
    '',
    url(r'^history/$', History.as_view(), name='history'),
    url(r'^choose_retail_bundle$', choose_retail_bundle, name='choose_retail_bundle'),
    url(r'^choose_vod_bundle$', choose_vod_bundle, name='choose_vod_bundle'),
    url(r'^authorize_adult$', authorize_adult, name='authorize_adult'),
    url(r'^accountSetup/$', account_setup,
        {'template_name': 'me/account.html', 'extra_context': get_base_context}, name='account_setup'),
)
