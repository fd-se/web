#!/usr/bin/python
# -*- coding:utf-8 -*-
import redis

redis0 = redis.StrictRedis(host='localhost', port=6379, db=0)
redis1 = redis.StrictRedis(host='localhost', port=6379, db=1)
