#!/usr/bin/env python
# coding=utf-8

from flask import Flask, render_template
from flask import abort, redirect, url_for
from flask import Flask
from flask.ext.cache import Cache
from flask import request
import model_redis as models
import http_proxy as proxy
import logging
from string import find
import socket
import urllib


app = Flask(__name__)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

# Redis配置部分
cache = Cache()
config = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': '127.0.0.1',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_REDIS_DB': 0,
    'CACHE_REDIS_PASSWORD': ''
}

def func():
    pass

@app.route("/")
def server():
    if request.headers:
        headers = request.headers
        # return render_template("headerInfo.html",res=headers)
        return "head is %s" % (headers)

# 解析请求，返回
def parseRequest(request):
    # if 'REMOTE_ADDR' in request.headers.environ:
    #     remote_addr = request.headers.environ['REMOTE_ADDR']
    # if 'PATH_INFO' in request.headers.environ:
    #     path_info = request.headers.environ["PATH_INFO"]
    # if 'SERVER_PROTOCOL' in request.headers.environ:
    #     version = request.headers.environ['SERVER_PROTOCOL']
    if 'QUERY_STRING' in request.headers.environ:
        api_name = request.headers.environ['QUERY_STRING']

    return api_name



@app.route("/linux")
def get():
    if request.headers:
        api_name = parseRequest(request)

        # 查询Check_Name表，获取该name对
        api_id,api_version = models.getCheckName(api_name=api_name)
        api_url,url_type = models.getCheckUrl(api_id=api_id, version=api_version)

        try:
            httpserver = proxy.Proxy(('', 9999))
            httpserver.serve_forever(api_url)
        except KeyboardInterrupt, e:
            logging.error("KeyboardInterrupt" + str(e))

    # 处理请求响应

    #return "%s" %(request.headers.environ)


# 数据库中查找数据时更新redis
tocken_test = '04078pEXPddAa2NzDe0yi5nIA0xl9KApb8YoIGdB'
@app.route("/mysql")
def getTokenInfo(tocken_test):
    app,usr = models.getTokenInfo(tocken_test)
    models.setCheckToken(token=tocken_test, app_id=app, usr_id=usr)
    return str(app)+str(usr)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)

