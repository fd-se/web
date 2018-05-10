#!/usr/bin/python
# -*- coding:utf-8 -*-
from flask import Flask, jsonify, request, g
from flask_httpauth import HTTPTokenAuth

app = Flask(__name__)
auth = HTTPTokenAuth(scheme='Dangerousor')

tokens = {
    "sfs": "test"
}


@auth.verify_token
def verify_token(token):
    g.user = None
    if token in tokens:
        g.user = tokens[token]
        return True
    return False


@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] == 'test@example.com' and request.form['password'] == 'helloworld':
        return jsonify({
            'success': True,
            'content': None
        })
    elif request.form['username'] == 'test@example.com':
        return jsonify({
            'success': False,
            'content': 'Wrong Password!'
        })
    else:
        return jsonify({
            'success': False,
            'content': 'Unknown Username!'
        })


@app.route('/login_token', methods=['POST'])
def login_token():
    g.user = None
    print request.form
    if request.form['token'] in tokens:
        g.user = tokens[request.form['token']]
        return jsonify({
            'success': True,
            'content': None
        })
    return jsonify({
        'success': False,
        'content': None
    })


@app.route('/')
def index():
    return "Hello Android Web"


if __name__ == '__main__':
    app.run('0.0.0.0', 80)
