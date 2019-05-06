# analyzing/analyzer.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
from datetime import datetime
from operator import itemgetter

from pandas import DataFrame as DF

from settings.constant import DATE_FORMAT, MONTHLY_TOPICS_ANALYZING_INTERVAL, TOPIC_FIELD_TABLE, WEEKLY_TOPICS_ANALYZING_INTERVAL
from utils.mongo import mongo
from utils.toolkit import redis_cli

logger = logging.getLogger(__name__)


class Analyzer:
    def __init__(self):
        self.utcnow = datetime.utcnow()

    def take_daily_topics_snapshot(self):
        daily_analyze_fields = [field for field, attr in TOPIC_FIELD_TABLE.items() if attr['analyze_type'] is not None]
        topics = [*mongo.find(col='topics', fields=daily_analyze_fields)]
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
        mongo.update_one(col='topics_snapshot', query={'topics_snapshot_id': topics_snapshot_id}, data=data)
        logger.debug(f'topics_snapshot {topics_snapshot_id} was upserted!')

    def _topics_analyzing(self, summary_type, query_dict):
        analyze_fields = ['question_num_summary', 'follower_num_summary', 'summary_last_updated']
        topic_summaries = [*mongo.find(col='topics_snapshot', query=query_dict, fields=analyze_fields)]
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
        # update to mongo
        def df2dict_func(df, drop_column):
            df.drop(columns=drop_column, inplace=True)
            return df.to_dict(orient='index')
        data = {
                    'summary_last_updated': self.utcnow,
                    'question_num_dict': df2dict_func(question_num_df, 'var'),
                    'follower_num_dict': df2dict_func(follower_num_df, 'var'),
                    'topic_follower_question_dict': df2dict_func(topic_follower_question_df, 'ratio'),
                    # '': ,
                }
        data.update(query_dict)
        mongo.update_one(col=summary_type + '_topics_summary', query=query_dict, data=data)
        logger.debug(f'{summary_type}_topics_summary {query_dict} was upserted!')

    def analyze_weekly_topics(self):
        year, week, weekday =  self.utcnow.strftime('%Y %W %w').split()
        if int(weekday) not in range(0, 7, WEEKLY_TOPICS_ANALYZING_INTERVAL):
            return
        query_dict = {
                'year': year,
                'week': week,
                }
        self._topics_analyzing('weekly', query_dict)

    def analyze_monthly_topics(self):
        year, month, monthday =  self.utcnow.strftime('%Y %m %d').split()
        if int(monthday) not in range(0, 28, MONTHLY_TOPICS_ANALYZING_INTERVAL):
            return
        query_dict = {
                'year': year,
                'month': month,
                }
        self._topics_analyzing('monthly', query_dict)

analyzer = Analyzer()


def analyze():
    analyzer.take_daily_topics_snapshot()
    analyzer.analyze_weekly_topics()
    analyzer.analyze_monthly_topics()


if __name__ == '__main__':
    analyze()

