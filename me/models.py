# -*- coding: utf-8 -*-
from datetime import timedelta

from Shavida.utils import is_content_vendor
from django.conf import settings
from django.db import models
from django.utils import timezone
from ikwen.models import Member
from ikwen.utils import to_dict
from django.utils.translation import gettext as _
from sales.models import SalesConfig, RetailPrepayment, VODPrepayment, Plan, ContentUpdate

DEFAULT_SITE_IMAGE = 'plan/default_site_img.jpg'


class Profile(models.Model):
    """
    Member profile
    """
    member = models.OneToOneField(Member)
    # User must activate this from his profile to access adult content
    adult_authorized = models.BooleanField(default=False, editable=False)

    is_vod_operator = models.BooleanField(default=False, editable=is_content_vendor,
                                          help_text=_("Check if this customer is a VOD Operator."))
    # The home folder of cloud installation of this member copy of the application
    home_folder = models.CharField(max_length=60, editable=False)
    # share = models.IntegerField(editable=is_content_vendor, blank=True, null=True,
    #                             help_text=_("Percentage you collect from this operator on turnover."))
    # plan = models.ForeignKey(Plan, editable=is_content_vendor, blank=True, null=True,
    #                          help_text=_("Plan of this VOD Operator."))
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now, auto_now_add=True)

    def _get_days_passed_since_latest_order(self):
        orders = ContentUpdate.objects.filter(member=self.member).order_by('-id')
        latest_order = orders[0] if len(orders) > 0 else None
        now = timezone.now()
        passed_days = None
        if latest_order:
            passed_days = now - latest_order.when
        if passed_days is not None:
            return passed_days.days
        else:
            return None
    days_passed_since_latest_order = property(_get_days_passed_since_latest_order)

    _get_days_passed_since_latest_order.admin_order_field = 'days_passed_since_latest_order'
    _get_days_passed_since_latest_order.short_description = 'Days without order'

    def ordered_recently(self):
        sales_config = SalesConfig.objects.all()[0]
        if self.days_passed_since_latest_order is not None:
            if self.days_passed_since_latest_order <= sales_config.max_inactivity:
                return True
        return False
    ordered_recently.admin_order_field = 'ordered_recently'
    ordered_recently.boolean = True
    ordered_recently.short_description = 'Ordered recently?'

    def get_last_retail_prepayment(self):
        prepayments = RetailPrepayment.objects.filter(member=self.member).order_by('-id')
        return prepayments[0] if len(prepayments) > 0 else None

    def get_last_vod_prepayment(self, status=None):
        if status:
            vod_prepayments = VODPrepayment.objects.filter(member=self.member, status=status).order_by('-id')
        else:
            vod_prepayments = VODPrepayment.objects.filter(member=self.member).order_by('-id')
        return vod_prepayments[0] if len(vod_prepayments) > 0 else None

    def get_has_pending_update(self):
        return ContentUpdate.objects.filter(status=ContentUpdate.PENDING, member=self.member).count()

    def get_last_update(self):
        from sales.models import ContentUpdate
        updates = ContentUpdate.objects.filter(member=self.member).order_by('-id')
        return updates[0] if len(updates) > 0 else None

    def get_can_access_adult_content(self):
        if not self.is_vod_operator:
            last_vod_prepayment = self.get_last_vod_prepayment(VODPrepayment.CONFIRMED)
            return self.adult_authorized and last_vod_prepayment.adult_authorized
        return True

    def to_dict(self):
        can_access_adult_content = self.get_can_access_adult_content()
        var = to_dict(self)
        var['can_access_adult_content'] = can_access_adult_content
        del(var['member'])
        return var
