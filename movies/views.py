# -*- coding: utf-8 -*-
import requests
from bson.objectid import ObjectId
from django.core.cache import cache

import json
from random import shuffle
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.utils.module_loading import import_by_path
from django.utils.translation import gettext as _

from cms.views import BaseView
from movies.models import *
from cms.models import *
from movies.utils import get_all_recommended, as_matrix, EXCLUDE_LIST_KEYS_KEY, get_recommended_for_category, \
    get_movies_series_share
from sales.models import RetailBundle, VODBundle, VODPrepayment


class CustomerView(BaseView):

    def get_context_data(self, **kwargs):
        context = super(CustomerView, self).get_context_data(**kwargs)
        member = self.request.user
        if member.is_authenticated():
            last_prepayment = member.profile.get_last_retail_prepayment()
            context['last_prepayment'] = last_prepayment
            available_quota = 0
            if last_prepayment:
                if last_prepayment.days_left > 0:
                    available_quota = last_prepayment.balance
            unit = getattr(settings, 'SALES_UNIT', SalesConfig.BROADCASTING_TIME)
            if unit == SalesConfig.BROADCASTING_TIME:
                display_available_quota = "%.2f GB" % (available_quota / 1000.0)
            else:
                display_available_quota = "%dh" % available_quota
            context['SALES_UNIT'] = unit
            context['SALES_UNIT_STR'] = _("GigaBytes") if unit == SalesConfig.DATA_VOLUME else _("Brodcasting hours")
            context['available_quota'] = available_quota
            context['display_available_quota'] = display_available_quota
        return context


class Home(CustomerView):
    template_name = 'movies/home.html'

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        member = self.request.user
        recommended_items = []
        if member.is_authenticated():
            for item in get_all_recommended(member, 12):
                if isinstance(item, Movie):
                    item.type = 'movie'
                else:
                    item.type = 'series'
                    size = 0
                    episodes = SeriesEpisode.objects.filter(series=item)
                    for episode in episodes:
                        size += episode.size
                    item.size = size
                recommended_items.append(item)
            if len(recommended_items) < Movie.MIN_RECOMMENDED:
                additional = Movie.MIN_RECOMMENDED - len(recommended_items)
                additional_items = Movie.objects.all().order_by('-release')[:additional]
                recommended_items.append(additional_items)
        context['items'] = recommended_items
        context['recommended_items'] = as_matrix(recommended_items, 4)
        recent_releases = list(Movie.objects.all().order_by('-release', '-id')[:Movie.MAX_RECENT])
        shuffle(recent_releases)
        sample_media = recent_releases[0]
        context['fb_share_item'] = sample_media
        return context

    def render_to_response(self, context, **response_kwargs):
        if is_touch_device(self.request):
            self.template_name = 'movies/touch/home.html'
        return super(Home, self).render_to_response(context, **response_kwargs)


class MediaList(CustomerView):
    template_name = 'movies/media_list.html'

    def get_context_data(self, **kwargs):
        context = super(MediaList, self).get_context_data(**kwargs)
        slug = kwargs['slug']
        category = Category.objects.get(slug=slug)
        context['current_category'] = category
        context['category_id'] = category.id
        context['category_top'] = Category.objects.get(slug='top')
        return context

    def get(self, request, *args, **kwargs):
        slug = kwargs['slug']
        category = get_object_or_404(Category, slug=slug)
        if category.is_adult and not self.request.user.is_authenticated():
            next_url = reverse("ikwen:sign_in") + '?next_url=' + reverse('movies:media_list', args=(category.slug, ))
            return HttpResponseRedirect(next_url)
        context = self.get_context_data(**kwargs)
        if is_touch_device(self.request):
            self.template_name = 'movies/touch/movie_by_category.html'
        return render(request, self.template_name, context)

    def render_to_response(self, context, **response_kwargs):
        if is_touch_device(self.request):
            self.template_name = 'movies/touch/movie_by_category.html'
        return super(MediaList, self).render_to_response(context, **response_kwargs)


