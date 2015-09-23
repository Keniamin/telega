#!/usr/bin/env python
import os
from distutils.core import setup

def add_to_lib(dir):
    path = os.path.join('/var/lib/telega', dir)
    files = [os.path.join(dir, file) for file in os.listdir(dir) if not file.startswith('@')]
    return (path, files)


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
        ('/etc/init', ['etc/init/telega-worker.conf']),
        ('/etc', ['etc/telega.conf']),
        add_to_lib('templates'),
        add_to_lib('static'),
    ],
)
