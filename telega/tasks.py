# -*- coding: utf8 -*-
from random import randint
from datetime import datetime, timedelta

import pytz

import telega.schedule as schedule
import telega.classifier as classifier
from telega.common import DbManager, config

db = TaskDbManager()


class TaskDbManager(DbManager):
    def remove_old_tasks(self):
        with self.db.cursor() as cursor:
            cursor.execute("""
                    DELETE FROM Tasks
                    WHERE time < (UTC_TIMESTAMP() - INTERVAL %s HOUR)
                """, config['task_expire_hours'])

    def get_next_task(self):
        with self.db.cursor() as cursor:
            cursor.execute("""
                    SELECT *
                    FROM Tasks
                    ORDER BY time ASC
                    LIMIT 1
                """)
            result = cursor.fetchone()
        result['processor'] = globals().get(result['processor'])
        return result

    def get_last_task_time(self, type):
        with self.db.cursor() as cursor:
            cursor.execute("""
                    SELECT MAX(time) AS time
                    FROM Tasks
                    WHERE processor = %s
                """, type)
            return cursor.fetchone()['time']

    def add_task(self, type, time, target):
        self.insert('Tasks', {
            'processor': type,
            'time': time.isoformat(),
            'target_id': target,
        })

    def add_end_time(self, begin, channel):
        with self.db.cursor() as cursor:
            cursor.execute("""
                    UPDATE Events
                    SET end = %s
                    WHERE channel_id = %s
                      AND begin <= %s
                      AND (end > %s OR end = NULL)
                """, (begin, channel, begin, begin))
            cursor.execute("""
                    SELECT MIN(time) AS time
                    FROM Events
                    WHERE channel_id = %s
                      AND begin > %s
                """, (channel, begin))
            return cursor.fetchone()['time']

    def update_channel_date(self, channel, date):
        with self.db.cursor() as cursor:
            cursor.execute("""
                    UPDATE Channels
                    SET known_until = %s
                    WHERE channel_id = %s
                """, (date, channel))


class Task(object):
    delay = (0, 0)
    target_table = None

    @classmethod
    def add_task(cls, target=None, later_than=None):
        last_task_time = db.get_last_task_time(cls.__name__)
        if last_task_time:
            last_task_time += timedelta(
                seconds=randint(cls.delay[0], cls.delay[1])
            )
        new_task_time = max(
            later_than.replace(tzinfo=None),
            last_task_time,
            datetime.utcnow(),
        )
        db.add_task(cls.__name__, new_task_time, target)

    @classmethod
    def prepare_target(cls, target):
        if not cls.target_table:
            return True
        if not target:
            return None
        return db.select(cls.target_table, target)

    @classmethod
    def run_task(cls, target):
        raise NotImplementedError


class GetEventInfoTask(Task):
    delay = (5, 10)
    target_table = 'Events'

    @classmethod
    def run_task(cls, event):
        info = schedule.get_event_info(event['link'])
        info['event_id'] = event['id']
        info['id'] = db.insert('EventInfo', info)
        classifier.check_heuristics(info)


class GetEventsTask(Task):
    delay = (360, 600)
    target_table = 'Channels'

    @classmethod
    def run_task(cls, channel):
        for_date = datetime.now().date()
        if channel['known_until'] >= for_date:
            for_date += timedelta(days=1)
            if channel['known_until'] >= for_date:
                return
        for event in schedule.get_events(channel['link'], for_date):
            event['channel_id'] = channel['id']
            event['end'] = db.add_end_time(event['begin'], channel['id']) or
            event['id'] = db.insert('Events', event)
            classifier.check_filters(event)
            GetEventInfoTask.add_task(event['id'])
        db.update_channel_date(channel['id'], for_date)


class GetScheduleTask(Task):
    @classmethod
    def run_task(cls, target):
        for ch in db.select_all('Channels'):
            GetEventsTask.add_task(ch['id'])
        now = datetime.now(tz=pytz.timezone("Europe/Moscow"))
        local_next_midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        GetScheduleTask.add_task(
            later_than=local_next_midnight.astimezone(pytz.utc)
        )
