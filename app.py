#!/usr/bin/python
# -*- coding:utf-8 -*-
from flask import Flask, jsonify, request, g
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import MEDIUMTEXT

import hashlib

from config import USER, PASSWORD, URL, PORT, DATABASE
from ext import redis0, redis1

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
    # token = db.Column(db.String(128), index=True)
    bitmap = db.Column(MEDIUMTEXT)

    def __init__(self, nickname, name, pwd):
        self.nickname = nickname
        self.username = name
        self.password = pwd
        self.id = None


@auth.verify_token
def verify_token(token):
    g.user = None
    if redis0.exists(token):
        g.user = redis0.get(token)
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
            # redis.delete(user.token)
            # redis.expire(user.token, 2592000)
            redis0.delete(redis1.get(user.username))
            redis0.set(token, user.username)
            redis0.expire(token, 2592000)
            redis1.set(user.username, token)
            redis1.expire(user.username, 2592000)
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
    # res = User.query.filter_by(token=token).first()
    if redis0.exists(token):
        res = User.query.filter_by(username=redis0.get(token)).first()
        print res
        g.user = redis0.get(token)
        redis0.expire(token, 2592000)
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
    user = User(nickname, username, password)
    db.session.add(user)
    db.session.commit()
    redis0.set(token, username)
    redis0.expire(token, 2592000)
    redis1.set(username, token)
    redis1.expire(username, 2592000)
    g.user = username
    return jsonify({
        'success': True,
        'content': nickname
    })


@app.route('/logout', methods=['POST'])
def logout():
    token = hashlib.md5(request.form['token']).hexdigest()
    redis1.delete(redis0.get(token))
    redis0.delete(token)
    g.user = None
    return jsonify({
        'success': True
    })


@app.route('/change', methods=['POST'])
def change():
    nickname = request.form['nickname']
    bitmap = request.form['bitmap']
    token = request.form['token']
    password = request.form['password']
    username = redis0.get(token)
    print username
    print bitmap
    print nickname
    print password
    if bitmap:
        User.query.filter_by(username=username).update({"bitmap": bitmap})
        db.session.commit()
        return jsonify({
            'success': True
        })
    if nickname:
        User.query.filter_by(username=username).update({'nickname': nickname})
        db.session.commit()
        return jsonify({
            'success': True
        })
    if password:
        User.query.filter_by(username=username).update({'password': password})
        db.session.commit()
        return jsonify({
            'success': True
        })


@app.route('/')
def index():
    return "Hello Android Web"


if __name__ == '__main__':
    app.run('0.0.0.0', 80)
