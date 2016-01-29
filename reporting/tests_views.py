# -*- coding: utf-8 -*-

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import json

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import Client
from django.utils.unittest import TestCase
from django.test.utils import override_settings
from movies.models import Movie, SeriesEpisode, Trailer
from ikwen.models import Member

from movies.tests_views import wipe_test_data
from sales.models import ContentUpdate, SalesConfig
from sales.models import RetailPrepayment


class ReportingViewsTest(TestCase):
    """
    This test derives django.utils.unittest.TestCate rather than the default django.test.TestCase.
    Thus, self.client is not automatically created and fixtures not automatically loaded. This
    will be achieved manually by a custom implementation of setUp()
    """
    fixtures = ['cms.yaml', 'members.yaml', 'categories.yaml', 'movies.yaml', 'content_updates.yaml', 'prepayments.yaml']

    def setUp(self):
        self.client = Client()
        for fixture in self.fixtures:
            if fixture == 'members.yaml':
                call_command('loaddata', fixture, database='umbrella')
            call_command('loaddata', fixture)

    def tearDown(self):
        wipe_test_data()

    def test_get_repo_setup_files_with_wrong_provider_credentials(self):
        """
        Return a JSON error message if wrong username and/or password
        """
        username = 'simo'
        response = self.client.get(reverse('reporting:get_repo_setup_files'), {'username': username, 'password': 'admin'})
        json_resp = json.loads(response.content)
        self.assertEqual(json_resp['error'], "Could not authenticate user %s with password." % username)

    def test_get_repo_setup_files_with_unexisting_operator_username(self):
        """
        Return a JSON error message if wrong operator_username
        """
        operator_username = 'simo'
        response = self.client.get(reverse('reporting:get_repo_setup_files'),
                                   {'username': 'member1@ikwen.com', 'password': 'admin', 'operator_username': operator_username})
        json_resp = json.loads(response.content)
        self.assertEqual(json_resp['error'], "Member not found with username %s" % operator_username)

    @override_settings(UNIT_TESTING=True, SALES_UNIT=SalesConfig.DATA_VOLUME)  # Avoid trying to save in database other than default
    def test_get_repo_setup_files_with_everything_ok(self):
        """
        Return a JSON list of filename
        """
        response = self.client.get(reverse('reporting:get_repo_setup_files'),
                                   {'username': 'member1@ikwen.com', 'password': 'admin', 'operator_username': 'member2@ikwen.com',
                                    'movies_max_load': '200000', 'series_max_load': '450000'})
        media1 = set()
        for movie in Movie.objects.all():
            for filename in movie.filename.split(','):
                media1.add(filename.strip())
                if movie.trailer_slug:
                    trailer = Trailer.objects.get(slug=movie.trailer_slug)
                    media1.add(trailer.filename)
        for episode in SeriesEpisode.objects.all():
            media1.add(episode.filename)
            if episode.series.trailer_slug:
                trailer = Trailer.objects.get(slug=episode.series.trailer_slug)
                media1.add(trailer.filename)
        json_response = json.loads(response.content)
        media2 = []
        for item in json_response:
            filenames = item.filename.split(',')  # Some movies have filename in multiple parts separated by comma
            for filename in filenames:
                filename = filename.strip()
                media2.append(filename)
        self.assertEqual(len(media1), len(media2))
        for m in media1:
            self.assertIn(m, media2)
        update = ContentUpdate.objects.order_by('-id')[0]  # ContentUpdate object must have been created in default database

    def test_get_repo_files_update_with_wrong_provider_credentials(self):
        """
        Return a JSON error message if wrong username and/or password
        """
        username = 'simo'
        response = self.client.get(reverse('reporting:get_repo_files_update'), {'username': username, 'password': 'admin'})
        json_resp = json.loads(response.content)
        self.assertEqual(json_resp['error'], "Could not authenticate user %s with password." % username)

    def test_get_repo_files_update_with_unexisting_operator_username(self):
        """
        Return a JSON error message if wrong operator_username
        """
        operator_username = 'simo'
        response = self.client.get(reverse('reporting:get_repo_files_update'),
                                   {'username': 'member1@ikwen.com', 'password': 'admin', 'operator_username': operator_username})
        json_resp = json.loads(response.content)
        self.assertEqual(json_resp['error'], "Member not found with username %s" % operator_username)

    @override_settings(UNIT_TESTING=True, SALES_UNIT=SalesConfig.DATA_VOLUME)  # Avoid trying to save in database other than default
    def test_get_repo_files_update_with_insufficient_space(self):
        """
        Return a JSON error message if wrong insufficient space
        """
        member = Member.objects.get(email='member2@ikwen.com')
        add_list = ['top-movie.part1.mp4', 'top-movie.part2.mp4', 'Daredevil.saison1/Daredevil-s01e01.mp4']
        delete_list = ['hd-movie.mp4', 'western-movie.mp4']
        ContentUpdate.objects.get(member=member).delete()
        ContentUpdate.objects.create(member=member, add_list=','.join(add_list), add_list_size=100000,
                                     delete_list=','.join(delete_list), delete_list_size=15000, status=ContentUpdate.AUTHORIZED)
        response = self.client.get(reverse('reporting:get_repo_files_update'),
                                   {'username': 'member1@ikwen.com', 'password': 'admin', 'operator_username': 'member2@ikwen.com',
                                    'available_space': '35000'})
        needed_space_str = "%.2f GB" % (50000 / 1000.0)
        json_resp = json.loads(response.content)
        self.assertEqual(json_resp['error'], "Insufficient space on drive to run this update, Need %s more." % needed_space_str)

    @override_settings(UNIT_TESTING=True, SALES_UNIT=SalesConfig.DATA_VOLUME)  # Avoid trying to save in database other than default
    def test_get_repo_files_update_with_everything_ok(self):
        """
        Return a JSON list of filename
        """
        member = Member.objects.get(email='member2@ikwen.com')
        add_list = ['top-movie.part1.mp4', 'top-movie.part2.mp4', 'Daredevil.saison1/Daredevil-s01e01.mp4']
        delete_list = ['hd-movie.mp4', 'western-movie.mp4']
        RetailPrepayment.objects.create(member=member, balance=100000, amount=0)
        ContentUpdate.objects.get(member=member).delete()
        ContentUpdate.objects.create(member=member, add_list=','.join(add_list), add_list_size=40000,
                                     delete_list=','.join(delete_list), delete_list_size=15000, status=ContentUpdate.AUTHORIZED)
        response = self.client.get(reverse('reporting:get_repo_files_update'),
                                   {'username': 'member1@ikwen.com', 'password': 'admin', 'operator_username': 'member2@ikwen.com',
                                    'available_space': '35000'})
        update = json.loads(response.content)
        self.assertDictEqual(update, {'add_list': add_list, 'delete_list': delete_list})
        update = ContentUpdate.objects.order_by('-id')[0]
        prepayment = RetailPrepayment.objects.filter(member=member).order_by('-id')[0]
        self.assertEqual(update.status, ContentUpdate.DELIVERED)
        self.assertEqual(prepayment.balance, 60000)

    def test_debit_user_with_direct_url_hit(self):
        """
        Hitting the URL directly should return an http 403 Forbidden error
        """
        response = self.client.get(reverse('reporting:debit_vod_balance'), {'bytes': '3000000'})
        self.assertTrue(response.status_code, 403)

    def test_debit_user(self):
        """
        Debiting user should cause VODPrepayment.balance to decrease by the number of bytes passed as parameter
        """
        self.client.login(email='member3@ikwen.com', password='admin')
        response = self.client.get(reverse('reporting:debit_vod_balance'), {'bytes': 3000000, 'duration': 3, 'type': 'movie', 'media_id': '56eb6d04b37b3379b531e081'},
                                   HTTP_REFERER='referer')
        json_content = json.loads(response.content)
        self.assertEqual(json_content['balance'], 197000000)
