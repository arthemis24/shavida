# -*- coding: utf-8 -*-
import json

from datetime import date

from Shavida.files_selector import collect_movies, collect_series
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.http.response import HttpResponseForbidden
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView
from ikwen.models import Member, Service
from movies.models import SeriesEpisode, Movie
from reporting.models import StreamLogEntry
from reporting.utils import sync_changes, generate_add_list_info, add_media_to_update
from sales.models import ContentUpdate
from sales.models import SalesConfig

__author__ = "Kom Sihon"


def get_history_data(request):
    updates = ContentUpdate.objects.filter(member=request.user).order_by('-id')
    response = [update.to_dict() for update in updates]
    return HttpResponse(json.dumps(response), 'content-type: text/json')


def get_filename(file_path):
    """
    Gets the filename only part of a file path
    get_filename('/home/root/Documents/somefile.avi') = 'somefile.avi'
    """
    idx = file_path.rfind('/') + 1
    return file_path[idx:]


def get_series_folder(filename):
    naked_filename = get_filename(filename)
    rel_folder = filename.replace(naked_filename, '')
    return rel_folder


def get_repo_setup_files(request, *args, **kwargs):
    if request.user.is_authenticated():
        provider_id = getattr(settings, 'PROVIDER_ID')
        provider = Member.objects.get(pk=provider_id)
        member = request.user
    else:
        username = request.GET.get('username')
        password = request.GET.get('password')
        provider = authenticate(username=username, password=password)
        if not provider:
            response = {'error': "Could not authenticate user %s with password." % username}
            return HttpResponse(json.dumps(response), 'content-type: text/json')

        operator_username = request.GET.get('operator_username')
        try:
            member = Member.objects.get(email=operator_username)
        except Member.DoesNotExist:
            response = {'error': "Member not found with username %s" % operator_username}
            return HttpResponse(json.dumps(response), 'content-type: text/json')

    movies_max_load = request.GET.get('movies_max_load')
    series_max_load = request.GET.get('series_max_load')
    unit = getattr('unit', 'SALES_UNIT', SalesConfig.DATA_VOLUME)
    base_categories_slugs = request.GET.get('base_categories_slugs')
    preferred_categories_slugs = request.GET.get('preferred_categories_slugs')
    base_categories_slugs = base_categories_slugs.split(',') if base_categories_slugs else []
    preferred_categories_slugs = preferred_categories_slugs.split(',') if base_categories_slugs else []
    movies_max_load = int(movies_max_load)
    series_max_load = int(series_max_load)
    media_selection = collect_movies(movies_max_load, unit, base_categories_slugs, preferred_categories_slugs)
    media_selection.extend(collect_series(series_max_load, unit))
    response = []
    add_list = []
    add_list_size = 0
    add_list_duration = 0
    for item in media_selection:
        add_list_size += item.size
        add_list_duration += item.duration
        filenames = item.filename.split(',')  # Some movies have filename in multiple parts separated by comma
        response.append(item.to_dict())
        for filename in filenames:
            filename = filename.strip()
            add_list.append(filename)
    update = ContentUpdate(member=member, status=ContentUpdate.DELIVERED, provider=provider,
                           add_list=','.join(add_list), add_list_size=add_list_size, add_list_duration=add_list_duration)
    update.movies_add_list = []
    update.series_episodes_add_list = []
    current_series = None
    for media in media_selection:
        if type(media).__name__ == "Movie":
            update.cost += media.price
            update.movies_add_list.append(media)
            media.orders += 1
            media.fake_orders += 1
            media.save()
        elif type(media).__name__ == "SeriesEpisode":
            if current_series != media.series:
                update.cost += media.price
                current_series = media.series
            update.series_episodes_add_list.append(media)
            media.orders += 1
            media.fake_orders += 1
            media.save()
    update.save()
    if not getattr(settings, 'UNIT_TESTING', False):
        # Copy the ContentUpdate object to the Operator database
        service_id = getattr(settings, 'IKWEN_SERVICE_ID')
        database = Service.objects.get(pk=service_id).database
        update.save(using=database)
    sync_changes(update)
    return HttpResponse(json.dumps(response), 'content-type: text/json')


