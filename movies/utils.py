# -*- coding: utf-8 -*-
from bson import ObjectId
from django.core.cache import cache
from math import ceil
from django.shortcuts import get_object_or_404
from movies.models import Category, Movie, Series, SeriesEpisode
from reporting.models import StreamLogEntry
from reporting.utils import get_ordered, get_watched

__author__ = 'komsihon'

# Cache key for the exclude_list. Exclude_list contains a pipe separated values of keys of list already computed
#  and cached. Those lists should be excluded when computing subsequent recommended movies
EXCLUDE_LIST_KEYS_KEY = 'exclude_list_keys'
MAX_CATEGORIES_IN_RECOMMENDATIONS = 5
TOTAL_RECOMMENDED = 12


def get_all_recommended(member, count):
    """
    Gets Media recommended for a Member based on the recently watched media categories
    :param member:
    :param count: Total number of media to grab
    :return: list of Movies and/or Series
    """
    if StreamLogEntry.objects.filter(member=member).count() == 0:
        recommended = []
    else:
        exclude_list_keys = set()
        cache_key_recommended = member.email + ':recommended'
        recommended = cache.get(cache_key_recommended)
        if recommended:
            return recommended

        cache_key_watched = member.email + ':already_watched'
        already_watched = cache.get(cache_key_watched)
        if not already_watched:
            already_watched = get_watched(member)
            if len(already_watched) > 0:
                cache.set(cache_key_watched, already_watched)
                exclude_list_keys.add(cache_key_watched)
        exclude_list = already_watched

        categories = get_watched_categories(already_watched)
        if len(categories) > 0:
            # Main category is the category of the media most recently watched
            main_category = categories[0]
            cnt = count - (len(categories) - 1)
            media = get_recommended_for_category(main_category, cnt, exclude_list)
            recommended = media
            exclude_list.extend(media)
        categories = categories[1:]
        for category in categories:  # Grab one item for each category other than the main
            media = get_recommended_for_category(category, 1, exclude_list)
            recommended.extend(media)
            exclude_list.extend(media)
        cache.set(cache_key_recommended, recommended)
        exclude_list_keys.add(cache_key_recommended)
        cache.set(member.email + ':' + EXCLUDE_LIST_KEYS_KEY, exclude_list_keys)
    return recommended


def get_recommended_for_category(category, count, exclude_list):
    """
    Pulls media recommended for given category. It merely consists of pulling media that are not in the exclude_list,
    which in this case stands for media that were already watched by the user. It is performed this way:
    We search for elements in the category. While items found are less than count, then search continues.
    We stop if we have been through all the movies or if we reach count items

    :param category: A "natural" (category.smart=False) categories to recommend from
    :param count: total number of elements to collect
    :param exclude_list: an arbitrary list of movies to exclude from the result
    :return: list of recommended movies and series
    """
    movies_count, series_count = get_movies_series_share(count)
    recommended = []
    if movies_count > 0:
        movies_qs = Movie.objects.raw_query({'categories': {'$elemMatch': {'id': ObjectId(category.id)}}, 'visible': True})
        for movie in movies_qs.order_by('-release', '-fake_clicks', '-fake_orders', '-id'):
            if movie not in recommended and movie not in exclude_list and len(recommended) < movies_count:
                recommended.append(movie)
    if series_count > 0:
        series_qs = Series.objects.raw_query({'categories': {'$elemMatch': {'id': ObjectId(category.id)}}, 'visible': True})
        for series in series_qs.order_by('-release', '-season', '-id'):
            if series not in recommended and series not in exclude_list and len(recommended) < count:
                recommended.append(series)
    return recommended


def get_movies_series_share(count, category=None):
    """
    Gives the number of movies and series to pull from the database whenever we want to get a total of "count" media
    It calculates the ratio of each type of media based of their respective total items in the given category.
    :param count:
    :param category:
    :return: tuple movies_count, series_count
    """
    if category:
        total_movies = Movie.objects.raw_query({'categories': {'$elemMatch': {'id': ObjectId(category.id)}}, 'visible': True}).count()
        total_series = Series.objects.raw_query({'categories': {'$elemMatch': {'id': ObjectId(category.id)}}, 'visible': True}).count()
    else:
        total_movies = Movie.objects.filter(visible=True).count()
        total_series = Series.objects.filter(visible=True).count()
    if count == 1:
        if total_movies > total_series:
            return 1, 0
        else:
            return 0, 1
    if total_movies + total_series == count:
        return total_movies, total_series
    total_media = total_movies + total_series
    movies_count = total_movies * count / total_media
    series_count = count - movies_count
    return movies_count, series_count


def get_watched_categories(watched_media):
    categories = []
    for media in watched_media:
        for category in media.categories:
            # Media categories are embedded, so check the smart status
            # from the original category. So re-get from the database
            if not Category.objects.get(pk=category.id).smart:
                categories.append(category)
    return categories


def clear_user_cache(member):
    """
    Delete all the exclude list from the cache, as well as the list containing their keys
    :param member:
    :return:
    """
    elk_key = member.email + ':' + EXCLUDE_LIST_KEYS_KEY
    exclude_list_keys = cache.get(elk_key)
    if exclude_list_keys:
        exclude_list_keys.add(elk_key)
        cache.delete_many(exclude_list_keys)


def as_matrix(movies_list, column_count):
    row = []
    matrix = []
    for elt in movies_list:
        if len(row) < column_count - 1:
            row.append(elt)
        else:
            row.append(elt)
            matrix.append(row)
            row = []
    return matrix