#!/usr/bin/env python
import os
from subprocess import check_call
from distutils.core import setup


def add_to_lib(*dirs):
    path = os.path.join('.', *dirs)
    target = os.path.join('/var/lib/telega', *dirs)
    files = []
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            files.append(file_path)
    return (target, files)


print 'Compiling scss...'
check_call("""
        sass --scss --no-cache --sourcemap=none --style=compressed
            --force --stop-on-error --update static/scss/:static/css/
    """.strip().split())
print 'Changing right of css to 644...'
check_call('chmod 644 static/css/*', shell=True)

setup(
    name='telega',
    version='0.1',
    description='Television program schedule guide',

    author='Innokentii Goncharov',
    author_email='inngoncharov@yandex.ru',

    packages=['telega'],
    scripts=['bin/telega-worker', 'bin/telega-web'],
    data_files=[
        ('/etc/nginx/sites-enabled', ['etc/nginx/telega']),
        ('/etc/logrotate.d', ['etc/logrotate/telega']),
        ('/etc/init', [
            'etc/init/telega-worker.conf',
            'etc/init/telega-web.conf',
        ]),
        ('/etc', ['etc/telega.conf']),
        add_to_lib('templates'),
        add_to_lib('static', 'fonts'),
        add_to_lib('static', 'img'),
        add_to_lib('static', 'css'),
        add_to_lib('static', 'js'),
    ],
)
