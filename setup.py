#!/usr/bin/env python
import os
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
        add_to_lib('static', 'img'),
        add_to_lib('static'),
    ],
)
