# -*- coding: utf-8 -*-
import random

from django.conf import settings

from django.db import models
from django.db.models.signals import post_syncdb
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_mongodb_engine.contrib import MongoDBManager
from djangotoolbox.fields import ListField, EmbeddedModelField
from Shavida.fields import MultiImageField
from django.utils.translation import gettext as _
from ikwen.models import Member
from ikwen.utils import to_dict
from Shavida.utils import is_content_vendor, is_vod_operator
from sales.models import SalesConfig


def series_cmp_orders(s1, s2):
    if s1.orders > s2.orders:
        return 1
    elif s1.orders < s2.orders:
        return -1
    return 0


class Category(models.Model):
    """
    A category of movie
    """
    title = models.CharField(max_length=100, unique=True,
                             help_text=_("Title of the category."))
    slug = models.SlugField(max_length=100, unique=True,
                            help_text=_("Auto-filled. If edited, use only lowercase letters and -. Space is not allowed"
                                        " Eg: top-100"))
    is_adult = models.BooleanField(default=False,
                                   help_text=_("Check if it is supposed to contain adult movies."))
    smart = models.BooleanField(default=False,
                                help_text=_("Check if not a common category. Eg: 'Recent', 'Top 20' are good candidates"
                                            " for smart categories. They appear before normal categories in the list"
                                            " on the site."))
    order_of_appearance = models.IntegerField(help_text=_("Order of appearance in the list of categories."))
    appear_in_main = models.BooleanField(default=False,
                                         help_text=_("Check if you want it to be visible out of the 'More ...' section."))
    visible = models.BooleanField(default=True,
                                  help_text=_("Check if you want to make this category visible on the site"))
    previews_title = models.CharField(max_length=45, blank=True, null=True,
                                      help_text=_("Title you want to appear on the category preview on home page."
                                                  " If not set, the title will be used."))
    previews_length = models.PositiveSmallIntegerField(default=0,
                                                       help_text=_("Number of items you want to appear in the preview"
                                                                   " of the category on home page."))

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Media categories"


class MediaInterface():

    def _get_display_size(self):
        """
        Size of movie in a format suitable for display
        """
        return '%d MB' % self.size if self.size < 1024 else '%.2f GB' % (self.size / 1024.0)
    display_size = property(_get_display_size)

    def _get_display_duration(self):
        """
        Duration of the movie in a format suitable for display
        """
        duration = self.duration
        return '%dmn' % duration if duration < 60 else '%dh%dmn' % (duration / 60, duration % 60)
    display_duration = property(_get_display_duration)

    def _get_load(self):
        """
        Load represented by media depending on the unit of sales in sales.models.SalesConfig
        duration if unit == 'Broadcasting', size otherwise
        """
        unit = getattr(settings, 'SALES_UNIT', SalesConfig.BROADCASTING_TIME)
        return self.duration if unit == SalesConfig.BROADCASTING_TIME else self.size
    load = property(_get_load)

    def _get_display_load(self):
        """
        Load in a format suitable for display depending on the unit of sales in sales.models.SalesConfig
        duration if unit == 'Broadcasting', size otherwise
        """
        unit = getattr(settings, 'SALES_UNIT', SalesConfig.BROADCASTING_TIME)
        return self.display_duration if unit == SalesConfig.BROADCASTING_TIME else self.display_size
    display_load = property(_get_display_load)


class Media(models.Model, MediaInterface):
    title = models.CharField(max_length=100,
                             help_text=_("Title of the media."))
    size = models.PositiveIntegerField(help_text=_("Size in MegaBytes (MB) of the file."))
    duration = models.PositiveIntegerField(help_text=_("Duration in minutes of the media file."))
    clicks = models.PositiveIntegerField(default=0,
                                         help_text=_("Number of times movie was clicked for streaming. Can be considered "
                                                     "as the number of view in a certain way."))
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    class Meta:
        abstract = True


class Trailer(Media):
    """
    Trailer of a Movie or Series
    """
    slug = models.SlugField(unique=True,
                            help_text=_("Auto-filled. If edited, use only lowercase letters and -. Space is not allowed"
                                        " Eg: trailer-tomorrow-never-dies"))
    filename = models.CharField(max_length=255, unique=True)


