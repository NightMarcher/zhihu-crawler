# settings/constant.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import pytz


CHROME_DRIVER_PATH = 'crawling/chromedriver'
ZHIHU_URL = 'https://www.zhihu.com/'

LOCAL_TZ = pytz.timezone('Asia/Shanghai')

DATE_FORMAT = '%Y-%m-%d %a'
TIME_FORMAT = '%I:%M:%S %p'

WEEKLY_TOPICS_ANALYZING_INTERVAL = 1
MONTHLY_TOPICS_ANALYZING_INTERVAL = 2

PER_PAGE = 10

TOPIC_FIELD_TABLE = {
        'topic_id': {'hash_type': 'key', 'analyze_type': 'key', },
        'name': {'hash_type': 'to_hash', 'analyze_type': 'key', },
        'follower_num': {'hash_type': 'to_hash', 'analyze_type': 'data', },
        'question_num': {'hash_type': 'to_hash', 'analyze_type': 'data', },
        'children_topic_ids': {'hash_type': 'to_hash', 'analyze_type': 'data', },
        'parent_topic_ids': {'hash_type': 'to_hash', 'analyze_type': 'data', },
        'hash_digest': {'hash_type': 'value', 'analyze_type': None, },
        'last_upserted': {'hash_type': None, 'analyze_type': None, },
        # '': {'hash_type': '', 'analyze_type': '', },
        }

SUMMARY_ATTR_DICT = {
    'weekly': {'key_word': '周', 'summary_title_fmt': '%Y年第%W周', 'search_params': ['year', 'week']},
    'monthly': {'key_word': '月', 'summary_title_fmt': '%Y年第%m月', 'search_params': ['year', 'month']},
    }

