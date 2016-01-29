# -*- coding: utf-8 -*-
from django.utils import timezone
from datetime import datetime


def change_date_to_string(date_to_stringify):
    changed_date = '%02d/%02d/%d/%02d/%02d/%02d' % (
        date_to_stringify.year, date_to_stringify.month, date_to_stringify.day, date_to_stringify.hour,
        date_to_stringify.minute, date_to_stringify.second)
    return changed_date


def to_datetime(raw_string):
    tokens = raw_string.strip().split(' ')
    date_tokens = tokens[0].split('-')
    time_tokens = tokens[1].split(':') if len(tokens) > 1 else ['0', '0', '0']
    year = int(date_tokens[0])
    month = int(date_tokens[1])
    day = int(date_tokens[2])
    hour = int(time_tokens[0])
    minute = int(time_tokens[1])
    sec = int(time_tokens[2])
    return datetime(year, month, day, hour, minute, sec, tzinfo=timezone.get_current_timezone())
