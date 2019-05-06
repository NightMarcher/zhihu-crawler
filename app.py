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


@app.route('/summary_pagination/', methods=['GET', 'POST'])
def summary_pagination():
    summary_type = request.args.get('summary_type')
    search_params = SUMMARY_ATTR_DICT[summary_type]['search_params']
    topic_summaries = [*mongo.find(col=summary_type + '_topics_summary', fields=search_params + ['summary_last_updated']).sort('summary_last_updated', pymongo.DESCENDING)]
    summary_dicts = [{
        'summary_title': ts['summary_last_updated'].strftime(SUMMARY_ATTR_DICT[summary_type]['summary_title_fmt']) + '话题总结',
        search_params[0]: ts[search_params[0]],
        search_params[1]: ts[search_params[1]],
        } for ts in topic_summaries
    ]
    page = request.args.get('page', 1, int)
    pagination = Pagination(summary_dicts, per_page=PER_PAGE, page=page)
    return render_template('pagination.html', summary_pagination=pagination, summary_type=summary_type, summary_pagination_title=SUMMARY_ATTR_DICT[summary_type]['key_word']+'话题总结')


@app.route('/summary/', methods=['GET', 'POST'])
def summary():
    summary_type = request.args['summary_type']
    query_dict = {sp: request.args[sp] for sp in SUMMARY_ATTR_DICT[summary_type]['search_params']}
    topic_summary_dict = mongo.find_one(col=summary_type + '_topics_summary', query=query_dict)
    logger.debug(f'### {topic_summary_dict}')
    summary_title = summary_type
    return render_template('summary.html', summary_type=summary_type, summary_title=summary_title)


if __name__ == '__main__':
    app.run()