class Bundles(CustomerView):
    template_name = 'movies/bundles.html'

    def get_context_data(self, **kwargs):
        context = super(Bundles, self).get_context_data(**kwargs)
        retail_bundles = RetailBundle.objects.all().order_by('quantity')
        vod_bundles = VODBundle.objects.all().order_by('volume')
        context['retail_bundles'] = retail_bundles
        for bundle in vod_bundles:
            bundle.volume /= 1000
        context['vod_bundles'] = vod_bundles
        return context

    def render_to_response(self, context, **response_kwargs):
        if is_touch_device(self.request):
            self.template_name = 'movies/touch/bundles.html'
        return super(Bundles, self).render_to_response(context, **response_kwargs)


class MovieDetail(CustomerView):
    MAX_SUGGESTIONS = 8
    template_name = 'movies/movie_detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super(MovieDetail, self).get_context_data(**kwargs)
        slug = self.kwargs.get('slug', None)
        movie = get_object_or_404(Movie, slug=slug)
        context['media'] = movie
        groups = ' '.join([val.strip() for val in movie.groups.split(' ') if val != ''])
        suggestions = []
        if groups:
            suggestions = [movie for movie in
                           Movie.objects.raw_query(
                               {'$text': {'$search': groups}, 'visible': True}
                           ).exclude(pk=movie.id).order_by("-id")]
        if len(suggestions) < MovieDetail.MAX_SUGGESTIONS:
            limit = MovieDetail.MAX_SUGGESTIONS - len(suggestions)
            categories_ids = [ObjectId(category.id) for category in movie.categories]
            exclude_ids = [item.id for item in suggestions]
            exclude_ids.append(movie.id)
            categories_suggestions = [movie for movie in
                                      Movie.objects.raw_query(
                                          {'categories': {'$elemMatch': {'id': {'$in': categories_ids}}}, 'visible': True}
                                      ).exclude(pk__in=exclude_ids).order_by("-id")[:limit]]
            suggestions.extend(categories_suggestions)
        context['suggestions'] = [movie.to_dict() for movie in suggestions]
        return context

    def render_to_response(self, context, **response_kwargs):
        if is_touch_device(self.request):
            self.template_name = 'movies/touch/movie_detail.html'
        return super(MovieDetail, self).render_to_response(context, **response_kwargs)


class SeriesDetail(CustomerView):
    MAX_SUGGESTIONS = 5
    template_name = 'movies/series_detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super(SeriesDetail, self).get_context_data(**kwargs)
        slug = self.kwargs.get('slug')
        current_series = get_object_or_404(Series, slug=slug)
        context['episodes'] = [ep for ep in SeriesEpisode.objects.filter(series=current_series).order_by('id')]
        context['media'] = current_series
        groups = ' '.join([val.strip() for val in current_series.groups.split(' ') if val != ''])
        suggestions = []
        if groups:
            suggestions = [series for series in
                           Series.objects.raw_query(
                               {'$text': {'$search': groups}, 'visible': True}
                           ).exclude(pk=current_series.id).order_by("-id")]
            print suggestions
        if len(suggestions) < SeriesDetail.MAX_SUGGESTIONS:
            limit = SeriesDetail.MAX_SUGGESTIONS - len(suggestions)
            categories_ids = [ObjectId(category.id) for category in current_series.categories]
            exclude_ids = [item.id for item in suggestions]
            exclude_ids.append(current_series.id)
            categories_suggestions = [series for series in
                                      Series.objects.raw_query(
                                          {'categories': {'$elemMatch': {'id': {'$in': categories_ids}}}, 'visible': True}
                                      ).exclude(pk__in=exclude_ids).order_by("-id")[:limit]]
            suggestions.extend(categories_suggestions)
        context['suggestions'] = [series.to_dict() for series in suggestions]
        return context

    def render_to_response(self, context, **response_kwargs):
        if is_touch_device(self.request):
            self.template_name = 'movies/touch/series_detail.html'
        return super(SeriesDetail, self).render_to_response(context, **response_kwargs)


