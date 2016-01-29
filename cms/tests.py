# -*- coding: utf-8 -*-
import cms.models
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.utils.unittest import TestCase
from django.test.client import Client

__author__ = "Kom Sihon"


class CMSTest(TestCase):
    """
    This test derives django.utils.unittest.TestCate rather than the default django.test.TestCase.
    Thus, self.client is not automatically created and fixtures not automatically loaded. This
    will be achieved manually by a custom implementation of setUp()
    """
    fixtures = ['cms.yaml']

    def setUp(self):
        self.client = Client()
        for fixture in self.fixtures:
            call_command('loaddata', fixture)

    def tearDown(self):
        """
        This test was originally built with django-nonrel 1.6 which had an error when flushing the database after
        each test. So the flush is performed manually with this custom tearDown()
        """
        for name in ('SiteConfig', 'FlatPage'):
            model = getattr(cms.models, name)
            for model in model.objects.all():
                model.delete()

    def test_flat_page(self):
        """
        Checks whether flat page url works fine
        """
        response = self.client.get(reverse('flat_page', args=('test-flat-page', )))
        self.assertEqual(response.status_code, 200)
