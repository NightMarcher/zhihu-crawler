# analyzing/analyzer.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
from datetime import datetime
from operator import itemgetter

from pandas import DataFrame as DF

from settings.constant import DATE_FORMAT, MONTHLY_TOPICS_ANALYZING_INTERVAL, TOPIC_FIELD_TABLE, TOPIC_SUMMARY_NUM, WEEKLY_TOPICS_ANALYZING_INTERVAL
from utils.mongo import Mongo
from utils.toolkit import logging_init, redis_init, utc_2_local_datetime

logging_init()
logger = logging.getLogger(__name__)


class Analyzer:
    def __init__(self):
        self.mongo = Mongo()
        self.utcnow = datetime.utcnow()

    def take_daily_topics_snapshot(self):
        daily_analyze_fields = [field for field, attr in TOPIC_FIELD_TABLE.items() if attr['analyze_type'] is not None]
        topics = [*self.mongo.find(col='topics', fields=daily_analyze_fields)]
        question_num_summary = {t['name']: t['question_num'] for t in topics}
        follower_num_summary = {t['name']: t['follower_num'] for t in topics}
        topics_snapshot_id = self.utcnow.strftime('%Y%jD')
        data = {
                    'topics_snapshot_id': topics_snapshot_id,
                    'weekday': self.utcnow.strftime('%w'),
                    'monthday': self.utcnow.strftime('%d'),
                    'week': self.utcnow.strftime('%W'),
                    'month': self.utcnow.strftime('%m'),
                    'year': self.utcnow.strftime('%Y'),
                    'summary_last_updated': self.utcnow,
                    'question_num_summary': question_num_summary,
                    'follower_num_summary': follower_num_summary,
                    # '': ,
                }
        self.mongo.update_one(col='topics_snapshot', query={'topics_snapshot_id': topics_snapshot_id}, data=data)
        logger.debug(f'topics_snapshot {topics_snapshot_id} was upserted!')

    def _topics_analyzing(self, analyze_scale, query_dict):
        analyze_fields = ['question_num_summary', 'follower_num_summary', 'summary_last_updated']
        topic_summaries = [*self.mongo.find(col='topics_snapshot', query=query_dict, fields=analyze_fields)]
        # number of question
        question_num_df = DF.from_dict({ts['summary_last_updated'].strftime(DATE_FORMAT): ts['question_num_summary'] for ts in topic_summaries}).dropna()
        question_num_df['var'] = question_num_df.var(axis='columns')
        question_num_df.sort_values(by='var', ascending=False, inplace=True)
        logger.debug(question_num_df)
        # number of follower 
        follower_num_df = DF.from_dict({ts['summary_last_updated'].strftime(DATE_FORMAT): ts['follower_num_summary'] for ts in topic_summaries}).dropna()
        follower_num_df['var'] = follower_num_df.var(axis='columns')
        follower_num_df.sort_values(by='var', ascending=False, inplace=True)
        logger.debug(follower_num_df)
        # ratio of follower num to question num
        topic_summaries.sort(key=itemgetter('summary_last_updated'))
        topic_summaries[-1].pop('_id')
        topic_summaries[-1].pop('summary_last_updated')
        topic_follower_question_df = DF.from_dict(topic_summaries[-1])
        topic_follower_question_df['ratio'] = topic_follower_question_df['follower_num_summary'] / topic_follower_question_df['question_num_summary']
        topic_follower_question_df.sort_values(by='ratio', ascending=False, inplace=True)
        logger.debug(topic_follower_question_df)
        # summary url
        summary_url_field = analyze_scale + '_summary_url'
        summary_url_str = '&'.join(f'{tp[0]}={tp[1]}' for tp in sorted(query_dict.items(), key=itemgetter(0)))
        def df2dict_func(df, drop_column):
            df.drop(columns=drop_column, inplace=True)
            return df.to_dict(orient='index')
        data = {
                    summary_url_field: summary_url_str,
                    'summary_last_updated': self.utcnow,
                    'question_num_dict': df2dict_func(question_num_df[:TOPIC_SUMMARY_NUM], 'var'),
                    'follower_num_dict': df2dict_func(follower_num_df[:TOPIC_SUMMARY_NUM], 'var'),
                    'topic_follower_question_dict': df2dict_func(topic_follower_question_df[:TOPIC_SUMMARY_NUM], 'ratio'),
                    # '': ,
                }
        self.mongo.update_one(col=analyze_scale+'_topics_summary', query={summary_url_field: summary_url_str}, data=data)
        logger.debug(f'{analyze_scale}_topics_summary {summary_url_str} was upserted!')

    def analyze_weekly_topics(self):
        year, week, weekday =  self.utcnow.strftime('%Y %W %w').split()
        if int(weekday) not in range(0, 7, WEEKLY_TOPICS_ANALYZING_INTERVAL):
            return
        query_dict = {
                'year': year,
                'week': week,
                'weekday': weekday,
                }
        self._topics_analyzing('weekly', query_dict)

    def analyze_monthly_topics(self):
        year, month, monthday =  self.utcnow.strftime('%Y %m %d').split()
        if int(monthday) not in range(0, 28, MONTHLY_TOPICS_ANALYZING_INTERVAL):
            return
        query_dict = {
                'year': year,
                'month': month,
                'monthday': monthday,
                }
        self._topics_analyzing('monthly', query_dict)


if __name__ == '__main__':
    analyzer = Analyzer()
    analyzer.take_daily_topics_snapshot()
    analyzer.analyze_weekly_topics()
    analyzer.analyze_monthly_topics()