class Search(CustomerView):
    template_name = 'movies/search.html'

    def get_context_data(self, **kwargs):
        context = super(Search, self).get_context_data(**kwargs)
        context['page_title'] = ''
        radix = self.request.GET.get('q')
        items = [item.to_dict() for item in self.grab_items_by_radix(radix)]
        context['items'] = items
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('format') == 'json':
            terms = self.request.GET.get('q')
            response = [item.to_dict() for item in self.grab_items_by_radix(terms, use_limit=True)]
            return HttpResponse(
                json.dumps(response),
                'content-type: text/json',
                **response_kwargs
            )
        else:
            if is_touch_device(self.request):
                self.template_name = 'movies/touch/search.html'
            return super(Search, self).render_to_response(context, **response_kwargs)

    def grab_items_by_radix(self, terms, use_limit=False):
        total = 10 if use_limit else 10000
        if use_limit:
            limit_movies, limit_series = get_movies_series_share(total)
        else:
            limit_movies, limit_series = 10000, 10000
        items = []
        if terms and len(terms) >= 2:
            stripped_terms = ' '.join([term.strip()[:4] for term in terms.split(' ') if term])
            if limit_movies > 0:
                movies = [movie for movie in Movie.objects.raw_query(
                    {'$text': {'$search': stripped_terms}, 'visible': True}
                )[:limit_movies]]
                items.extend(movies)
            if limit_series:
                series = [series for series in Series.objects.raw_query(
                    {'$text': {'$search': stripped_terms}, 'visible': True}
                )[:limit_series]]
                items.extend(series)
        if getattr(settings, 'DEBUG'):
            show_adult = self.request.user.is_authenticated() and self.request.user.profile.get_can_access_adult_content()
        else:
            show_adult = self.request.user.is_authenticated() and self.request.user.can_access_adult_content
        for item in items:
            if type(item).__name__ == "Movie" and item.is_adult:
                if not show_adult:
                    items.remove(item)
        return items


def get_media(request, *args, **kwargs):
    """
    :param request:
    :return: list of media (movies and/or series)
    """
    category_id = request.GET.get('category_id') if request.GET.get('category_id') else None
    start_movies = request.GET.get('start_movies') if request.GET.get('start_movies') else ''
    start_series = request.GET.get('start_series') if request.GET.get('start_series') else ''
    length = int(request.GET.get('length')) if request.GET.get('length') else None

    category = Category.objects.get(pk=category_id)
    if not length:
        length = category.previews_length
    response = []
    if category_id and length and (start_movies != '' or start_series != ''):
        start_movies = int(start_movies)
        start_series = int(start_series)
        cache_key = '%s-%d-%d-%d' % (category_id, start_movies, start_series, length)
        media = cache.get(cache_key)
        if not media:
            movies_length, series_length = get_movies_series_share(length)
            limit_movies = start_movies + movies_length
            limit_series = start_series + series_length
            media = list(Movie.objects.raw_query({'categories': {'$elemMatch': {'id': ObjectId(category.id)}}, 'visible': True}).order_by('-id')[start_movies:limit_movies])
            series = list(Series.objects.raw_query({'categories': {'$elemMatch': {'id': ObjectId(category.id)}}, 'visible': True}).order_by('-id')[start_series:limit_series])
            media.extend(series)
            cache.set(cache_key, media, 8 * 3600)
        if request.GET.get('shuffle'):
            shuffle(media)
        response = [item.to_dict() for item in media]
    return HttpResponse(
        json.dumps(response),
        'content-type: text/json'
    )


