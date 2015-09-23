# -*- coding: utf8 -*-
import re
import logging
from urllib2 import urlopen, Request
from datetime import datetime, timedelta

from telega.common import InterruptTask


def _make_field_re(field):
    return re.compile(ur'<p>.*?{}:(.*?)</p>'.format(field))

re_prg_item = re.compile(ur'prg_item_time[^>]*>([^<]+)</span>\s*<a\s[^>]*href="#([^"]+)"[^>]*>(.+?)</a>')
re_event_type = re.compile(ur'<p class="type">(.*?)</p>')
re_field_country = _make_field_re(u'Страна')
re_field_genre = _make_field_re(u'Жанр')
re_field_year = _make_field_re(u'Год')


def _make_request(url):
    try:
        request = Request(url, headers={
            'Accept': 'text/html, application/xhtml+xml',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
        })
        response = urlopen(request)
        assert response.getcode() >= 200 and response.getcode() < 300
        return response
    except Exception as exc:
        logging.warning('Can not load url %s: %s', url, exc)
        return None


def _make_time(time_str, for_date, prev_hour):
    hour, minute = map(int, time_str.split('.'))
    if hour < prev_hour:
        for_date += timedelta(days=1)
    return (
        datetime(
            year=for_date.year, month=for_date.month, day=for_date.day,
            hour=hour, minute=minute,
        ),
        for_date, hour
    )

def _clean_title(title):
    title = re.sub(ur'<([a-z]+)\s+[^>]*>.*</\1>', '', title)
    title = re.sub(ur'\[\d+\+\]', '', title)
    return title.strip()

def _search_for_field(info, re_field):
    found = re.search(re_field, info)
    if found is None:
        return ''
    return re.sub(ur'</?[^>]+>', '', found.group(1)).strip()


def get_events(channel_link, for_date):
    url = 'http://www.s-tv.ru/tv/{}/{}/'.format(channel_link, for_date)
    response = _make_request(url)
    if response is None:
        raise InterruptTask

    prev_hour = 0
    for event in re.finditer(re_prg_item, response.read().decode('utf8')):
        time, for_date, prev_hour = \
            _make_time(event.group(1), for_date, prev_hour)
        yield {
            'begin': time,
            'link': event.group(2),
            'title': _clean_title(event.group(3)),
        }

def get_event_info(event_link):
    event_link = event_link.replace('ab', '')
    url = 'http://www.s-tv.ru/tv/ajaxinfo/{}/0/'.format(event_link)
    response = _make_request(url)
    if response is None:
        raise InterruptTask

    info = response.read().decode('utf8')
    return dict(
        type = re.search(re_event_type, info).group(1),
        genre = _search_for_field(info, re_field_genre),
        country = _search_for_field(info, re_field_country),
        year = _search_for_field(info, re_field_year),
    )
