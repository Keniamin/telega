# -*- coding: utf8 -*-
import logging

from telega.common import DbManager


class FiltersDbManager(DbManager):
    def reset_event_state(self, event, filter=None, heuristic=None):
        assert (filter is None) or (heuristic is None)
        if filter is not None:
            state = 'filter'
        elif heuristic is not None:
            state = 'heuristic'
        else:
            state = None
        with self.cursor() as cursor:
            cursor.execute("""
                    UPDATE Events
                    SET state = %s,
                        filter_id = %s,
                        heuristic_id = %s
                    WHERE id = %s
                """, (state, filter, heuristic, event))


def check_filters(event, filters=None):
    if event.get('state') == 'filter':
        return True
    if filters is None:
        filters = db.select_all('Filters')
    for filter in filters:
        if _normalize(filter['title']) in _normalize(event['title']):
            db.reset_event_state(event['id'], filter=filter['id'])
            return True
    return False

def check_heuristics(info, event=None, heuristics=None):
    if event is None:
        event = info
    if event.get('state') == 'filter':
        return False
    if event.get('state') == 'heuristic':
        return True
    if heuristics is None:
        heuristics = db.select_all('Heuristics')
    for heuristic in heuristics:
        if _match_heuristic(info, heuristic):
            db.reset_event_state(event['id'], heuristic=heuristic['id'])
            return True
    return False

def clear_state(event):
    db.reset_event_state(event['id'])

def _normalize(text):
    # Текст на русском для нормального определения кодировки
    return text.lower().replace(u'ё', u'е')

def _match_heuristic(info, heuristic):
    try:
        if (
            heuristic['type'] and
            (_normalize(heuristic['type']) not in _normalize(info['type']))
        ):
            return False
        if (
            heuristic['genre'] and
            (_normalize(heuristic['genre']) not in _normalize(info['genre']))
        ):
            return False
        if (
            heuristic['country'] and
            (_normalize(heuristic['country']) not in _normalize(info['country']))
        ):
            return False
        if heuristic['year']:
            h_beg, h_end = (heuristic['year'] + '-').split('-')[:2]
            if not h_end:
                h_end = h_beg
            i_beg, i_end = (info['year'] + '-').split('-')[:2]
            if not i_beg:
                i_beg = '0'
            if not i_end:
                i_end = i_beg
            if (int(i_end) < int(h_beg)) or (int(i_beg) > int(h_end)):
                return False
        return True
    except Exception as exc:
        logging.warning(
            'Exception checking id %s by heuristic %s: %s',
            info['id'], heuristic['id'], exc
        )
        return False

db = FiltersDbManager()
