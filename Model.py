#!/usr/bin/python
# -*- coding:utf-8 -*-
from app import db


class User(db.Model):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, index=True)
    password = db.Column(db.String(128))
    token = db.Column(db.String(128))

    def __init__(self, name, pwd, token):
        self.name = name
        self.pwd = pwd
        self.token = token
        self.id = None
