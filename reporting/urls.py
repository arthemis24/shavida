# -*- coding: utf-8 -*-

__author__ = 'Kom Sihon'

from django.conf.urls import *
from reporting.views import ContentPublicationReport, get_repo_setup_files, get_repo_files_update, confirm_order, \
    debit_vod_balance, cancel_order

urlpatterns = patterns(
    '',
    url(r'^contentPublication/$', ContentPublicationReport.as_view(), name='content_publication'),
    url(r'^get_repo_setup_files$', get_repo_setup_files, name='get_repo_setup_files'),
    url(r'^get_repo_files_update$', get_repo_files_update, name='get_repo_files_update'),
    url(r'^confirm_order$', confirm_order, name='confirm_order'),
    url(r'^debit_vod_balance$', debit_vod_balance, name='debit_vod_balance'),
    url(r'^cancel_order$', cancel_order, name='cancel_order'),
)
