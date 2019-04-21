# analyzing/analyzer.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
from datetime import datetime
from operator import itemgetter

from pandas import DataFrame as DF

from settings.constant import DAILY_TOPIC_SHOT_NUM, DATE_FORMAT, TOPIC_FIELD_TABLE, TOPIC_SUMMARY_NUM
from utils.mongo import Mongo
from utils.toolkit import logging_init, redis_init, utc_2_local_datetime

logging_init()
logger = logging.getLogger(__name__)


class Analyzer:
    def __init__(self):
        self.mongo = Mongo()
        self.utcnow = datetime.utcnow()

    def daily_topics_snapshot(self):
        utcnow = self.utcnow
        day_id = utcnow.strftime('%jD')
        weekday_id = utcnow.strftime('%wWD')
        monthday_id = utcnow.strftime('%dMD')
        week_id = utcnow.strftime('%WW')
        month_id = utcnow.strftime('%mM')
        year_id = utcnow.strftime('%YY')
        daily_analyze_fields = [field for field, attr in TOPIC_FIELD_TABLE.items() if attr['analyze_type'] is not None]
        topics = [*self.mongo.find(col='topics', fields=daily_analyze_fields)]
        topics.sort(key=itemgetter('question_num'), reverse=True)
        daily_question_num_summary = {t['name']: t['question_num'] for t in topics[:DAILY_TOPIC_SHOT_NUM]}
        topics.sort(key=itemgetter('follower_num'), reverse=True)
        daily_follower_num_summary = {t['name']: t['follower_num'] for t in topics[:DAILY_TOPIC_SHOT_NUM]}
        data = {
                    'day_id': day_id,
                    'weekday_id': weekday_id,
                    'monthday_id': monthday_id,
                    'week_id': week_id,
                    'month_id': month_id,
                    'year_id': year_id,
                    'summary_last_updated': utcnow,
                    'daily_question_num_summary': daily_question_num_summary,
                    'daily_follower_num_summary': daily_follower_num_summary,
                    # '': ,
                }
        self.mongo.update_one(col='daily_summary', query={'daily_id': daily_id}, data=data)
        logger.debug(f'daily_summary {daily_id} was upserted!')

    def analyze(self):
        weekly_analyze_fields = ['daily_question_num_summary', 'daily_follower_num_summary', 'summary_last_updated']
        weekly_summaries = [*self.mongo.find(col='daily_summary', query={'weekly_id': weekly_id}, fields=weekly_analyze_fields)]
        weekly_question_num_df = DF.from_dict({ws['summary_last_updated'].strftime(DATE_FORMAT): ws['daily_question_num_summary'] for ws in weekly_summaries}).dropna()
        weekly_question_num_df['var'] = weekly_question_num_df.var(axis='columns')
        weekly_question_num_df.sort_values(by='var', ascending=False, inplace=True)
        weekly_follower_num_df = DF.from_dict({ws['summary_last_updated'].strftime(DATE_FORMAT): ws['daily_follower_num_summary'] for ws in weekly_summaries}).dropna()
        weekly_follower_num_df['var'] = weekly_follower_num_df.var(axis='columns')
        weekly_follower_num_df.sort_values(by='var', ascending=False, inplace=True)
        data = {
                    'summary_last_updated': self.utcnow,
                    'weekly_question_num_df': weekly_question_num_df[:TOPIC_SUMMARY_NUM],
                    'weekly_follower_num_df': weekly_follower_num_df[:TOPIC_SUMMARY_NUM],
                    # '': ,
                }


if __name__ == '__main__':
    analyzer = Analyzer()
    analyzer.daily_topics_snapshot()
    # analyzer.analyze()

