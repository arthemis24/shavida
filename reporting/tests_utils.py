# -*- coding: utf-8 -*-

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import json
import os
from django.conf import settings
from django.core.management import call_command

from django.utils.unittest import TestCase
from django.test.client import Client
from movies.models import Movie, Series, Category, SeriesEpisode
from ikwen.models import Member
from movies.tests_views import wipe_test_data
from movies.utils import get_recommended_for_category
from reporting.models import StreamLogEntry
from reporting.utils import reduce_stream_log_entries, get_watched, get_ordered, generate_add_list_info, \
    add_media_to_update
from sales.models import RetailPrepayment, ContentUpdate


class ReportingUtilsTest(TestCase):
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

    def test_reduce_stream_log_entries(self):
        member = Member.objects.get(pk='56eb6d04b37b3379b531e011')
        reduce_stream_log_entries(member)
        self.assertEqual(StreamLogEntry.objects.all().count(), 3)
        for entry in StreamLogEntry.objects.all():
            self.assertEqual(entry.status, StreamLogEntry.REDUCED)
        entry1 = StreamLogEntry.objects.all().order_by('id')[0]
        entry2 = StreamLogEntry.objects.all().order_by('id')[1]
        entry3 = StreamLogEntry.objects.all().order_by('id')[2]
        self.assertEqual(entry1.bytes, 730000)
        self.assertEqual(entry2.bytes, 780000)
        self.assertEqual(entry3.bytes, 765000)

    def test_get_watched(self):
        member = Member.objects.get(pk='56eb6d04b37b3379b531e011')
        watched = get_watched(member)
        expected = [Movie.objects.get(pk=pk) for pk in ['56eb6d04b37b3379b531e082', '56eb6d04b37b3379b531e081', '56eb6d04b37b3379b531e083']]
        self.assertListEqual(watched, expected)

    def test_generate_add_list_info(self):
        serialized_items = '56eb6d04b37b3379b531e081|movie,56eb6d04b37b3379b531e082|movie,' \
                           '56eb6d04b37b3379b531e083|movie,56eb6d04b37b3379b531e061|seriesepisode,' \
                           '56eb6d04b37b3379b531e062|seriesepisode,56eb6d04b37b3379b531e063|seriesepisode,'
        info = generate_add_list_info(serialized_items)
        expected_add_list = [Movie.objects.get(pk=pk).filename for pk in ('56eb6d04b37b3379b531e081', '56eb6d04b37b3379b531e082', '56eb6d04b37b3379b531e083')]
        expected_add_list.extend([SeriesEpisode.objects.get(pk=pk).filename for pk in ('56eb6d04b37b3379b531e061', '56eb6d04b37b3379b531e062', '56eb6d04b37b3379b531e063')])
        self.assertEqual(info['add_list'], ','.join(expected_add_list))
        self.assertEqual(info['add_list_size'], 450 + 1023)
        self.assertEqual(info['add_list_duration'], 270 + 120)

    def test_add_media_to_update(self):
        serialized_items = '56eb6d04b37b3379b531e081|movie,56eb6d04b37b3379b531e082|movie,' \
                           '56eb6d04b37b3379b531e083|movie,56eb6d04b37b3379b531e061|seriesepisode,' \
                           '56eb6d04b37b3379b531e062|seriesepisode,56eb6d04b37b3379b531e063|seriesepisode,'
        member = Member.objects.get(pk='56eb6d04b37b3379b531e012')
        update = ContentUpdate.objects.create(member=member)
        add_media_to_update(serialized_items, update)
        expected_movies_add_list = [Movie.objects.get(pk=pk) for pk in ('56eb6d04b37b3379b531e081', '56eb6d04b37b3379b531e082', '56eb6d04b37b3379b531e083')]
        expected_episodes_add_list = [SeriesEpisode.objects.get(pk=pk) for pk in ('56eb6d04b37b3379b531e061', '56eb6d04b37b3379b531e062', '56eb6d04b37b3379b531e063')]
        self.assertEqual(update.movies_add_list, expected_movies_add_list)
        self.assertEqual(update.series_episodes_add_list, expected_episodes_add_list)

    def test_get_ordered(self):
        member = Member.objects.get(pk='56eb6d04b37b3379b531e012')
        ordered = get_ordered(member)
        expected = [Movie.objects.get(pk=pk) for pk in ['56eb6d04b37b3379b531e081', '56eb6d04b37b3379b531e082']]
        expected.append(Series.objects.get(pk='56eb6d04b37b3379b531e071'))
        self.assertEqual(len(ordered), len(expected))
        for medium in ordered:
            self.assertIn(medium, expected)