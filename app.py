# app.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from datetime import datetime, timedelta

from flask import Flask
from flask import request, session, render_template, url_for
from flask_apscheduler import APScheduler
from flask_bootstrap import Bootstrap
# from flask_sqlalchemy import SQLAlchemy

from utils.toolkit import logging_init

app = Flask(__name__)
app.config.from_object('settings.flask_config.Basic')
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
bootstrap = Bootstrap(app)
# db = SQLAlchemy(app)
logging_init()
logger = app.logger


# class Message(db.Model):
#     id = db.Column(db.Integer, primary_key=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/pagination', methods=['GET', 'POST'])
def test_pagination():
    db.drop_all()
    db.create_all()
    for i in range(100):
        m = Message()
        db.session.add(m)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    pagination = Message.query.paginate(page, per_page=10)
    messages = pagination.items
    return render_template('pagination.html', pagination=pagination, messages=messages)


if __name__ == '__main__':
    app.run()

