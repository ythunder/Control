#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import signal
import tornado
import time
from tornado import httpserver, ioloop, web
from tornado.httputil import native_str
from tornado.web import RequestHandler
from tornado import gen

import logging
import traceback

from tornado import gen
from tornado.httpclient import HTTPRequest, HTTPError
from tornado.httputil import HTTPHeaders
from tornado.httpclient import AsyncHTTPClient

import model_redis as models

logger = logging.getLogger(__name__)

MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 1


class ResultCode(object):
    """
    响应结果的编码
    """
    # 成功
    OK = 200
    # 请求的参数不完整，或者格式不正确，例如缺少一些参数
    BAD_REQUEST = 400
    # 登录验证失败
    BAD_ACCESS_TOKEN = 401


    # 没有访问权限
    NO_PERMISSION = 432

    # 服务器处理发生异常
    INTERNAL_SERVER_ERROR = 500
    # 访问 endpoint server 出现错误, 服务不可用
    ENDPOINT_REQUEST_ERROR = 503
    # endpoint 返回的数据格式不正确
    BAD_ENDPOINT_RESPONSE = 502
    # client 缺少配置，或配置有误
    BAD_CLIENT_CONFIG = 510


class BackendAPIHandler(RequestHandler):
    """
    处理代理请求
    """

    def __init__(self, application, request, **kwargs):
        super(BackendAPIHandler, self).__init__(application, request, **kwargs)
        self.client = None
        self.post_data = {}
        self.request = request
        self.result_code = 0

        def write(self, chunk):
            super(BackendAPIHandler, self).write(chunk)

        # self.post_data = {}
        # self.handler = handler
        # self.request = self.handler.request
        # self.client = self.handler.client
        # self.analytics = self.handler.analytics
        # self.write = self.handler.write
        # self.set_header = self.handler.set_header
        # self.finish = self.handler.finish
        # self.set_status = self.handler.set_status
        # self.add_header = self.handler.add_header

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


    @gen.coroutine
    def _do_fetch(self, method):

        # 这里是从连接中截取api_name
        # api_name = self.request.host
        # api_name = api_name[0:api_name.find('.')]

        # 测试数据
        api_name = "monkey"

        # TODO 添加api_version指定情况
        api_id, api_version = models.getCheckName(api_name)
        api_url, api_type = models.getCheckUrl(api_id, api_version)
        forward_url = str(api_url)

        try:
            if method in ['GET']:
                body = None
            elif method in ['POST']:
                body = self.request.body
            elif method in ['PUT']:
                body = self.request.body
            else:
                body = None

            headers = HTTPHeaders()
            headers = self.request.headers
            headers['Host'] = forward_url

            req = tornado.httpclient.HTTPRequest(
                url=forward_url,
                headers = headers,
                method='GET',
                body = body,
                validate_cert=False)

            response = yield AsyncHTTPClient().fetch(req)

            #response = yield AsyncHTTPClient().fetch(forward_url)

            # response = yield AsyncHTTPClient().fetch(
            #     HTTPRequest(url=forward_url,
            #                 method=method,
            #                 body=body,
            #                 headers=headers,
            #                 decompress_response=True,
            #                 follow_redirects=False
            #                 ))

            self._on_proxy(response, forward_url)
        except HTTPError as x:
            if hasattr(x, 'response') and x.response:
                self._on_proxy(x.response)
            else:
                self.result_code = ResultCode.ENDPOINT_REQUEST_ERROR
                logger.error('proxy failed for %s, error: %s' % (forward_url, x))
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            self.result_code = ResultCode.ENDPOINT_REQUEST_ERROR

    def _on_proxy(self, response, forward_url):
        # forward_url = self.client.request.forward_url
        # if response.error and not isinstance(
        #         response.error, HTTPError):
        #     self.result_code = ResultCode.ENDPOINT_REQUEST_ERROR
        #     logger.error('proxy failed for %s, error: %s' % (forward_url, response.error))
        #     return
        #
        # try:
        #     self.set_status(response.code, response.reason)
        # except ValueError:
        #     self.set_status(response.code, 'Unknown Status Code')
        #     logger.warning('proxy %s encounters unknown status code,  %s' % (forward_url, response.code))

        # 这里要用 get_all 因为要按顺序
        # for (k, v) in response.headers.get_all():
        #     # 隐藏后端网站真实服务器名称
        #     if k == 'Server' or k == 'X-Powered-By':
        #         pass
        #     elif k == 'Transfer-Encoding' and v.lower() == 'chunked':
        #         # 如果设置了分块传输编码，但是实际上代理这边已经完整接收数据
        #         # 到了浏览器端会导致(failed)net::ERR_INVALID_CHUNKED_ENCODING
        #         pass
        #     elif k == 'Location':
        #         # API不存在301, 302跳转, 过滤Location
        #         pass
        #     elif k == 'Content-Length':
        #         # 代理传输过程如果采用了压缩，会导致remote传递过来的content-length与实际大小不符
        #         # 会导致后面self.write(response.body)出现错误
        #         # 可以不设置remote headers的content-length
        #         # "Tried to write more data than Content-Length")
        #         # HTTPOutputError: Tried to write more data than Content-Length
        #         pass
        #     elif k == 'Content-Encoding':
        #         # 采用什么编码传给请求的客户端是由Server所在的HTTP服务器处理的
        #         pass
        #     elif k == 'Set-Cookie':
        #         # Set-Cookie是可以有多个，需要一个个添加，不能覆盖掉旧的
        #         # 理论上不存在 Set-Cookie,可以过滤
        #         self.add_header(k, v)
        #     else:
        #         self.set_header(k, v)

        # logger.debug("local response headers: %s" % self.handler._headers)

        if response.code != 304:
            self.write(response.body)

        logger.debug('proxy success for %s' % forward_url)


class FaviconHandler(RequestHandler):
    def get(self):
        self.write('')

class RobotsHandler(RequestHandler):
    def get(self):
        self.set_header('Content-Type', 'text/plain')
        self.write('User-agent: *\nDisallow: /*')


class Application(web.Application):
    def __init__(self):
        tornado_settings = {
            'autoreload': True,
            'debug': True
        }

        handlers = [
            (r'/.*', BackendAPIHandler),
        ]

        super(Application, self).__init__(handlers, **tornado_settings)




def sig_handler(sig, frame):
    logger.warning('caught signal: %s', sig)
    tornado.ioloop.IOLoop.instance().add_callback(shutdown)


def shutdown():
    logger.info('stopping http server')
    server.stop()

    logger.info('will shutdown in %s seconds...', MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
    io_loop = tornado.ioloop.IOLoop.instance()

    deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN


    def stop_loop():
        now = time.time()
        if now < deadline and (io_loop._callbacks or io_loop._timeouts):
            io_loop.add_timeout(now + 1, stop_loop)
        else:
            io_loop.stop()
            logger.info('shutdown')

    stop_loop()


def main():

    global server
    app = Application()
    server = httpserver.HTTPServer(app, xheaders=True)
    server.listen(9999, '127.0.0.1')
    logger.info('fomalhaut is running on 127.0.0.1:9999')

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
