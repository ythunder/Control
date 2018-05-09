#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2015/12/19

from __future__ import unicode_literals, absolute_import

import logging
import traceback

from tornado import gen
from tornado.httpclient import HTTPRequest, HTTPError
from tornado.httputil import HTTPHeaders

# from .setting import ASYNC_HTTP_CONNECT_TIMEOUT, \
#     ASYNC_HTTP_REQUEST_TIMEOUT, HEADER_BACKEND_USER_JSON,
#     HEADER_X_PREFIX
#
# from ..utils import text_type
from tornado.httpclient import AsyncHTTPClient


logger = logging.getLogger(__name__)

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
    # HMAC 签名鉴定失败，禁止访问
    BAD_SIGN_REQUEST = 403

    # Signature 参数已过期
    EXPIRED_SIGNATURE = 430
    # Signature 参数不正确
    INVALID_SIGNATURE = 431

    # 没有访问权限
    NO_PERMISSION = 432

    # 该 Client 已被禁用
    DISABLED_CLIENT = 421
    # 该 Endpoint 已被禁用
    DISABLED_ENDPOINT = 422
    # AES 解密失败
    AES_DECRYPT_ERROR = 423

    # --------------------------------
    # 服务器处理发生异常
    INTERNAL_SERVER_ERROR = 500
    # 访问 endpoint server 出现错误, 服务不可用
    ENDPOINT_REQUEST_ERROR = 503
    # endpoint 返回的数据格式不正确
    BAD_ENDPOINT_RESPONSE = 502
    # client 缺少配置，或配置有误
    BAD_CLIENT_CONFIG = 510

    # AES 加密失败
    AES_ENCRYPT_ERROR = 523


class BackendAPIHandler(object):
    """
    处理代理请求
    """

    def __init__(self, handler, *args, **kwargs):
        self.post_data = {}
        self.handler = handler
        self.request = self.handler.request
        self.client = self.handler.client
        self.analytics = self.handler.analytics
        self.write = self.handler.write
        self.set_header = self.handler.set_header
        self.finish = self.handler.finish
        self.set_status = self.handler.set_status
        self.add_header = self.handler.add_header


    @gen.coroutine
    def get(self):
        yield self._do_fetch('GET')

    @gen.coroutine
    def post(self):
        yield self._do_fetch('POST')

    @gen.coroutine
    def head(self):
        yield self._do_fetch('HEAD')

    @gen.coroutine
    def options(self):
        yield self._do_fetch('OPTIONS')

    @gen.coroutine
    def put(self):
        yield self._do_fetch('PUT')

    @gen.coroutine
    def delete(self):
        yield self._do_fetch('DELETE')

    # def _clean_headers(self):
    #     """
    #     清理headers中不需要的部分，以及替换值
    #     :return:
    #     """
    #     headers = self.request.headers
    #     if HEADER_BACKEND_APP_ID in headers:
    #         del headers[HEADER_BACKEND_APP_ID]
    #
    #     # TODO 更新host字段为后端访问网站的host
    #     headers['host'] = '127.0.0.1:8899'
    #     # headers['Host'] = self.client.request.endpoint['netloc']
    #
    #     new_headers = HTTPHeaders()
    #     # 如果 header 有的是 str，有的是 unicode
    #     # 会出现 422 错误
    #     for name, value in headers.get_all():
    #         # 过滤 HEADERS_X_PREFIX 开头的, 这些只是发给 api-gateway
    #         # 但是以下这些 headers 是需要传递给后端
    #         required_headers = [
    #             HEADER_BACKEND_USER_JSON
    #         ]
    #         if name in required_headers:
    #             new_headers.add(text_type(name), text_type(value))
    #         elif name.startswith(HEADER_X_PREFIX):
    #             pass
    #         # 不需要提供 Content-Length, 自动计算
    #         # 如果 Content-Length 不正确, 请求后端网站会出错,
    #         # 太大会出现超时问题, 太小会出现内容被截断
    #         elif name == 'Content-Length':
    #             pass
    #         else:
    #             new_headers.add(text_type(name), text_type(value))
    #
    #     # 传递 app_id
    #     new_headers[HEADER_BACKEND_APP_ID] = self.client.app_id
    #
    #     return new_headers

    @gen.coroutine
    def _do_fetch(self, method):

        # forward_url = self.client.request.forward_url
        forward_url = "127.0.0.18899"

        # logger.debug('请求的后端网站 %s' % forward_url)
        # logger.debug('原始的 headers %s' % self.request.headers)
        # 清理和处理一下 header
        # headers = self._clean_headers()
        # logger.debug('修改后的 headers %s' % headers)

        try:
            if method == 'GET':
                body = None
            elif method == 'POST':
                body = self.request.body
            elif method in ['PUT']:
                body = self.request.body
            else:
                # method in ['GET', 'HEAD', 'OPTIONS', 'DELETE']
                # GET 方法 Body 必须为 None，否则会出现异常
                body = None

            config = self.client.config
            # # 设置超时时间
            # async_http_connect_timeout = config.get(
            #     'async_http_connect_timeout', ASYNC_HTTP_CONNECT_TIMEOUT)
            # async_http_request_timeout = config.get(
            #     'async_http_request_timeout', ASYNC_HTTP_REQUEST_TIMEOUT)

            response = yield AsyncHTTPClient().fetch(
                HTTPRequest(url=forward_url,
                            method=method,
                            body=body,
                            # headers=headers,
                            decompress_response=True,
                            # connect_timeout=async_http_connect_timeout,
                            # request_timeout=async_http_request_timeout,
                            follow_redirects=False))
            self._on_proxy(response)
        except HTTPError as x:
            if hasattr(x, 'response') and x.response:
                self._on_proxy(x.response)
            else:
                self.analytics.result_code = ResultCode.ENDPOINT_REQUEST_ERROR
                logger.error('proxy failed for %s, error: %s' % (forward_url, x))
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            self.analytics.result_code = ResultCode.ENDPOINT_REQUEST_ERROR

    def _on_proxy(self, response):
        forward_url = self.client.request.forward_url
        if response.error and not isinstance(
                response.error, HTTPError):
            self.analytics.result_code = ResultCode.ENDPOINT_REQUEST_ERROR
            logger.error('proxy failed for %s, error: %s' % (forward_url, response.error))
            return

        try:
            # 如果 response.code 是非w3c标准的，而是使用了自定义，就必须设置reason，
            # 否则会出现unknown status code的异常
            self.set_status(response.code, response.reason)
        except ValueError:
            self.set_status(response.code, 'Unknown Status Code')
            logger.warning('proxy %s encounters unknown status code,  %s' % (forward_url, response.code))

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
            # 如果 304 (Not Modified) 的话不能 write，因为在 finish() 中有检查
            # assert not self._write_buffer, "Cannot send body with 304"
            # 如果在 304 的时候仍然设置 body，有可能会导致客户端一直 pending 导致 502 bad gateway 错误
            self.write(response.body)

        logger.debug('proxy success for %s' % forward_url)
