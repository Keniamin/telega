# -*- coding: utf8 -*-
from fresco import Route, GET, POST, Response

import telega.common


class ChannelsView(object):
    name = 'Каналы'
    link = 'channels'
    columns = [
        {'name': 'name', 'title': 'Название', 'editable': False},
        {'name': 'button', 'title': 'Канал', 'editable': True},
        {'name': 'link', 'title': 'Указатель', 'editable': True},
    ]
    __routes__ = [
        Route('/', GET, 'get'),
        Route('/', POST, 'post'),
    ]

    def get(self):
        return Response.json(
            [
                {'id': 1, 'name': 'Nick', 'button': '12', 'link': 'ntv+15'}
            ]
        )

    def post(self):
        return Response('ok')
