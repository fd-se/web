#!/usr/bin/python
# -*- coding:utf-8 -*-
import redis
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

redis0 = redis.StrictRedis(host='localhost', port=6379, db=0)
redis1 = redis.StrictRedis(host='localhost', port=6379, db=1)
redis2 = redis.StrictRedis(host='localhost', port=6379, db=2)
redis3 = redis.StrictRedis(host='localhost', port=6379, db=3)
