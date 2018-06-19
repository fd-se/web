#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import time
import sys

from flask import Flask, jsonify, request, g, send_from_directory
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import TEXT, DATETIME
from sqlalchemy.dialects.mysql import LONGTEXT

import hashlib

from config import USER, PASSWORD, URL, PORT, DATABASE, UPLOAD_PATH
from ext import redis0, redis2

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

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
    bitmap = db.Column(LONGTEXT)

    def __init__(self, nickname, name, pwd):
        self.nickname = nickname
        self.username = name
        self.password = pwd
        self.id = None


class Video(db.Model):

    __tablename__ = 'video'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32))
    video = db.Column(db.String(256), unique=True, index=True)
    title = db.Column(TEXT)
    location = db.Column(TEXT)
    time = db.Column(DATETIME)

    def __init__(self, username, video, title, location, time_):
        self.username = username
        self.video = video
        self.title = title
        self.location = location
        self.time = time_


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
            redis0.set(token, user.username)
            redis0.expire(token, 2592000)
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
    g.user = username
    return jsonify({
        'success': True,
        'content': nickname
    })


@app.route('/logout', methods=['POST'])
def logout():
    token = hashlib.md5(request.form['token']).hexdigest()
    redis0.delete(token)
    g.user = None
    return jsonify({
        'success': True
    })


@app.route('/change', methods=['POST'])
def change():
    nickname = request.form['nickname']
    bitmap = request.form['bitmap']
    password = hashlib.md5(request.form['password']).hexdigest()
    token = hashlib.md5(request.form['token']).hexdigest()
    username = redis0.get(token)
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


@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({'success': False, 'content': 'No file part'})
        file_ = request.files['file']
        # if user does not select file, browser also submit a empty part without filename
        if file_.filename == '':
            return jsonify({'success': False, 'content': 'No selected file'})
        else:
            try:
                file_dir = os.getcwd() + '/users'
                if not os.path.exists(file_dir):
                    os.makedirs(file_dir)
                temp = file_.filename.split('+title+')
                title = temp[0]
                temp = temp[1].split('+location+')
                location = temp[0]
                temp = temp[1].split('+token+')
                token = hashlib.md5(temp[0]).hexdigest()
                # filename = secure_filename(file.filename)
                # filename = origin_file_name
                now_time = time.strftime('%Y-%m-%d %X', time.localtime())
                h_path = hashlib.md5(file_.filename.split('.')[0]).hexdigest() + '.' + file_.filename.split('.')[1]
                save_path = os.path.join(file_dir, h_path)

                file_.save(save_path)
                username = redis0.get(token)
                video = Video(username, h_path, title, location, now_time)
                db.session.add(video)
                db.session.commit()
                return jsonify({'success': True, 'content': ''})
            except Exception as e:
                return jsonify({'success': False, 'content': 'Error occurred'})
    else:
        return jsonify({'success': False, 'content': 'Method not allowed'})


@app.route('/videoname/<mtoken>', methods=['GET'])
def videoname(mtoken):
    if not Video.query.filter_by(id=1).first():
        return jsonify({
            'content': None,
            'success': False
        })
    token = hashlib.md5(mtoken).hexdigest()
    username = redis0.get(token)
    if redis2.exist(username):
        num = redis2.get(username)
        redis2.incr(username)
        video = Video.query.filter_by(id=num).first()
        if not video:
            redis2.set(username, 2)
            video = Video.query.filter_by(id=1).first()
        return jsonify({
            'content': video.video,
            'success': True
        })
    redis2.set(username, 2)
    video = Video.query.filter_by(id=1).first()
    return jsonify({
        'content': video.video,
        'success': True
    })


@app.route('/videodetail/<filename>', methods=['GET'])
def videodetail(filename):
    video = Video.query.filter_by(video=filename).first()
    user = User.query.filter_by(username=video.username).first()
    return jsonify({
        'pic': user.bitmap,
        'author': user.nickname,
        'title': video.title,
        'place': video.location
    })


@app.route('/video/<filename>', methods=['GET'])
def video(filename):
    dic = os.getcwd() + '/user/'
    return send_from_directory(dic, filename, as_attachment=True)


@app.route('/')
def index():
    return "Hello Android Web"


if __name__ == '__main__':
    app.run('0.0.0.0', 80)
