# analyzing/analyzer.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
from datetime import datetime
from operator import attrgetter, itemgetter

from settings.constant import TOPIC_FIELD_TABLE, TOPIC_SUMMARY_NUM
from utils.mongo import Mongo
from utils.toolkit import logging_init, redis_init, utc_2_local_datetime

logging_init()
logger = logging.getLogger(__name__)


def daily_analyze(mongo, basic_analyze_fields):
    all_topics = [*mongo.find(col='topics', fields=basic_analyze_fields)]
    all_topics.sort(key=itemgetter('question_num'), reverse=True)
    daily_question_num_summary = {t['name']: t['question_num'] for t in all_topics[:TOPIC_SUMMARY_NUM]}
    all_topics.sort(key=itemgetter('follower_num'), reverse=True)
    daily_follower_num_summary = {t['name']: t['follower_num'] for t in all_topics[:TOPIC_SUMMARY_NUM]}
    daily_id = datetime.utcnow().strftime('%Y%jD')
    daily_summary = mongo.find_one(col='daily_summary', filters={'daily_id': daily_id}, fields={})
    data = {
                'daily_id': daily_id,
                'daily_question_num_summary': daily_question_num_summary,
                'daily_follower_num_summary': daily_follower_num_summary,
                # '': ,
            }
    if daily_summary is None:
        mongo.update_one(col='daily_summary', query={'daily_id': daily_id}, data=data)
        logger.debug(f'daily_summary {daily_id} was inserted!')
    else:
        mongo.update_one(col='daily_summary', query={'_id': daily_summary['_id']}, data=data)
        logger.debug(f'daily_summary {daily_id} was updated!')


def weekly_analyze():
    weekly_id = datetime.utcnow().strftime('%Y%UW')


def monthly_analyze():
    monthly_id = datetime.utcnow().strftime('%Y%mM')


def analyze():
    mongo = Mongo()
    basic_analyze_fields = [field for field, attr in TOPIC_FIELD_TABLE.items() if attr['analyze_type'] is not None]
    daily_analyze(mongo, basic_analyze_fields)
    weekly_analyze()
    monthly_analyze()


if __name__ == '__main__':
    analyze()

