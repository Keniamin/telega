# -*- coding: utf8 -*-

import os
import yaml
import fcntl
import errno
import logging
from datetime import datetime

import pymysql

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FORMAT='%(asctime)s %(process)-6d [%(funcName)16.16s] %(levelname)-8s %(message)s'
DATE_FORMAT='%Y/%m/%d %H:%M:%S'


class InterruptTask(Exception):
    pass


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


def init_logging(filename):
    hnd = logging.TimedRotatingFileHandler(filename, when='W0', backupCount=4, utc=True)
    frm = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
    hnd.setFormatter(frm)
    log = logging.getRootLogger()
    log.setLevel(logging.INFO)
    log.addHandler(hnd)


def load_config(filename):
    with open(filename) as config_file:
        config = yaml.load(config_file.read())
    return config


def get_lock(name):
    filename = '.{}.lock'.format(name)
    try:
        fd = os.open(filename, os.O_CREAT)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except IOError as err:
        if err.errno in (errno.EACCES, errno.EAGAIN):
            return False
        raise


os.chdir(BASE_DIR)
config = load_config('telega.conf')