class Movie(Media):
    objects = MongoDBManager()
    MAX_RECENT = 96
    TOTAL_RECOMMENDED = 12  # Number of items to recommend in a case where there are enough to recommend
    MIN_RECOMMENDED = 8  # Number of items to recommend in case where there are not enough after the normal algorithm
    slug = models.SlugField(unique=True,
                            help_text=_("Auto-filled. If edited, use only lowercase letters and -. Space is not allowed"
                                        " Eg: tomorrow-never-dies"))
    release = models.DateField(blank=True, null=True,
                               help_text=_("Date of release of movie in country of origin."))
    synopsis = models.TextField(blank=True)
    filename = models.CharField(max_length=255, unique=True)
    poster = MultiImageField(upload_to='movies', blank=True, null=True)
    price = models.PositiveIntegerField(editable=is_content_vendor,
                                        help_text=_("Cost of sale of this movie to VOD operators."))
    trailer_slug = models.SlugField(blank=True, null=True,
                                    help_text=_("Slug of the trailer bound to this movie."))
    provider = models.ForeignKey(Member, editable=is_vod_operator, blank=True, null=True,
                                 help_text=_("Provider of this movie."))
    fake_orders = models.IntegerField(help_text=_("Random value you want customers to think the movie was ordered "
                                                  "that number of times."))
    orders = models.IntegerField(default=0,
                                 help_text=_("Number of times movie was actually ordered."))
    fake_clicks = models.PositiveIntegerField(help_text=_("Random value you want customers to think the movie was "
                                                          "viewed that number of times."))
    visible = models.BooleanField(default=True,
                                  help_text=_("Check if you want the movie to be visible on the site."))
    categories = ListField(EmbeddedModelField('Category'),
                           help_text=_("Categories the movie is part of."))
    # Tells whether this Movie is part of an Adult category.
    # Set automatically upon Movie.save() by checking categories
    is_adult = models.BooleanField(default=False, editable=False)
    groups = models.CharField(max_length=100, default='', blank=True,
                              help_text=_("Group the movie belongs to (write lowercase). Will be used for suggestions "
                                          "Eg: Matrix 1, 2 and 3 are all part of group matrix"))
    tags = models.CharField(max_length=150,
                            help_text=_("Key words used to retrieve the movie in search. Typically title of movie written "
                                        "lowercase and main actors, all separated by space. Eg: matrix keanu reaves"))
    # Random field used for random selections in MongoDB
    rand = models.FloatField(default=random.random, db_index=True, editable=False)

    def _get_display_orders(self):
        """
        Number of orders(based on fake_orders) of movie in a format suitable for display
        """
        if self.fake_orders < 1000:
            return self.fake_orders
        else:
            num500 = self.fake_orders / 500
            return "%d+" % (num500 * 500)
    display_orders = property(_get_display_orders)

    def _get_display_clicks(self):
        """
        Number of clicks(based on fake_clicks) of movie in a format suitable for display
        """
        if self.fake_clicks < 1000:
            return self.fake_clicks
        else:
            num500 = self.fake_clicks / 500
            return "%d+" % (num500 * 500)
    display_clicks = property(_get_display_clicks)

    def _get_categories_to_string(self):
        categories = [category.title for category in self.categories]
        return ", ".join(categories)
    categories_to_string = property(_get_categories_to_string)

    def to_dict(self):
        var = to_dict(self)
        var['poster'] = {
            'url': self.poster.url if self.poster else 'static.cinemax.club/media/images/default_poster.jpg',
            'small_url': self.poster.small_url if self.poster.name else 'static.cinemax.club/media/images/default_poster_small.jpg',
            'thumb_url': self.poster.thumb_url if self.poster.name else 'static.cinemax.club/media/images/default_poster_thumb.jpg'
        }
        var['type'] = 'movie'
        var['display_orders'] = self.display_orders
        var['display_clicks'] = self.display_clicks
        var['load'] = self.load
        var['display_load'] = self.display_load
        del(var['filename'])
        del(var['release'])
        del(var['synopsis'])
        del(var['provider_id'])
        del(var['visible'])
        del(var['fake_orders'])
        del(var['fake_clicks'])
        del(var['categories'])
        del(var['groups'])
        del(var['rand'])
        del(var['created_on'])
        del(var['updated_on'])
        return var

    def __unicode__(self):
        return self.title


