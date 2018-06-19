#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

USER = 'root'
PASSWORD = 'liuxiaofeng1974'
# URL = 'localhost'
URL = 'sh-cdb-byc5k8w5.sql.tencentcdb.com'
PORT = '63096'
DATABASE = 'android'
UPLOAD_PATH = 'users'