def get_repo_files_update(request, *args, **kwargs):
    username = request.GET.get('username')
    password = request.GET.get('password')
    provider = authenticate(email=username, password=password)
    if not provider:
        response = {'error': "Could not authenticate user %s with password." % username}
        return HttpResponse(json.dumps(response), 'content-type: text/json')
    available_space = request.GET.get('available_space')
    operator_username = request.GET.get('operator_username')
    try:
        member = Member.objects.get(email=operator_username)
        service_id = getattr(settings, 'IKWEN_SERVICE_ID')
        database = Service.objects.get(pk=service_id).database
        update = ContentUpdate.objects.get(member=member, status=ContentUpdate.AUTHORIZED)
    except Member.DoesNotExist:
        response = {'error': "Member not found with username %s" % operator_username}
        return HttpResponse(json.dumps(response), 'content-type: text/json')
    except ContentUpdate.DoesNotExist:
        response = {'error': "No update placed by member with username %s" % operator_username}
        return HttpResponse(json.dumps(response), 'content-type: text/json')
    total_available_space = int(available_space) + update.delete_list_size
    if total_available_space < update.add_list_size:
        needed_space = update.add_list_size - total_available_space
        if needed_space >= 1000:
            needed_space_str = "%.2f GB" % (needed_space / 1000.0)
        else:
            needed_space_str = "%d MB" % needed_space
        response = {'error': "Insufficient space on drive to run this update, Need %s more." % needed_space_str}
        return HttpResponse(json.dumps(response), 'content-type: text/json')
    latest_prepayment = member.profile.get_last_retail_prepayment()
    latest_prepayment.balance -= update.add_list_size
    latest_prepayment.save()
    update.status = ContentUpdate.DELIVERED
    update.provider = provider
    update.save()
    if not getattr(settings, 'UNIT_TESTING', False):
        update.save(using=database)
    sync_changes(update)
    response = {
        'add_list': update.add_list.split(','),
        'delete_list': update.delete_list.split(',')
    }
    return HttpResponse(json.dumps(response), 'content-type: text/json')


@login_required
def debit_vod_balance(request, *args, **kwargs):
    referrer = request.META.get('HTTP_REFERER')
    if not referrer:
        return HttpResponseForbidden("You don't have permission to access this resource.")
    member = request.user
    last_vod_prepayment = member.profile.get_last_vod_prepayment()
    response = {'success': True}
    try:
        bytes = int(request.GET.get('bytes'))
        duration = int(request.GET.get('duration'))
        type = request.GET.get('type')
        media_id = request.GET.get('media_id')
        if bytes and bytes > 0:
            if bytes >= last_vod_prepayment.balance:
                last_vod_prepayment.balance = 0
                response['error'] = _("Sorry, you just ran out of balance. Please refill your account.")
            else:
                last_vod_prepayment.balance -= bytes
            StreamLogEntry.objects.create(member=member, media_type=type, media_id=media_id, duration=duration, bytes=bytes)
            last_vod_prepayment.save()
    finally:
        response['balance'] = last_vod_prepayment.balance
        return HttpResponse(json.dumps(response), 'content-type: text/json')


@login_required
def confirm_order(request, *args, **kwargs):
    member = request.user
    if not member.profile.is_vod_operator:
        return HttpResponse(json.dumps({'error': "Only VoD operators may order movies."}))
    last_prepayment = member.profile.get_last_retail_prepayment()
    items = request.GET.get('items')
    info = generate_add_list_info(items)
    sales_config = SalesConfig.objects.all()[0]
    add_list_size = info['add_list_size']
    add_list_duration = info['add_list_duration']
    if not last_prepayment:
        return HttpResponse(json.dumps({'error': _("You don't have any retail bundle. Contact your vendor.")}))
    if sales_config.unit == SalesConfig.BROADCASTING_TIME:
        if last_prepayment.balance < add_list_duration:
            return HttpResponse(json.dumps({'error': _("Your update bundle contains only %d hours." % (last_prepayment.balance / 60))}))
    else:
        if last_prepayment.balance < add_list_size:
            return HttpResponse(json.dumps({'error': _("Your update bundle contains only %.2f GB." % (last_prepayment.balance / 1000.0))}))
    try:
        update = ContentUpdate.objects.get(member=member, status=ContentUpdate.PENDING)
    except ContentUpdate.DoesNotExist:
        update = ContentUpdate.objects.create(member=member)
    add_media_to_update(items, update)
    update.add_list = (update.add_list + ',' + info['add_list']).strip(',')
    update.add_list_size += add_list_size
    update.save()
    if not getattr(settings, 'UNIT_TESTING', False):
        service_id = getattr(settings, 'IKWEN_SERVICE_ID')
        database = Service.objects.get(pk=service_id).database
        update.save(using=database)
    return HttpResponse(json.dumps({'success': True}))