class Series(models.Model, MediaInterface):
    objects = MongoDBManager()
    SLUG = 'series'
    title = models.CharField(max_length=100,
                             help_text=_("Title of the series."))
    season = models.PositiveSmallIntegerField()
    slug = models.SlugField(max_length=100, unique=True,
                            help_text=_("Auto filled. But add -seasonX manually. Eg: arrow-saison3"))
    release = models.DateField(blank=True, null=True,
                               help_text=_("Date of release of movie in country of origin."))
    episodes_count = models.PositiveIntegerField(help_text="Number of episodes of this series.")  # Number of episodes
    synopsis = models.TextField()
    poster = MultiImageField(upload_to='series', blank=True, null=True)
    provider = models.ForeignKey(Member, editable=is_vod_operator, blank=True, null=True,
                                 help_text=_("Provider of this series."))
    price = models.PositiveIntegerField(editable=is_content_vendor,
                                        help_text=_("Cost of sale of this series to VOD operators."))
    # Tells whether this Movie is part of an Adult category.
    # Set automatically upon Movie.save() by checking categories
    is_adult = models.BooleanField(default=False, editable=False)
    trailer_slug = models.SlugField(blank=True, null=True,
                                    help_text=_("Slug of the trailer bound to this series."))
    categories = ListField(EmbeddedModelField('Category'),
                           help_text=_("Categories the series is part of."))
    visible = models.BooleanField(default=True)
    groups = models.CharField(max_length=100, default='', blank=True,
                              help_text=_("Group the series belongs to (write lowercase). Will be used for suggestions "
                                          "Eg: Scandal season 1, 2, 3 ... are all part of group scandal"))
    tags = models.CharField(max_length=150,
                            help_text=_("Key words used to retrieve the series in search. Typically title of movie written "
                                        "lowercase and main actors, all separated by space. Eg: scandal keanu reaves"))
    # Random field used for random selections in MongoDB
    rand = models.FloatField(default=random.random, db_index=True, editable=False)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Series'
        unique_together = ('title', 'season', )

    def _get_display_orders(self):
        """
        Number of orders(based on fake_orders) of the series.
        Is arbitrarily considered as the number of fake_orders of the first episode of the series.
        It is returned in a format suitable for display
        """
        query_set = SeriesEpisode.objects.filter(series=self.id)
        first_episode = query_set[0] if len(query_set) > 0 else None
        if first_episode:
            if first_episode.fake_orders < 1000:
                return first_episode.fake_orders
            else:
                num500 = first_episode.fake_orders / 500
                return "%d+" % (num500 * 500)
        else:
            return 20  # This is an arbitrary value
    display_orders = property(_get_display_orders)

    def _get_display_clicks(self):
        """
        Number of clicks(based on fake_clicks) of the series.
        Is arbitrarily considered as the number of fake_clicks of the first episode of the series.
        It is returned in a format suitable for display
        """
        query_set = SeriesEpisode.objects.filter(series=self.id)
        first_episode = query_set[0] if len(query_set) > 0 else None
        if first_episode:
            if first_episode.fake_clicks < 1000:
                return first_episode.fake_clicks
            else:
                num500 = first_episode.fake_clicks / 500
                return "%d+" % (num500 * 500)
        else:
            return 150  # This is an arbitrary value
    display_clicks = property(_get_display_clicks)

    def _get_orders(self):
        """
        Calculate the number of orders of the series as the average number of orders of the episodes.
        """
        episodes = SeriesEpisode.objects.filter(series=self.id)
        if len(episodes) == 0:
            return 0
        total_orders = 0
        for episode in episodes:
            total_orders += episode.orders
        return total_orders / len(episodes)
    orders = property(_get_orders)

    def _get_clicks(self):
        """
        Calculate the number of clicks of the series as the average number of clicks of the episodes.
        """
        episodes = SeriesEpisode.objects.filter(series=self.id)
        if len(episodes) == 0:
            return 0
        total_clicks = 0
        for episode in episodes:
            total_clicks += episode.orders
        return total_clicks / len(episodes)
    clicks = property(_get_clicks)

    def _get_size(self):
        """
        Calculate the size of the series by summing up the size of episodes individual files.
        """
        sizes = [series_episode.size for series_episode in SeriesEpisode.objects.filter(series=self)]
        return reduce(lambda x, y: x + y, sizes) if len(sizes) > 0 else 0
    size = property(_get_size)

    def _get_duration(self):
        """
        Calculate the duration of the series by summing up the duration of episodes individual files.
        """
        durations = [series_episode.duration for series_episode in SeriesEpisode.objects.filter(series=self)]
        return reduce(lambda x, y: x + y, durations) if len(durations) > 0 else 0
    duration = property(_get_duration)

    def _get_categories_to_string(self):
        categories = [category.title for category in self.categories]
        return ", ".join(categories)
    categories_to_string = property(_get_categories_to_string)

    def _get_episodes(self):
        """
        Gets the list of episodes of this series
        """
        return [series_episode for series_episode in SeriesEpisode.objects.filter(series=self)]
    episodes = property(_get_episodes)

    def to_dict(self):
        var = to_dict(self)
        var['poster'] = {
            'url': self.poster.url if self.poster else 'static.cinemax.club/media/images/default_poster.jpg',
            'small_url': self.poster.small_url if self.poster.name else 'static.cinemax.club/media/images/default_poster_small.jpg',
            'thumb_url': self.poster.thumb_url if self.poster.name else 'static.cinemax.club/media/images/default_poster_thumb.jpg'
        }
        var['type'] = 'series'
        var['display_orders'] = self.display_orders
        var['display_clicks'] = self.display_clicks
        var['display_load'] = self.display_load
        del(var['release'])
        del(var['rand'])
        del(var['synopsis'])
        del(var['provider_id'])
        del(var['visible'])
        del(var['groups'])
        del(var['categories'])
        del(var['created_on'])
        del(var['updated_on'])
        return var

    def __unicode__(self):
        return "%s Season %d" % (self.title, self.season)


