# -*- coding: utf8 -*-
import re
from datetime import datetime
from urllib2 import urlopen, Request

def _make_field_re(field):
    return re.compile(r'<p>.*?{}:(.*?)</p>'.format(field))

re_prg_item = re.compile(r'prg_item_time[^>]*>([^<]+)</span>\s*<a [^>]*href="#([^"]+)"[^>]*>(.+?)</a>')
re_event_type = re.compile(r'<p class="type">(.*?)</p>')
re_field_country = _make_field_re('Страна')
re_field_genre = _make_field_re('Жанр')
re_field_year = _make_field_re('Год')


def _make_request(url):
    try:
        request = Request(url, headers={
            'Accept': 'text/html, application/xhtml+xml',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
        })
        response = urlopen(request)
        assert response.getcode() >= 200 and response.getcode() < 300
    except Exception as e:
        return None
    return response

def _make_time(for_date, time_str):
    hour, minute = time_str.split('.')
    return datetime(
        year=for_date.year, month=for_date.month, day=for_date.day,
        hour=int(hour), minute=int(minute),
    )

def _clean_title(title):
    title = re.sub(r'<([a-z]+)\s+[^>]*>.*</\1>', '', title)
    title = re.sub(r'\[\d+\+\]', '', title)
    return title.strip()

def _search_for_field(info, re_field):
    found = re.search(re_field, info)
    if found is None:
        return ''
    return re.sub(r'</?[^>]+>', '', found.group(1)).strip()


def get_events(channel_link, for_date):
    url = 'http://www.s-tv.ru/tv/{}/{}/'.format(channel_link, for_date)
    response = _make_request(url)
    if response is None:
        return []

    events = []
    for event in re.finditer(re_prg_item, response.read()):
        events.append({
            'begin': _make_time(for_date, event.group(1)),
            'link': event.group(2),
            'title': _clean_title(event.group(3)),
        })
    return events

def get_event_info(event_link):
    url = 'http://www.s-tv.ru/tv/ajaxinfo/{}/0/'.format(event_link.replace('ab', ''))
    response = _make_request(url)
    if response is None:
        return {}

    info = response.read()
    return dict(
        type = re.search(re_event_type, info).group(1),
        genre = _search_for_field(info, re_field_genre),
        country = _search_for_field(info, re_field_country),
        year = _search_for_field(info, re_field_year),
    )
