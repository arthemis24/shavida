# -*- coding: utf-8 -*-

from django.conf.urls import *
from cms.views import BaseView, FlatPageView, Contact
from movies.views import stream, TestVideoBytesCounter, Home, MediaList, Checkout, MovieDetail, \
    get_media, get_recommended_for_single_category, Search, SeriesDetail, Bundles
from reporting.views import confirm_order, debit_vod_balance

__author__ = "Kom Sihon"

urlpatterns = patterns(
    '',
    url(r'^$', Home.as_view(), name='home'),
    url(r'^category/(?P<slug>[-\w]+)/$', MediaList.as_view(), name='media_list'),
    url(r'^contact/$', Contact.as_view(), name='contact'),
    url(r'^bundles/$', Bundles.as_view(), name='bundles'),
    url(r'^checkout/$', Checkout.as_view(), name='checkout'),
    url(r'^page/(?P<slug>[-\w]+)/$', FlatPageView.as_view(), name='flat_page'),
    url(r'^movie/(?P<slug>[-\w]+)/$', MovieDetail.as_view(), name='movie_detail'),
    url(r'^getMovies$', get_media, name='get_media'),
    url(r'^get_recommended_for_single_category$', get_recommended_for_single_category, name='get_recommended_for_single_category'),
    url(r'^confirmOrder$', confirm_order, name='confirm_order'),
    url(r'^series/(?P<slug>[-\w]+)/$', SeriesDetail.as_view(), name='series_detail'),
    url(r'^search$', Search.as_view(), name='search'),
    url(r'^stream/(?P<media_type>[-\w]+)/(?P<item_id>[-\w]+)/$', stream, name='stream'),
    url(r'^debit_vod_balance$', debit_vod_balance, name='debit_vod_balance'),
    url(r'^testVideoBytesCounter/$', TestVideoBytesCounter.as_view()),
)