class SeriesEpisode(Media):
    series = models.ForeignKey(Series)
    slug = models.SlugField(help_text=_("Auto-filled. If edited, use only lowercase letters and -. Space is not allowed"
                                        " Eg: arrow-s03e04"))
    release = models.DateField(blank=True, null=True, editable=False)
    filename = models.CharField(max_length=255, unique=True)
    provider = models.ForeignKey(Member, editable=is_vod_operator, blank=True, null=True,
                                 help_text=_("Provider of this series episode."))
    fake_orders = models.IntegerField()
    orders = models.IntegerField(default=0)
    fake_clicks = models.PositiveIntegerField()
    # Tells whether this Movie is part of an Adult category.
    # Set automatically upon Movie.save() by checking categories
    is_adult = models.BooleanField(default=False, editable=False)

    def to_dict(self):
        var = to_dict(self)
        var['poster'] = {
            'url': self.series.poster.url if self.series.poster else 'static.cinemax.club/media/images/default_poster.jpg',
            'small_url': self.series.poster.small_url if self.series.poster.name else 'static.cinemax.club/media/images/default_poster_small.jpg',
            'thumb_url': self.series.poster.thumb_url if self.series.poster.name else 'static.cinemax.club/media/images/default_poster_thumb.jpg'
        }
        var['type'] = 'series'
        var['orders'] = 'fake_orders'
        var['clicks'] = 'fake_clicks'
        var['load'] = self.load
        del(var['filename'])
        del(var['fake_orders'])
        del(var['created_on'])
        del(var['updated_on'])
        return var

    def __unicode__(self):
        return self.title


@receiver(post_syncdb)
def create_text_index_on_tags_and_groups(sender, **kwargs):
    from pymongo import MongoClient
    client = MongoClient()
    db_name = getattr(settings, 'DATABASES')['default']['NAME']
    db = client[db_name]
    db.movies_movie.create_index([('tags', 'text'), ('groups', 'text')])
    db.movies_series.create_index([('tags', 'text'), ('groups', 'text')])