# -*- coding: utf-8 -*-
from copy import copy

from datetime import timedelta
from django.db import models
from django.utils import timezone
from djangotoolbox.fields import ListField, EmbeddedModelField
from ikwen.models import Member
from django.utils.translation import gettext as _
from ikwen.utils import to_dict
from Shavida.utils import is_vod_operator


class SalesConfig(models.Model):
    BROADCASTING_TIME = "Broadcasting"
    DATA_VOLUME = "Volume"
    UNITS_CHOICES = (
        (BROADCASTING_TIME, _("Broadcasting Time")),
        (DATA_VOLUME, _("Data Volume")),
    )
    max_inactivity = models.PositiveIntegerField(default=14,
                                                 help_text=_("Number of days after which user is considered inactive."))
    free_trial = models.BooleanField(default=True,
                                     help_text=_("Check to activate free trial bundle for you customers."))
    welcome_offer = models.BooleanField(default=200,
                                        help_text=_("Number of MegaBytes offered for free trial."))
    welcome_offer_duration = models.BooleanField(default=30,
                                                 help_text=_("Number of days left to use free trial."))
    # unit = models.CharField(max_length=30, choices=UNITS_CHOICES,
    #                         help_text=_("Your trade measurement."))


class RetailBundle(models.Model):
    name = models.CharField(unique=True, max_length=30,
                            help_text=_("How you call this plan."))
    quantity = models.PositiveIntegerField(unique=True,
                                           help_text=_("Number of hours or Number of MegaBytes depending "
                                                       "on your unit of trade."))
    cost = models.PositiveIntegerField(help_text=_("Cost of this bundle."))
    comment = models.CharField(max_length=60, blank=True, null=True,
                               help_text=_("Additional information about this bundle that may help user."))
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now, auto_now_add=True)
    # share = models.IntegerField(editable=is_content_vendor, blank=True, null=True,
    #                             help_text=_("Percentage you collect from this operator on his turnover."))

    def __unicode__(self):
        return self.name


class Plan(models.Model):
    bundle = EmbeddedModelField('RetailBundle')
    start = models.DateTimeField()
    finish = models.DateTimeField()
    duration = models.PositiveIntegerField()
    total_cost = models.PositiveIntegerField()
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now, auto_now_add=True)

    def __unicode__(self):
        return self.bundle.name


class VODBundle(models.Model):
    volume = models.PositiveSmallIntegerField(unique=True,
                                              help_text=_("Amount of MegaBytes of available for the customer "
                                                          "(1 GigaBytes = 1000 MegaBytes)."))
    cost = models.FloatField(unique=True,
                             help_text=_("Cost of the bundle."))
    duration = models.PositiveSmallIntegerField(help_text=_("Number of days the customer must take to view empty his bundle. "
                                                            "After that it is automatically brought back to 0."))
    adult_authorized = models.BooleanField(default=False,
                                           help_text=_("Check it this bundle gives access to adult content."))
    comment = models.CharField(max_length=60, blank=True, null=True,
                               help_text=_("Additional information about this bundle that may help user."))
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now, auto_now_add=True)


class Prepayment(models.Model):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (CONFIRMED, "Confirmed"),
    )
    member = models.ForeignKey(Member)
    amount = models.PositiveIntegerField()
    paid_on = models.DateTimeField(blank=True, null=True)
    duration = models.PositiveSmallIntegerField(default=30,
                                                help_text=_("Number of days for this to expire."))
    status = models.CharField(choices=STATUS_CHOICES, max_length=15, default=PENDING)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now, auto_now_add=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.member.email

    def _get_display_created_on(self):
        return '%02d/%02d/%d %02d:%02d' % (self.when.day, self.when.month, self.when.year,
                                           self.when.hour, self.when.minute)
    display_created_on = property(_get_display_created_on)

    def _get_display_paid_on(self):
        return '%02d/%02d/%d %02d:%02d' % (self.paid_on.day, self.paid_on.month, self.paid_on.year,
                                           self.paid_on.hour, self.paid_on.minute)
    display_paid_on = property(_get_display_paid_on)

    def _get_display_expiry(self):
        expiry = self.when + timedelta(days=self.duration)
        return '%02d/%02d/%d' % (expiry.day, expiry.month, expiry.year)
    display_expiry = property(_get_display_expiry)

    def _get_days_left(self):
        """
        Number of days left for this RetailPrepayment to expire
        """
        if self.paid_on:
            spent = timezone.now() - self.paid_on
            return self.duration - spent.days
        return 30  # Return an arbitrary value of 30 days as long as the user didn't pay. The counter starts upon payment
    days_left = property(_get_days_left)


