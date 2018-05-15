#!/usr/bin/python
# -*- coding:utf-8 -*-
from flask import Flask, jsonify, request, g
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy

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

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(32))
    username = db.Column(db.String(32), unique=True, index=True)
    password = db.Column(db.String(128))
    token = db.Column(db.String(128), index=True)

    def __init__(self, nickname, name, pwd, token):
        self.nickname = nickname
        self.name = name
        self.pwd = pwd
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
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({
            'success': False,
            'content': 'Unknown Username!'
        })
    else:
        if user.password == password:
            redis.set(user.token, user.username)
            redis.expire(user.token, 2592000)
            g.user = username
            return jsonify({
                'success': True,
                'content': user.nickname
            })
        else:
            return jsonify({
                'success': False,
                'content': 'Wrong Password!'
            })


@app.route('/login_token', methods=['POST'])
def login_token():
    g.user = None
    token = hashlib.md5(request.form['token']).hexdigest()
    nickname = User.query.filter_by(token=token).first().nickname
    if redis.exists(token):
        g.user = redis.get(token)
        redis.expire(token, 2592000)
        return jsonify({
            'success': True,
            'content': nickname
        })
    return jsonify({
        'success': False,
        'content': None
    })


@app.route('/register', methods=['POST'])
def register():
    g.user = None
    nickname = request.form['nickname']
    username = request.form['username']
    password = hashlib.md5(request.form['password']).hexdigest()
    token = hashlib.md5(request.form['token']).hexdigest()
    if User.query.filter(username=username):
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
