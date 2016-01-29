# -*- coding: utf-8 -*-

import json
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from cms.views import BaseView
from django.http.response import HttpResponseForbidden

from me.models import Profile
from sales.models import VODBundle, SalesConfig, VODPrepayment, Prepayment,\
    RetailPrepayment, RetailBundle


def offer_welcome_bundle(request, *args, **kwargs):
    sales_config = SalesConfig.objects.all()[0]
    if sales_config.free_trial:
        bytes_balance = sales_config.welcome_offer * 1000000
        VODPrepayment.objects.create(member=request.user, balance=bytes_balance, amount=0,
                                     duration=sales_config.welcome_offer_duration, status=Prepayment.CONFIRMED)


@login_required
def set_additional_session_info(request, *args, **kwargs):
    request.user.can_access_adult_content = request.user.profile.get_can_access_adult_content()
    request.user.has_pending_update = request.user.profile.get_has_pending_update()


@login_required
def create_member_profile(request, *args, **kwargs):
    member = request.user
    try:
        Profile.objects.get(member=member)
    except Profile.DoesNotExist:
        Profile.objects.create(member=member)


class History(BaseView):
    template_name = 'me/history.html'
    # TODO: Correct the display of history client side


@login_required
def choose_vod_bundle(request, *args, **kwargs):
    member = request.user
    bundle_id = request.GET.get('bundle_id')
    bundle = VODBundle.objects.get(pk=bundle_id)
    status = request.GET.get('status', Prepayment.PENDING)
    if status == Prepayment.CONFIRMED:
        # TODO: Add some logic here to verify that this bundle was actually paid
        pass
    last_vod_prepayment = member.profile.get_last_vod_prepayment()
    if last_vod_prepayment:
        try:
            welcome_offer = VODPrepayment.objects.get(member=member, paid_on__isnull=True, status=Prepayment.CONFIRMED)
            if last_vod_prepayment.status == Prepayment.PENDING and last_vod_prepayment != welcome_offer:
                last_vod_prepayment.delete()  # This VODPrepayment was never paid so wipe it out
                balance = bundle.volume + welcome_offer.balance
            else:
                balance = last_vod_prepayment.balance + bundle.volume
        except VODPrepayment.DoesNotExist:
            if last_vod_prepayment.status == Prepayment.PENDING:
                balance= 0
                last_vod_prepayment.delete()  # This VODPrepayment was never paid so wipe it out
            else:
                balance = last_vod_prepayment.balance + bundle.volume
    else:
        balance = bundle.volume
    VODPrepayment.objects.create(member=member, amount=bundle.cost, duration=bundle.duration,
                                 balance=balance, adult_authorized=bundle.adult_authorized, status=status)
    return HttpResponseRedirect(reverse('me:account_setup') + "?bundleChosen=yes")


@login_required
def choose_retail_bundle(request, *args, **kwargs):
    member = request.user
    if not member.profile.is_vod_operator:
        return HttpResponseForbidden("You are not allowed to order retail bundle.")
    bundle_id = request.GET.get('bundle_id')
    bundle = RetailBundle.objects.get(pk=bundle_id)
    status = request.GET.get('status', Prepayment.PENDING)
    if status == Prepayment.CONFIRMED:
        # TODO: Add some logic here to verify that this bundle was actually paid
        pass
    last_retail_prepayment = member.profile.get_last_retail_prepayment()
    if last_retail_prepayment:
        balance = last_retail_prepayment.balance + bundle.volume
    else:
        balance = bundle.volume
    RetailPrepayment.objects.create(member=member, amount=bundle.cost, duration=bundle.duration,
                                    balance=balance, adult_authorized=bundle.adult_authorized, status=status)
    return HttpResponseRedirect(reverse('movies:home') + "?bundleChosen=yes")


@login_required
def authorize_adult(request, *args, **kwargs):
    member = request.user
    member.profile.adult_authorized = True
    member.profile.save()
    return HttpResponse(
        json.dumps({'success': True}),
        content_type='application/json'
    )
