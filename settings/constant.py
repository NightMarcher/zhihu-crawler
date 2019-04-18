# settings/constant.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import pytz


LOCAL_TZ = pytz.timezone('Asia/Shanghai')

DATETIME_FORMAT = '%Y-%m-%d %a %I:%M:%S %p'

TOPIC_SUMMARY_NUM = 100

TOPIC_FIELD_TABLE = {
        'topic_id': {'hash_type': 'key', 'analyze_type': 'key', },
        'name': {'hash_type': 'to_hash', 'analyze_type': 'key', },
        'follower_num': {'hash_type': 'to_hash', 'analyze_type': 'data', },
        'question_num': {'hash_type': 'to_hash', 'analyze_type': 'data', },
        'children_topic_ids': {'hash_type': 'to_hash', 'analyze_type': 'data', },
        'parent_topic_ids': {'hash_type': 'to_hash', 'analyze_type': 'data', },
        'hash_digest': {'hash_type': 'value', 'analyze_type': None, },
        'last_updated': {'hash_type': None, 'analyze_type': None, },
        # '': {'hash_type': '', 'analyze_type': '', },
        }

