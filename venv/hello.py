#!/usr/bin/env python
# coding=utf-8

from flask import Flask, render_template
from flask import abort, redirect, url_for
from flask import Flask
from flask.ext.cache import Cache
import redis
import model_redis as models

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


@app.route("/")
def server():
# 解析用户请求

    

@app.route("/get")
def get():
    id,ver = models.getCheckName(api_name="yulong")
    return id + ver


# 数据库中查找数据时更新redis
tocken_test = '04078pEXPddAa2NzDe0yi5nIA0xl9KApb8YoIGdB'
@app.route("/mysql")
def getTokenInfo(tocken_test):
    app,usr = models.getTokenInfo(tocken_test)
    models.setCheckToken(token=tocken_test, app_id=app, usr_id=usr)
    return str(q)+str(w)+str(e)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
