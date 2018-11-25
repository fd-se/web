#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

USER = 'dangerousor'
PASSWORD = '123456'
# URL = 'localhost'
URL = '192.168.3.45'
PORT = '3306'
DATABASE = 'android'
UPLOAD_PATH = 'users'
