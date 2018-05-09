#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2015/12/19

from __future__ import unicode_literals, absolute_import

import logging
import sys
import time
import traceback

from tornado import gen
from tornado.concurrent import is_future
from tornado.httputil import HTTPHeaders
from tornado.web import RequestHandler
from . proxy import BackendAPIHandler

logger = logging.getLogger(__name__)


class BaseHandler(RequestHandler):
    # _call_mapper = {
    #     _REQUEST: 'process_request',
    #     _RESPONSE: 'process_response',
    #     _FINISHED: 'process_finished',
    # }

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.client = None

    def write(self, chunk):
        super(BaseHandler, self).write(chunk)




    @gen.coroutine
    def _do_fetch(self, method, *args, **kwargs):
        proxy = BackendAPIHandler
        pass

    @gen.coroutine
    def get(self, *args, **kwargs):
        yield self._do_fetch('get', *args, **kwargs)

    @gen.coroutine
    def post(self, *args, **kwargs):
        yield self._do_fetch('post', *args, **kwargs)

    @gen.coroutine
    def options(self, *args, **kwargs):
        yield self._do_fetch('options', *args, **kwargs)

    @gen.coroutine
    def head(self, *args, **kwargs):
        yield self._do_fetch('head', *args, **kwargs)

    @gen.coroutine
    def put(self, *args, **kwargs):
        yield self._do_fetch('put', *args, **kwargs)

    @gen.coroutine
    def delete(self, *args, **kwargs):
        yield self._do_fetch('delete', *args, **kwargs)
