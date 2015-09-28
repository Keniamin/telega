# -*- coding: utf8 -*-
import json
from datetime import datetime, timedelta

from fresco import Route, GET, POST, Response, context

from telega.common import DbManager, config
import telega.classifier as classifier


class ViewsDbManager(DbManager):
    def _query(self, query, args=None):
        with self.cursor() as cursor:
            cursor.execute(query, args)
            return cursor.fetchall()

    def _get_timed_events(self, begin, end, state):
        return self._query("""
            SELECT
                e.id,
                e.title,
                TIME_FORMAT(e.begin, '%%k:%%i') AS begin,
                TIME_FORMAT(e.end, '%%k:%%i') AS end,
                CONCAT(c.name, ' (', c.button, ')') AS channel,
                IFNULL(e.filter_id, e.heuristic_id) AS reason,
                CONCAT('event-', e.state) AS _class
            FROM
                Events AS e LEFT JOIN Channels AS c
                ON e.channel_id = c.id
            WHERE e.state = %s
              AND e.begin <= %s
              AND e.end > %s
            ORDER BY e.begin
        """, (state, end, begin))

    def get_current_events(self, state):
        begin = datetime.now()
        end = begin + timedelta(minutes=config['current_since_minutes'])
        return self._get_timed_events(begin, end, state)

    def get_today_events(self, state):
        now = datetime.now()
        day_change = now.replace(
            hour=config['day_change_hour'],
            minute=0, second=0, microsecond=0,
        )
        if day_change < now:
            begin = day_change
            end = begin + timedelta(days=1)
        else:
            end = day_change
            begin = end - timedelta(days=1)
        return self._get_timed_events(begin, end, state)

    def get_filters(self):
        return list(self.select_all('Filters'))

    def get_heuristics(self):
        return list(self.select_all('Heuristics'))

    def get_channels(self):
        return self._query("""
            SELECT id, name, button, link
            FROM Channels
            ORDER BY name
        """)

    def get_locking_events(self, state, id):
        return self._query("""
                SELECT *
                FROM Events
                WHERE state = %s
                  AND {}_id = %s
            """.format(state), (state, id))

    def get_events_with_info(self):
        return self.select_all("""
            Events AS e LEFT JOIN EventInfo AS ei
            ON ei.event_id = e.id
        """)


class ViewHelper(object):
    __routes__ = [
        Route('/', GET, 'get'),
        Route('/', POST, 'post'),
    ]

    @staticmethod
    def _post_to_table(table, data=None):
        if data is None:
            data = context.request.get_json()
        id = data.get('id')
        field = data.get('field')
        if not id or not field:
            return
        db.update(table, id, field, data.get('value'))

    @staticmethod
    def _unlock_classifier(state, id):
        for event in db.get_locking_events(state, id):
            classifier.clear_state(event)


class EventsViewHelper(ViewHelper):
    columns = [
        {'name': 'title', 'title': 'Название'},
        {'name': 'begin', 'title': 'Начало'},
        {'name': 'end', 'title': 'Окончание'},
        {'name': 'channel', 'title': 'Канал'},
        {'name': 'reason', 'title': 'Критерий'},
    ]

    def get(self):
        getter = getattr(db, self.events_getter)
        return Response.json(getter('filter') + getter('heuristic'))


class CurrentEventsView(EventsViewHelper):
    order = 10
    name = 'Текущие'
    link = 'current'
    events_getter = 'get_current_events'


class TodayEventsView(EventsViewHelper):
    order = 20
    name = 'Сегодня'
    link = 'today'
    events_getter = 'get_today_events'


class FiltersView(ViewHelper):
    order = 30
    name = 'Фильтры'
    link = 'filters'
    columns = [
        {'name': 'title', 'title': 'Название', 'editable': True},
    ]

    def get(self):
        return Response.json(db.get_filters())

    def post(self):
        data = context.request.get_json()
        id = data.get('id')
        if not id:
            return Response.bad_request()

        self._unlock_classifier('filter', id)
        self._post_to_table('Filters', data)
        filter = db.select('Filters', id)

        for event in db.select_all('Events'):
            classifier.check_filters(event, filters=(filter,))
        return Response('ok')


class HeuristicsView(ViewHelper):
    order = 40
    name = 'Эвристики'
    link = 'heuristics'
    columns = [
        {'name': 'type', 'title': 'Тип события', 'editable': True},
        {'name': 'genre', 'title': 'Жанр', 'editable': True},
        {'name': 'country', 'title': 'Страна', 'editable': True},
        {'name': 'year', 'title': 'Годы', 'editable': True, 'pattern': '(19[0-9][0-9]|20[0-9][0-9])(-(19[0-9][0-9]|20[0-9][0-9]))?', 'hint': 'год или интервал<br>года с 1900 по 2099'},
    ]

    def get(self):
        return Response.json(db.get_heuristics())

    def post(self):
        data = context.request.get_json()
        id = data.get('id')
        if not id:
            return Response.bad_request()

        self._unlock_classifier('heuristic', id)
        self._post_to_table('Heuristics', data)
        heuristic = db.select('Heuristics', id)

        for event in db.get_events_with_info():
            classifier.check_heuristics(event, heuristics=(heuristic,))
        return Response('ok')


class ChannelsView(ViewHelper):
    order = 50
    name = 'Каналы'
    link = 'channels'
    columns = [
        {'name': 'name', 'title': 'Название'},
        {'name': 'button', 'title': 'Канал', 'editable': True, 'pattern': '[0-9]+', 'hint': 'число'},
        {'name': 'link', 'title': 'Указатель', 'editable': True, 'pattern': '[-+a-z0-9._]+', 'hint': 'ссылка канала на s-tv.ru'},
    ]

    def get(self):
        return Response.json(db.get_channels())

    def post(self):
        self._post_to_table('Channels')
        return Response('ok')


db = ViewsDbManager()
