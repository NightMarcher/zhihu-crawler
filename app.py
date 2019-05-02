# app.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from datetime import datetime

from flask import Blueprint, Flask
from flask import request, session, render_template, url_for
from flask_apscheduler import APScheduler
from flask_bootstrap import Bootstrap
import pymongo

from settings.constant import PER_PAGE
from utils.mongo import mongo
from utils.toolkit import Pagination, redis_cli

app = Flask(__name__)
app.config.from_object('settings.flask_config.Basic')
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
bootstrap = Bootstrap(app)
logger = app.logger


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/weekly_pagination/', methods=['GET', 'POST'])
def weekly_pagination():
    weekly_topics_summary = [*mongo.find(col='weekly_topics_summary').sort('summary_last_updated', pymongo.DESCENDING)]
    messages = [f"{wts['summary_last_updated'].strftime('%Y年第%W周')} 话题总结" for wts in weekly_topics_summary]
    page = request.args.get('page', 1)
    try:
        page = int(page)
    except Exception as e:
        page = 1
    pagination = Pagination(messages, per_page=PER_PAGE, page=page)
    return render_template('pagination.html', pagination=pagination, summary_type='周话题总结')


@app.route('/monthly_pagination/', methods=['GET', 'POST'])
def monthly_pagination():
    monthly_topics_summary = [*mongo.find(col='monthly_topics_summary').sort('summary_last_updated', pymongo.DESCENDING)]
    messages = [f"{mts['summary_last_updated'].strftime('%Y年第%m月')} 话题总结" for mts in monthly_topics_summary]
    page = request.args.get('page', 1)
    try:
        page = int(page)
    except Exception as e:
        page = 1
    pagination = Pagination(messages, per_page=PER_PAGE, page=page)
    return render_template('pagination.html', pagination=pagination, summary_type='月话题总结')


if __name__ == '__main__':
    app.run()

