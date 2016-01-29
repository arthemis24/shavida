# -*- coding: utf-8 -*-
from datetime import datetime
from django.conf import settings
from django.core.urlresolvers import reverse

from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from cms.models import SiteConfig, FlatPage
from movies.models import Category


def get_base_context(request):
    context = {
        'config': get_object_or_404(SiteConfig, is_active=True),
        'WEBSITE_NAME': getattr(settings, 'WEBSITE_NAME'),
        'VOD_COUNTER_INTERVAL': getattr(settings, 'VOD_COUNTER_INTERVAL', 5),
        'IS_VOD_OPERATOR': getattr(settings, 'IS_VOD_OPERATOR', False),
        'IS_CONTENT_VENDOR': getattr(settings, 'IS_CONTENT_VENDOR', False), 'year': datetime.now().year,
        'footer_flat_pages': FlatPage.objects.filter(show_in_footer=True)
    }
    categories_qs = Category.objects.filter(visible=True)
    context['smart_categories'] = categories_qs.filter(smart=True)
    context['main_categories'] = categories_qs.filter(smart=False).exclude(appear_in_main=True)
    context['more_categories'] = categories_qs.filter(smart=False).exclude(appear_in_main=False)
    context['all_categories'] = categories_qs
    context['history_url'] = reverse('me:history')
    context['sign_in_url'] = reverse('ikwen:sign_in')
    context['bundles_url'] = reverse('movies:bundles')
    if request.user.is_authenticated():
        last_vod_prepayment = request.user.profile.get_last_vod_prepayment()
        last_vod_prepayment.balance /= 1000.0
        context['last_vod_prepayment'] = last_vod_prepayment
    return context


class BaseView(TemplateView):

    def get_context_data(self, **kwargs):
        return get_base_context(self.request)


class FlatPageView(BaseView):
    template_name = 'flat_page.html'

    def get_context_data(self, **kwargs):
        context = super(FlatPageView, self).get_context_data(**kwargs)
        slug = self.kwargs.get('slug', None)
        context['page'] = get_object_or_404(FlatPage, slug=slug)
        return context


class Contact(BaseView):
    template_name = 'contact.html'

    def get_context_data(self, *args, **kwargs):
        context = super(Contact, self).get_context_data(**kwargs)
        context['page'] = get_object_or_404(FlatPage, slug='contact')
        return context