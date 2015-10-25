# -*- coding: utf8 -*-
import yaml
import logging
from datetime import datetime

import pymysql

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(funcName)15s] %(levelname)-8s %(message)s')
config = yaml.load(open('/etc/telega.conf', 'r').read())


class InterruptTask(Exception): pass


class DbManager(object):
    def __init__(self):
        db_conf = config['db']
        self.db = pymysql.connect(
            db=db_conf['name'],
            user=db_conf['user'],
            password=db_conf['password'],
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8',
        )
        self.db.autocommit(True)

    def cursor(self):
        self.db.ping()
        return self.db.cursor()

    def insert(self, table, obj):
        with self.cursor() as cursor:
            request = """
                INSERT INTO {}({})
                VALUES ({})
            """.format(
                table, ','.join(obj.keys()), ','.join(['%s'] * len(obj))
            )
            cursor.execute(request, obj.values())
            return cursor.lastrowid

    def select(self, table, id):
        with self.cursor() as cursor:
            cursor.execute("""
                    SELECT *
                    FROM {}
                    WHERE id = %s
                """.format(table), id)
            return cursor.fetchone()

    def select_all(self, table, where=None):
        with self.cursor() as cursor:
            request = """
                SELECT *
                FROM """ + table;
            if where:
                request += ' WHERE ' + where
            cursor.execute(request)
            row = cursor.fetchone()
            while row is not None:
                yield row
                row = cursor.fetchone()

    def update(self, table, id, field, value):
        with self.cursor() as cursor:
            cursor.execute("""
                    UPDATE {}
                    SET {} = %s
                    WHERE id = %s
                """.format(table, field), (value, id))

    def remove(self, table, id):
        with self.cursor() as cursor:
            cursor.execute("""
                    DELETE FROM {}
                    WHERE id = %s
                """.format(table), id)
