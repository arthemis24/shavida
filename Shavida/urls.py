from cms.views import FlatPageView
from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

__author__ = "Kom Sihon"

urlpatterns = patterns(
    '',
    url(r'^', include('movies.urls', namespace='movies')),
    url(r'^me/', include('me.urls', namespace='me')),
    url(r'^reporting/', include('reporting.urls', namespace='reporting')),
    url(r'^page/(?P<slug>[-\w]+)/$', FlatPageView.as_view(), name='flat_page'),
    url(r'^ikwen/', include('ikwen.urls', namespace='ikwen')),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    url(r'^admin/', include(admin.site.urls)),
)
