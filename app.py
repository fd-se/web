#!/usr/bin/python
# -*- coding:utf-8 -*-
from flask import Flask, jsonify, request, g
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import MEDIUMTEXT

import hashlib

from config import USER, PASSWORD, URL, PORT, DATABASE
from ext import redis

app = Flask(__name__)
auth = HTTPTokenAuth(scheme='Dangerousor')

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}:{}/{}'.format(USER, PASSWORD, URL, PORT, DATABASE)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)


class User(db.Model):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nickname = db.Column(db.String(32))
    username = db.Column(db.String(32), unique=True, index=True)
    password = db.Column(db.String(128))
    token = db.Column(db.String(128), index=True)
    bitmap = db.Column(MEDIUMTEXT)

    def __init__(self, nickname, name, pwd, token):
        self.nickname = nickname
        self.username = name
        self.password = pwd
        self.token = token
        self.id = None


@auth.verify_token
def verify_token(token):
    g.user = None
    if redis.exists(token):
        g.user = redis.get(token)
        return True
    return False


@app.route('/login', methods=['POST'])
def login():
    g.user = None
    username = request.form['username']
    password = hashlib.md5(request.form['password']).hexdigest()
    token = hashlib.md5(request.form['token']).hexdigest()
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({
            'success': False,
            'content': 'Unknown Username!',
            'bitmap': None
        })
    else:
        if user.password == password:
            redis.delete(user.token)
            # redis.expire(user.token, 2592000)
            redis.set(token, user.username)
            redis.expire(token, 2592000)
            g.user = username
            return jsonify({
                'success': True,
                'content': user.nickname,
                'bitmap': user.bitmap
            })
        else:
            return jsonify({
                'success': False,
                'content': 'Wrong Password!',
                'bitmap': None
            })


@app.route('/login_token', methods=['POST'])
def login_token():
    g.user = None
    token = hashlib.md5(request.form['token']).hexdigest()
    res = User.query.filter_by(token=token).first()
    if redis.exists(token):
        g.user = redis.get(token)
        redis.expire(token, 2592000)
        return jsonify({
            'success': True,
            'content': res.nickname,
            'bitmap': res.bitmap
        })
    return jsonify({
        'success': False,
        'content': None,
        'bitmap': None
    })


@app.route('/register', methods=['POST'])
def register():
    g.user = None
    nickname = request.form['nickname']
    username = request.form['username']
    password = hashlib.md5(request.form['password']).hexdigest()
    token = hashlib.md5(request.form['token']).hexdigest()
    if User.query.filter_by(username=username).first():
        return jsonify({
            'success': False,
            'content': 'Username Already Exists!'
        })
    user = User(nickname, username, password, token)
    db.session.add(user)
    db.session.commit()
    redis.set(token, username)
    redis.expire(token, 2592000)
    g.user = username
    return jsonify({
        'success': True,
        'content': nickname
    })


@app.route('/logout', methods=['POST'])
def logout():
    token = hashlib.md5(request.form['token']).hexdigest()
    redis.delete(token)
    g.user = None
    return jsonify({
        'success': True
    })


@app.route('/')
def index():
    return "Hello Android Web"


if __name__ == '__main__':
    app.run('0.0.0.0', 80)
