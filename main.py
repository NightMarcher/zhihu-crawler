# main.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import json, logging
from hashlib import md5

from utils.mongo import Mongo
from utils.toolkit import logging_init, redis_init
from crawling.crawler import Crawler

logging_init()
logger = logging.getLogger(__name__)


TOPIC_FIELD_TABLE = {
        'topic_id': {'hash_type': 'key'},
        'name': {'hash_type': 'to_hash'},
        'follower_num': {'hash_type': 'to_hash'},
        'question_num': {'hash_type': 'to_hash'},
        'children_topic_ids': {'hash_type': 'to_hash'},
        'parent_topic_ids': {'hash_type': 'to_hash'},
        'hash_digest': {'hash_type': 'value'},
        'last_updated': {'hash_type': None},
        # '': {'hash_type': ''},
        }


def sync_redis_with_mongo(redis, mongo):
    filtered = filter(lambda field: TOPIC_FIELD_TABLE[field]['hash_type'] is not None, [*TOPIC_FIELD_TABLE])
    cursor = mongo.find(col='topics', fields=[*filtered])
    existsed_topics = [*cursor]
    if not existsed_topics:
        logger.info('No topic found in MongoDB!')
        return
    redis.hmset('topics', {topic['topic_id']: topic['hash_digest'] for topic in existsed_topics})
    logger.info('Redis sync with MongoDB succeed!')


def get_all_topics(crawler):
    home_topics = crawler.get_home_topics() or []
    logger.info(f'{len(home_topics)} home topics were found.')
    all_topics = []
    for ht in home_topics:
        topics = crawler.get_topics_by_home_topic(ht) or []
        logger.info(f'{len(topics)} topics were found under home topic {ht}.')
        all_topics.extend(topics)
        break # for debug
    return all_topics


def get_need_update_topics_iter(redis, topics):
    filtered = filter(lambda field: TOPIC_FIELD_TABLE[field]['hash_type'] == 'to_hash', [*TOPIC_FIELD_TABLE])
    to_hash_fields = [*filtered]
    def _calc_hash_by_fileds(topic_dict):
        to_hash_dict = {key: value for key, value in topic_dict.items() if key in to_hash_fields}
        to_hash_str = json.dumps(to_hash_dict, ensure_ascii=False, sort_keys=True)
        hash_str = md5(to_hash_str.encode()).hexdigest()
        topic_dict['hash_digest'] = hash_str
    map(_calc_hash_by_fileds, topics)
    topics_id_hash_dict = redis.hgetall('topics')
    return filter(lambda topic: topic['hash_digest'] != topics_id_hash_dict.get(topic['topic_id']), topics)


def update_redis_and_mongo_to_lasted(need_update_topics_iter, redis, mongo):
    for topic in need_update_topics_iter:
        redis.hset('tpoics', topic['topic_id'], topic['hash_digest'])
        mongo.update_one(
                col='topics',
                query={'topic_id': topic['topic_id']},
                data=topic,
                )
    logger.info('Update redis and mongo to the lasted!')


def main():
    redis = redis_init()
    mongo = Mongo()
    sync_redis_with_mongo(redis, mongo)
    crawler = Crawler()
    topics = get_all_topics(crawler)
    need_update_topics_iter = get_need_update_topics_iter(redis, topics)
    update_redis_and_mongo_to_lasted(need_update_topics_iter, redis, mongo)

if __name__ == '__main__':
    main()

