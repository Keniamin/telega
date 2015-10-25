# -*- coding: utf8 -*-
import re
import json
from os import path
from datetime import datetime, timedelta

from fresco import Route, GET, POST, PUT, DELETE, Response, context

from telega.common import DbManager, config
from telega.tasks import GetEventsTask
import telega.classifier as classifier


class ViewsDbManager(DbManager):
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
            Events AS e JOIN EventInfo AS ei
            ON ei.event_id = e.id
        """)

    def _query(self, query, args=None):
        with self.cursor() as cursor:
            cursor.execute(query, args)
            return cursor.fetchall()

    def _get_timed_events(self, begin, end, state):
        def _add_events_fields(obj):
            obj['_link_target'] = '/{}s/?hl={}'.format(state, obj['reason'])
            obj['_class'] = 'event-' + state
            return obj

        return map(_add_events_fields, self._query("""
            SELECT
                e.id,
                e.title,
                TIME_FORMAT(e.begin, '%%k:%%i') AS begin,
                TIME_FORMAT(e.end, '%%k:%%i') AS end,
                CONCAT(c.name, ' (', c.button, ')') AS channel,
                IFNULL(e.filter_id, e.heuristic_id) AS reason
            FROM
                Events AS e LEFT JOIN Channels AS c
                ON e.channel_id = c.id
            WHERE e.state = %s
              AND e.begin <= %s
              AND e.end > %s
            ORDER BY e.begin
        """, (state, end, begin)))


class ViewHelper(object):
    __routes__ = [
        Route('/', GET, 'get'),
        Route('/', POST, 'post'),
        Route('/<id:int>', PUT, 'put'),
        Route('/<id:int>', DELETE, 'delete'),
    ]

    def get(self, *args, **kwargs): return Response.method_not_allowed([])
    def post(self, *args, **kwargs): return Response.method_not_allowed([])
    def put(self, *args, **kwargs): return Response.method_not_allowed([])
    def delete(self, *args, **kwargs): return Response.method_not_allowed([])

    @staticmethod
    def _update_table_field(table, id):
        data = context.request.get_json()
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
        {'name': 'begin', 'title': 'Начало', 'class': 'text-center'},
        {'name': 'end', 'title': 'Окончание', 'class': 'text-center'},
        {'name': 'channel', 'title': 'Канал', 'class': 'text-right'},
        {'name': 'reason', 'title': 'Критерий', 'class': 'text-center', 'link': True},
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
        id = db.insert('Filters', context.request.get_json())
        filter = db.select('Filters', id)

        for event in db.select_all('Events'):
            classifier.check_filters(event, filters=(filter,))
        return Response('ok')

    def put(self, id):
        self._unlock_classifier('filter', id)
        self._update_table_field('Filters', id)
        filter = db.select('Filters', id)

        for event in db.select_all('Events'):
            classifier.check_filters(event, filters=(filter,))
        return Response('ok')

    def delete(self, id):
        self._unlock_classifier('filter', id)
        db.remove('Filters', id)
        return Response('ok')


class HeuristicsView(ViewHelper):
    order = 40
    name = 'Эвристики'
    link = 'heuristics'
    columns = [
        {'name': 'type', 'title': 'Тип события', 'editable': True},
        {'name': 'genre', 'title': 'Жанр', 'editable': True},
        {'name': 'country', 'title': 'Страна', 'editable': True},
        {'name': 'year', 'title': 'Годы', 'class': 'text-right', 'editable': True, 'pattern': '(19[0-9][0-9]|20[0-9][0-9])(-(19[0-9][0-9]|20[0-9][0-9]))?', 'hint': 'год или интервал, года с 1900 по 2099'},
    ]

    def get(self):
        return Response.json(db.get_heuristics())

    def post(self):
        id = db.insert('Heuristics', context.request.get_json())
        heuristic = db.select('Heuristics', id)

        for event in db.get_events_with_info():
            classifier.check_heuristics(event, heuristics=(heuristic,))
        return Response('ok')

    def put(self, id):
        self._unlock_classifier('heuristic', id)
        self._update_table_field('Heuristics', id)
        heuristic = db.select('Heuristics', id)

        for event in db.get_events_with_info():
            classifier.check_heuristics(event, heuristics=(heuristic,))
        return Response('ok')

    def delete(self, id):
        self._unlock_classifier('heuristic', id)
        db.remove('Heuristics', id)
        return Response('ok')


class ChannelsView(ViewHelper):
    order = 50
    name = 'Каналы'
    link = 'channels'
    columns = [
        {'name': 'name', 'title': 'Название'},
        {'name': 'button', 'title': 'Канал', 'class': 'text-center', 'editable': True, 'pattern': '[0-9]+', 'hint': 'число'},
        {'name': 'link', 'title': 'Указатель', 'class': 'text-right', 'editable': True, 'pattern': '[-+a-z0-9&._]+', 'hint': 'ссылка канала на s-tv.ru'},
    ]

    def get(self):
        return Response.json(db.get_channels())

    def post(self):
        id = db.insert('Channels', context.request.get_json())
        GetEventsTask.add_task(id) ## today
        GetEventsTask.add_task(id) ## tomorrow
        return Response('ok')

    def put(self, id):
        self._update_table_field('Channels', id)
        return Response('ok')

    def delete(self, id):
        db.remove('Channels', id)
        return Response('ok')


class LogMonitoring(object):
    log_files = ['/var/log/telega/worker.log', '/var/log/telega/worker.log.1']
    time_file = '/var/lib/telega/.logmon.time'
    time_format = '%Y-%m-%d %H:%M:%S'
    re_logmsg = re.compile(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[[^\]]*\]\s+(\S+)\s'
    )
    __routes__ = [
        Route('/', GET, 'get'),
        Route('/', POST, 'post'),
    ]

    def get(self):
        found = 0
        last_known = None
        if path.isfile(self.time_file):
            with open(self.time_file) as tf:
                last_known = datetime.strptime(tf.read(), self.time_format)
        for log in self.log_files:
            if path.isfile(log):
                with open(log) as lf:
                    for line in lf:
                        match = self.re_logmsg.match(line)
                        if match and (
                            match.group(2) == 'WARNING' or
                            match.group(2) == 'ERROR'
                        ):
                            cur = datetime.strptime(match.group(1), self.time_format)
                            if last_known is None or cur > last_known:
                                found += 1
        return Response(str(found))

    def post(self):
        with open(self.time_file, 'w') as tf:
            tf.write(datetime.now().strftime(self.time_format))
        return Response('ok')


db = ViewsDbManager()
