#!/usr/bin/env python
import os
from distutils.core import setup

def add_to_lib(dir):
    path = '/var/lib/telega/{}'.format(dir)
    files = ['{}/{}'.format(dir, file) for file in os.listdir(dir)]
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
        ('/etc/init', ['etc/init/telega-worker.conf']),
        ('/etc', ['etc/telega.conf']),
        add_to_lib('templates'),
        add_to_lib('static'),
    ],
)
