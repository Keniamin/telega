import yaml

import pymysql

config = yaml.load(open('/etc/telega.conf', 'r').read())


class DbManager(object):
    def __init__(self):
        db_conf = config.get('db', {})
        self.db = pymysql.connect(
            db=db_conf['name'],
            user=db_conf['user'],
            password=db_conf['password'],
            cursorclass=pymysql.cursors.DictCursor,
        )
        self.db.autocommit(True)

    def insert(self, table, obj):
        with self.db.cursor() as cursor:
            request = """
                INSERT INTO {}({})
                VALUES ({})
            """.format(
                table, ','.join(obj.keys()), ','.join(['%s'] * len(obj))
            )
            cursor.execute(request, obj.values())
            return cursor.lastrowid

    def select(self, table, id):
        with self.db.cursor() as cursor:
            cursor.execute("""
                    SELECT *
                    FROM """ + table + """
                    WHERE id = %s
                """, id)
            return cursor.fetchone()

    def select_all(self, table):
        with self.db.cursor() as cursor:
            cursor.execute("""
                    SELECT *
                    FROM %s
                """, table)
            row = cursor.fetchone()
            while row is not None:
                yield row
                row = cursor.fetchone()

    def remove(self, table, id):
        with self.db.cursor() as cursor:
            cursor.execute("""
                    DELETE FROM %s
                    WHERE id = %s
                """, (table, id))