@login_required
def stream(request, media_type, item_id, *args, **kwargs):
    referrer = request.META.get('HTTP_REFERER')
    response = {"success": True}
    if not referrer:
        return HttpResponseForbidden("You don't have permission to access this resource.")
    try:
        member = request.user
        latest_vod_prepayment = member.profile.get_last_vod_prepayment(VODPrepayment.CONFIRMED)
        if media_type == 'movie':
            media = Movie.objects.get(pk=item_id)
        elif media_type == 'series':
            media = SeriesEpisode.objects.get(pk=item_id)
        else:
            media = Movie.objects.get(pk=item_id).trailer
        media.clicks += 1
        media.save()

        if media.filename[-4:] != '.mp4':
            path = getattr(settings, 'NOT_MP4_HANDLER', None)
            if path:
                url_maker = import_by_path(path)
                resp = url_maker(request, media, *args, **kwargs)
                if resp:
                    return resp

        if media_type != 'trailer':
            if not latest_vod_prepayment:
                response = {"error": _("Sorry, you don't have any valid bundle. Please buy one.")}
                return HttpResponse(json.dumps(response), 'content-type: text/json')
            elif latest_vod_prepayment.balance <= 0:
                response = {"error": _("Sorry, your VOD bundle is sold out. Please buy a new one.")}
                return HttpResponse(json.dumps(response), 'content-type: text/json')
            if media.is_adult:
                if not (latest_vod_prepayment.adult_authorized and member.adult_authorized):
                    vod_bundles = list(VODBundle.objects.filter(adult_authorized=True).order_by('cost'))
                    vod_bundle = vod_bundles[0] if len(vod_bundles) > 0 else None
                    currency = getattr(settings, 'CURRENCY', 'XAF')
                    if vod_bundle:
                        response = {"error": _("Sorry, only bundles as from %s %d give you access to this content" % (currency, vod_bundle.cost))}
                        return HttpResponse(json.dumps(response), 'content-type: text/json')
                    else:
                        response = {"error": _("Sorry, you can't access this content. Please contact your provider.")}
                        return HttpResponse(json.dumps(response), 'content-type: text/json')
        config = get_object_or_404(SiteConfig, is_active=True)
        item_url = ''
        found = False
        for folder in config.vod_data_source.split(','):
            folder = folder.strip()
            path = getattr(settings, 'MAKE_MEDIA_URL', None)
            if path:
                url_maker = import_by_path(path)
                item_url = url_maker(request, folder, media, *args, **kwargs)
            else:
                item_url = folder + media.filename
            if requests.head(item_url).status_code == 200:
                found = True
                break
        is_check = request.GET.get('is_check')
        if is_check:
            if not found:
                response = {"error": _("Resource temporarily unavailable. Please try again later.")}
            return HttpResponse(json.dumps(response), 'content-type: text/json')
        return HttpResponseRedirect(item_url)
    except:
        response = {'error': _("An unknown server error occured. Please try again later.")}
        return HttpResponse(json.dumps(response), 'content-type: text/json')


class TestVideoBytesCounter(BaseView):
    template_name = "movies/test_video_bytes_counter.html"


class Checkout(CustomerView):
    template_name = "movies/checkout.html"

    def render_to_response(self, context, **response_kwargs):
        if is_touch_device(self.request):
            self.template_name = 'movies/touch/checkout.html'
        return super(Checkout, self).render_to_response(context, **response_kwargs)


def is_touch_device(request):
    ANDROID = 'Android'
    BLACKBERRY = 'Blackberry'
    IPhone = 'iPhone'
    IPAD = 'iPad'
    is_touch = False

    user_agent = request.META['HTTP_USER_AGENT']
    if user_agent.find(ANDROID) != -1 or user_agent.find(BLACKBERRY) != -1 or user_agent.find(IPhone) != -1 or user_agent.find(IPAD) != -1:
        is_touch = True
    return False


def get_recommended_for_single_category(request, *args, **kwargs):
    category_id = request.GET.get('category_id')
    response = []
    if category_id:
        category = Category.objects.get(pk=category_id)
        member = request.user
        cache_key = member.email + ':recommended-' + category_id
        recommended = cache.get(cache_key)
        if not recommended:
            exclude_list_keys = cache.get(member.email + ':' + EXCLUDE_LIST_KEYS_KEY)
            exclude_list = []
            if not exclude_list_keys:
                exclude_list_keys = set()
            else:
                for key in exclude_list_keys:
                    items = cache.get(key)
                    if items:
                        exclude_list.extend(items)
            recommended = get_recommended_for_category(category, category.previews_length, exclude_list)
            exclude_list_keys.add(cache_key)
            cache.set(cache_key, recommended)
            cache.set(member.email + ':' + EXCLUDE_LIST_KEYS_KEY, exclude_list_keys)
        response = [item.to_dict() for item in recommended]
    return HttpResponse(
        json.dumps(response),
        'content-type: text/json'
    )


# MAKE_MEDIA_URL
def make_media_url(request, media, *args, **kwargs):
    # Put in the transcode queue here
    response = {"error": _("Sorry, file under process, please try again very soon.")}
    return HttpResponse(json.dumps(response), 'content-type: text/json')


# NOT_MP4_HANDLER
def queue_for_transcode(request, media, *args, **kwargs):
    # Put in the transcode queue here
    response = {"error": _("Sorry, file under process, please try again very soon.")}
    return HttpResponse(json.dumps(response), 'content-type: text/json')
