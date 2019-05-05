# app.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from datetime import datetime

from flask import Blueprint, Flask
from flask import request, session, render_template, url_for
from flask_apscheduler import APScheduler
from flask_bootstrap import Bootstrap
import pymongo

from settings.constant import PER_PAGE, SUMMARY_ATTR_DICT
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


@app.route('/pagination/', methods=['GET', 'POST'])
def pagination():
    sub = request.args.get('sub')
    topics_summary = [*mongo.find(col=sub+'_topics_summary', fields=['summary_last_updated', 'summary_sub_url']).sort('summary_last_updated', pymongo.DESCENDING)]
    summary_dicts = [{
        'summary_title': ts['summary_last_updated'].strftime(SUMMARY_ATTR_DICT[sub]['summary_title_fmt']) + '话题总结',
        'summary_sub_url': ts['summary_sub_url'],
        } for ts in topics_summary
    ]
    page = request.args.get('page', 1, int)
    pagination = Pagination(summary_dicts, per_page=PER_PAGE, page=page)
    return render_template('pagination.html', pagination=pagination, pagination_title=SUMMARY_ATTR_DICT[sub]['key_word']+'话题总结')


@app.route('/summary/<sub_url>', methods=['GET', 'POST'])
def summary(sub_url):
    pass


if __name__ == '__main__':
    app.run()

