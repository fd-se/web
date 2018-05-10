#!/usr/bin/python
# -*- coding:utf-8 -*-
from flask import Flask, jsonify, request, g
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy

import hashlib

from config import USER, PASSWORD, URL, PORT, DATABASE
from Model import User
from ext import redis

app = Flask(__name__)
auth = HTTPTokenAuth(scheme='Dangerousor')

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}:{}/{}'.format(USER, PASSWORD, URL, PORT, DATABASE)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)


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
                'content': None
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
    if redis.exists(token):
        g.user = redis.get(token)
        redis.expire(token, 2592000)
        return jsonify({
            'success': True,
            'content': None
        })
    return jsonify({
        'success': False,
        'content': None
    })


@app.route('/register', methods=['POST'])
def register():
    g.user = None
    username = request.form['username']
    password = hashlib.md5(request.form['password']).hexdigest()
    token = hashlib.md5(request.form['token']).hexdigest()
    if User.query.filter(username=username):
        return jsonify({
            'success': False,
            'content': 'Username Already Exists!'
        })
    user = User(username, password, token)
    db.session.add(user)
    db.session.commit()
    redis.set(token, username)
    redis.expire(token, 2592000)
    g.user = username
    return jsonify({
        'success': True,
        'content': None
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
