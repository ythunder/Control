#!/usr/bin/env python
# coding=utf-8

import redis
import MySQLdb

client =redis.Redis(host='127.0.0.1',port=6379,db=0)
db = MySQLdb.connect("http://m56o8yzw.586.dnstoo.com",
                     "xiyoulinux_f","xiyoulinux","xiyoulinux" )

# 设置name值
# 有效值 api_id, api_name, version
# 例如查找 name="yun" 的 api_id 和 version
# 数据库中存储 key:yun_id  value:api_id
#             key:yun_version  value:version
def setCheckName(api_id, api_name, version):
    key_id = str(api_name) + "_id"
    key_version = str(api_name) + "_version"
    client.hset(name="check_name", key=key_id, value=api_id)
    client.hset(name="check_name", key=key_version, value=version)
    return True


# 获取id，version对应的值
def getCheckName(api_name):
    key_id = str(api_name) + "_id"
    key_version = str(api_name) + "_version"
    value_id = client.hget(name="check_name",key=key_id)
    value_version = client.hget(name="check_name", key=key_version)
    return value_id,value_version


#设置check_url
#有效数据 api_id, version, url, type
def setCheckUrl(api_id, version, url, type):
    key_url = str(api_id) + "_" + str(version) + "_url"
    key_type = str(api_id) + "_" + str(version) + "_type"
    client.hset(name="check_url", key=key_url, value=url)
    client.hset(name="check_url", key=key_type, value=type)
    return True


#获取url，type值
def getCheckUrl(api_id, version):
    key_url = str(api_id) + "_" + str(version) + "_url"
    key_type = str(api_id) + "_" + str(version) + "_type"
    value_url = client.hget(name="check_url", key=key_url)
    value_type = client.hget(name="check_url", key=key_type)
    return value_url,value_type


#设置check_match
def setCheckMatch(api_id, version, match):
    key_match = str(api_id) + "_" + str(version) + "_match"
    client.hset(name="check_match", key=key_match, value=match)
    return True


# 获取 match值
def getCheckMatch(api_id, version):
    key_match = str(api_id) + "_" + str(version) + "_match"
    value_match = client.hget(name="check_match", key=key_match)
    return value_match


# 设置check_token的值
def setCheckToken(token, app_id, usr_id, time):
    key_appid =str(token) + "_appid"
    key_usrid = str(token) + "_usrid"
    key_time = str(token) + "_time"
    client.set(name=key_appid, value=app_id, ex=time)
    client.set(name=key_usrid, value=usr_id, ex=time)
    return True

# 获取check_token值
def getCheckToken(token):
    key_appid = str(token) + "_appid"
    key_usrid = str(token) + "_usrid"
    value_appid = client.get(name=key_appid)
    value_usrid = client.hget(name=key_usrid)
    return value_appid,value_usrid


# 获取数据库查询
def getTokenInfo(token):
    cursor = db.cursor()
    # 使用execute方法执行SQL语句

    sql_res = '''
                SELECT
                    oauth_sessions.client_id AS app_id,
                    oauth_sessions.owner_id AS user_id,
                    oauth_access_tokens.expire_time AS expire_time
                FROM
                   oauth_sessions
                INNER JOIN oauth_access_tokens ON oauth_access_tokens.session_id = oauth_sessions.id
                WHERE
                  oauth_access_tokens.id =  
                # + str(token)
                '04078pEXPddAa2NzDe0yi5nIA0xl9KApb8YoIGdB' '''

    cursor.execute(sql_res)

    # 使用 fetchone() 方法获取一条数据
    data = cursor.fetchone()
    if data:
        setCheckToken()
        db.close()
        return data[0],data[1],data[2]
    else:
        return False