class RetailPrepayment(Prepayment):
    balance = models.PositiveIntegerField(help_text=_("Quantity you allow your customer to order depending on "
                                                      "your unit of sales. If selling volumes of data, give the value in"
                                                      "MegaBytes."))


class VODPrepayment(Prepayment):
    balance = models.PositiveIntegerField(help_text=_("The number of bytes of streaming remaining to the client. "
                                                      "(1 GigaBytes = 1,000,000,000 Bytes)"))
    adult_authorized = models.BooleanField(default=False,
                                           help_text=_("Check if you want customer to access adult content."))
    teller = models.ForeignKey(Member, blank=True, null=True, related_name='teller',
                               help_text=_("Staff who actually confirmed this Prepayment."))


# class Provider(models.Model):
#     member = models.ForeignKey(Member)
#     share = models.PositiveIntegerField(default=0,
#                                         help_text=_("Percentage you earn out of sales of the provider's content"))
#     created_on = models.DateTimeField(default=timezone.now)
#     updated_on = models.DateTimeField(default=timezone.now, auto_now_add=True)


class ContentUpdate(models.Model):
    PENDING = "Pending"
    AUTHORIZED = "Authorized"
    DELIVERED = "Delivered"
    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (AUTHORIZED, "Authorized"),
        (DELIVERED, "Delivered")
    )
    member = models.ForeignKey(Member)
    add_list = models.TextField(blank=True)
    movies_add_list = ListField(EmbeddedModelField('movies.Movie'), blank=True, null=True, editable=False)
    series_episodes_add_list = ListField(EmbeddedModelField('movies.SeriesEpisode'), blank=True, null=True, editable=False)
    add_list_size = models.PositiveIntegerField(default=0)
    add_list_duration = models.PositiveIntegerField(default=0)
    delete_list = models.TextField(blank=True)
    movies_delete_list = ListField(EmbeddedModelField('movies.Movie'), blank=True, null=True, editable=False)
    series_episodes_delete_list = ListField(EmbeddedModelField('movies.SeriesEpisode'), blank=True, null=True, editable=False)
    delete_list_size = models.PositiveIntegerField(default=0)
    cost = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=30, default=PENDING, choices=STATUS_CHOICES)
    provider = models.ForeignKey(Member, related_name="provider", blank=True, null=True, editable=is_vod_operator,
                                 help_text="Provider of this update.")
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now, auto_now_add=True)

    def _get_display_created_on(self):
        return '%02d/%02d/%d %02d:%02d' % (self.created_on.day, self.created_on.month, self.created_on.year,
                                           self.created_on.hour, self.created_on.minute)
    display_created_on = property(_get_display_created_on)

    def get_categories_share(self):
        from movies.models import Series
        share = {}
        count = 0
        for movie in self.movies.all():
            for category in movie.categories.all():
                count += 1
                if category.natural:
                    if share.get(category.slug):
                        share[category.slug] += 1
                    else:
                        share[category.slug] = 1

        share[Series.SLUG] = len(self.series_episodes_add_list)

        share_copy = copy(share)
        l = share.values()
        l.sort(reverse=True)
        sorted_share = []
        for i in range(len(l)):
            for key in share.keys():
                if share_copy.get(key) == l[i]:
                    sorted_share.append(key)
                    del(share_copy[key])
        return sorted_share

    def get_series(self):
        series = set()
        for series_episode in self.series_episodes_add_list:
            series.add(series_episode.series)
        return list(series)

    def to_dict(self, target=None):
        movies_add_list = self.movies_add_list
        series_episodes_add_list = self.series_episodes_add_list
        movies_delete_list = self.movies_delete_list
        series_episodes_delete_list = self.series_episodes_delete_list
        member = self.member.to_dict()
        var = to_dict(self)
        var['member'] = member
        var['display_created_on'] = self.display_created_on
        media_add_list = [movie.to_dict() for movie in movies_add_list]
        media_add_list.extend([episode.to_dict() for episode in series_episodes_add_list])
        media_delete_list = [movie.to_dict() for movie in movies_delete_list]
        media_delete_list.extend([episode.to_dict() for episode in series_episodes_delete_list])
        var['movies_add_list'] = media_add_list
        var['movies_delete_list'] = media_delete_list
        return var