@login_required
def cancel_order(request, *args, **kwargs):
    member = request.user
    last_update = member.profile.get_last_update()
    las_prepayment = member.profile.get_latest_prepayment()
    latest_trailer_offer = last_update.trailer_offer
    last_update.status = ContentUpdate.AUTHORIZED
    las_prepayment.balance += last_update.add_list_size
    last_update.save()
    las_prepayment.save()
    latest_trailer_offer.delete()
    response = {"success": True}
    return HttpResponse(json.dumps(response), 'content-type: text/json')


class ContentPublicationReport(TemplateView):
    template_name = 'reporting/content_publication_report.html'

    def get_context_data(self, **kwargs):
        context = super(ContentPublicationReport, self).get_context_data(**kwargs)
        csv_files_folder = self.request.GET.get('csv_files_folder')
        if not csv_files_folder:
            csv_files_folder = '/home/cinemax/listing'

        import os
        input_files = ['%s/%s' % (csv_files_folder, entry) for entry in os.listdir(csv_files_folder)]
        movies_filenames = set()
        series_filenames = set()
        for input_file in input_files:
            fh = open(input_file, 'r')
            lines = [line.split(';')[0].strip('"') for line in fh.readlines() if line.find('.trlr.') < 0]
            fh.close()
            current_file_movies = [filename.decode('cp1252') for filename in lines if filename.find('/') < 0]
            current_file_series = [filename.decode('cp1252') for filename in lines if filename.find('/') >= 0]
            movies_filenames = movies_filenames | set(current_file_movies)
            series_filenames = series_filenames | set(current_file_series)

        unpublished_movies, unimported_movies, unimported_series = [], [], set()

        for movie_filename in movies_filenames:
            try:
                Movie.objects.get(filename=movie_filename.encode('utf8'), visible=True)
            except ObjectDoesNotExist:
                try:
                    Movie.objects.get(filename=movie_filename.encode('utf8'))
                except ObjectDoesNotExist:
                    unimported_movies.append(movie_filename.encode('cp1252'))
                else:
                    unpublished_movies.append(movie_filename.encode('cp1252'))

        series_folders = set()
        for episode_filename in series_filenames:
            folder = get_series_folder(episode_filename.encode('cp1252'))
            series_folders.add(folder)
            try:
                SeriesEpisode.objects.get(filename=episode_filename.encode('utf8'))
            except ObjectDoesNotExist:
                unimported_series.add(folder)

        count_offline_movies = len(unimported_movies) + len(unpublished_movies)
        percent_offline_movies = "%.2f" % (count_offline_movies * 100.0 / len(movies_filenames))
        percent_unimported_movies = "%.2f" % (len(unimported_movies) * 100.0 / len(movies_filenames))
        percent_unpublished_movies = "%.2f" % (len(unpublished_movies) * 100.0 / len(movies_filenames))
        percent_unimported_series = "%.2f" % (len(unimported_series) * 100.0 / len(series_folders))

        context['count_movies'] = len(movies_filenames)
        context['count_series'] = len(series_folders)
        context['count_offline_movies'] = count_offline_movies
        unimported_movies.sort()
        unpublished_movies.sort()
        unimported_series = list(unimported_series)
        unimported_series.sort()
        context['unimported_movies'] = unimported_movies
        context['unpublished_movies'] = unpublished_movies
        context['unimported_series'] = unimported_series
        context['percent_offline_movies'] = percent_offline_movies
        context['percent_unimported_movies'] = percent_unimported_movies
        context['percent_unpublished_movies'] = percent_unpublished_movies
        context['percent_unimported_series'] = percent_unimported_series
        context['date'] = date.today()
        return context