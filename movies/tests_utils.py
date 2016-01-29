# -*- coding: utf-8 -*-

from django.core.cache import cache
from django.core.management import call_command
from django.test.utils import override_settings
from django.utils.unittest import TestCase
from django.test.client import Client
from movies.models import Movie, Series, Category
from ikwen.models import Member
from movies.tests_views import wipe_test_data
from movies.utils import get_recommended_for_category, get_watched_categories, EXCLUDE_LIST_KEYS_KEY, \
    get_all_recommended
from reporting.utils import get_watched


class MoviesUtilsTest(TestCase):
    """
    This test derives django.utils.unittest.TestCate rather than the default django.test.TestCase.
    Thus, self.client is not automatically created and fixtures not automatically loaded. This
    will be achieved manually by a custom implementation of setUp()
    """
    fixtures = ['cms.yaml', 'members.yaml', 'categories.yaml', 'movies.yaml', 'log_entries.yaml', 'content_updates.yaml']

    def setUp(self):
        self.client = Client()
        for fixture in self.fixtures:
            if fixture == 'members.yaml':
                call_command('loaddata', fixture, database='umbrella')
            call_command('loaddata', fixture)

    def tearDown(self):
        wipe_test_data()

    def test_get_recommended_for_category(self):
        category_id = '56eb6d04b37b3379b531e092'
        category_western = Category.objects.get(pk=category_id)
        for movie in Movie.objects.all():
            movie.categories.append(category_western)
            movie.save()
        for series in Series.objects.all():
            series.categories.append(category_western)
            series.save()
        items_to_exclude = [Movie.objects.get(pk=pk) for pk in ('56eb6d04b37b3379b531e085', '56eb6d04b37b3379b531e086')]
        media = get_recommended_for_category(category_western, 5, items_to_exclude)
        expected_media = [Movie.objects.get(pk=pk) for pk in ('56eb6d04b37b3379b531e084', '56eb6d04b37b3379b531e083', '56eb6d04b37b3379b531e082')]
        expected_media.extend([Series.objects.get(pk=pk) for pk in ('56eb6d04b37b3379b531e074', '56eb6d04b37b3379b531e073')])
        for item in media:
            self.assertIn(item, expected_media)

    def test_get_watched_categories_with_no_smart_category(self):
        """
        categories of media watched are returned from most recent watched to less recent watched
        :return:
        """
        member = Member.objects.get(pk='56eb6d04b37b3379b531e011')
        watched = get_watched(member)
        watched_categories = get_watched_categories(watched)
        expected_categories = [Category.objects.get(pk=pk) for pk in ('56eb6d04b37b3379b531e092', '56eb6d04b37b3379b531e091', '56eb6d04b37b3379b531e093')]
        self.assertListEqual(watched_categories, expected_categories)

    def test_get_watched_categories_with_one_smart_category(self):
        """
        smart categories should not be taken into account in get_watched_categories
        :return:
        """
        category = Category.objects.get(pk='56eb6d04b37b3379b531e091')
        category.smart = True
        category.save()
        member = Member.objects.get(pk='56eb6d04b37b3379b531e011')
        watched = get_watched(member)
        watched_categories = [category.slug for category in get_watched_categories(watched)]
        expected_categories = [Category.objects.get(pk=pk).slug for pk in ('56eb6d04b37b3379b531e092', '56eb6d04b37b3379b531e093')]
        self.assertListEqual(watched_categories, expected_categories)

    @override_settings(CACHES={  # Override the CACHES settings to avoid interference if running tests on prod server
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211'
        }
    })
    def test_get_all_recommended(self):
        """
        Pulls recommended media based on the ones previously watched. The so recommended items must be put in cache
        :return:
        """
        member = Member.objects.get(pk='56eb6d04b37b3379b531e011')
        category_western = Category.objects.get(pk='56eb6d04b37b3379b531e092')
        for series in Series.objects.all():
            series.categories.append(category_western)
            series.save()
        exclude_list_keys_key = 'member1@ikwen.com:' + EXCLUDE_LIST_KEYS_KEY
        cache_key_watched = 'member1@ikwen.com:already_watched'
        cache_key_recommended = 'member1@ikwen.com:recommended'
        cache.delete(exclude_list_keys_key)
        cache.delete(cache_key_watched)
        cache.delete(cache_key_recommended)
        self.client.login(email='member1@ikwen.com', password='admin')
        # exclude_list_keys = {cache_key_watched}
        # watched_media = [Movie.objects.get(pk='56eb6d04b37b3379b531e085')]
        # cache.set(exclude_list_keys_key, exclude_list_keys)
        # cache.set(cache_key_watched, watched_media)
        other_adult_movie = Movie.objects.get(pk='56eb6d04b37b3379b531e083')
        other_adult_movie.id = None
        other_adult_movie.slug = 'other-adult-movie'
        other_adult_movie.filename = 'other-adult-movie.mp4'
        other_adult_movie.title = 'Other adult movie'
        other_adult_movie.save()
        all_recommended_media = get_all_recommended(member, 6)
        expected_media = [Movie.objects.get(pk=pk) for pk in ('56eb6d04b37b3379b531e086', '56eb6d04b37b3379b531e085')]
        expected_media.extend([Series.objects.get(pk=pk) for pk in ('56eb6d04b37b3379b531e074', '56eb6d04b37b3379b531e073')])
        expected_media.append(other_adult_movie)
        cached_recommended = cache.get(cache_key_recommended)
        cached_ex_list_keys = cache.get(exclude_list_keys_key)
        self.assertListEqual(all_recommended_media, expected_media)
        self.assertListEqual(all_recommended_media, cached_recommended)
        for key in cached_ex_list_keys:
            self.assertIn(key, [cache_key_watched, cache_key_recommended])
        cache.delete(exclude_list_keys_key)
        cache.delete(cache_key_watched)
        cache.delete(cache_key_recommended)
