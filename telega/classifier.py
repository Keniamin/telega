# -*- coding: utf8 -*-
import logging

from telega.common import DbManager


class FiltersDbManager(DbManager):
    def select_active(self, table):
        return self.select_all(table, where='deleting IS NULL')

    def reset_event_state(self, event, filter=None, heuristic=None):
        assert (filter is None) or (heuristic is None)
        if filter is not None:
            state = 'filter'
        elif heuristic is not None:
            state = 'heuristic'
        else:
            state = None
        with self.db.cursor() as cursor:
            cursor.execute("""
                    UPDATE Events
                    SET state = %s,
                        filter_id = %s,
                        heuristic_id = %s
                    WHERE id = %s
                """, (state, filter, heuristic, event))


def _match_heuristic(info, heuristic):
    try:
        if (
            heuristic['type'] and
            (heuristic['type'].lower() not in info['type'].lower())
        ):
            return False
        if (
            heuristic['genre'] and
            (heuristic['genre'].lower() not in info['genre'].lower())
        ):
            return False
        if (
            heuristic['country'] and
            (heuristic['country'].lower() not in info['country'].lower())
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

def check_filters(event):
    if event.get('state') == 'filter':
        return True
    for filter in db.select_active('Filters'):
        if filter['title'].lower() in event['title'].lower():
            db.reset_event_state(event['id'], filter=filter['id'])
            return True
    return False

def check_heuristics(info, event=None):
    if event is None:
        event = info
    if event.get('state') == 'filter':
        return False
    if event.get('state') == 'heuristic':
        return True
    for heuristic in db.select_active('Heuristics'):
        if _match_heuristic(info, heuristic):
            db.reset_event_state(event['id'], heuristic=heuristic['id'])
            return True
    return False

def clear_state(event):
    db.reset_event_state(event['id'])

db = FiltersDbManager()
