# crawling/main.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import json, logging
from hashlib import md5
from multiprocessing.dummy import Pool as ThreadPool

from crawling.crawler import Crawler
from settings.constant import TOPIC_FIELD_TABLE
from utils.mongo import mongo
from utils.toolkit import redis_cli

logger = logging.getLogger(__name__)


def sync_redis_with_mongo():
    to_hash_fields = [field for field, attr in TOPIC_FIELD_TABLE.items() if attr['hash_type'] is not None]
    existed_topics = [*mongo.find(col='topics', fields=to_hash_fields)]
    if not existed_topics:
        logger.warning('No topic was found in MongoDB!')
        return None
    redis_cli.hmset('topics', {topic['topic_id']: topic['hash_digest'] for topic in existed_topics})
    logger.info('Redis sync with MongoDB succeed!')
    return True


def get_all_topics(crawler, thread_num):
    home_topics = crawler.get_home_topics() or []
    all_topic_dicts = []
    # Multi-thread crawling
    # pool = ThreadPool(processes=thread_num)
    # for tds in pool.map(crawler.get_topics_by_home_topic, home_topics):
    #     all_topic_dicts.extend(tds)
    # pool.close()
    # pool.join()
    # Ordinary crawling
    for ht in home_topics:
        topic_dicts = crawler.get_topics_by_home_topic(ht) or []
        all_topic_dicts.extend(topic_dicts)
        # break # for debug
    logger.info(f'{len(all_topic_dicts)} topics were found in total.')
    return all_topic_dicts


def get_need_update_topics(topics_id_hash_dict, batch_topic_dicts):
    to_hash_fields = [field for field, attr in TOPIC_FIELD_TABLE.items() if attr['hash_type'] == 'to_hash']
    def calc_hash_by_fileds(topic_dict):
        to_hash_dict = {key: value for key, value in topic_dict.items() if key in to_hash_fields}
        to_hash_str = json.dumps(to_hash_dict, ensure_ascii=False, sort_keys=True)
        topic_dict['hash_digest'] = md5(to_hash_str.encode()).hexdigest()
    [*map(calc_hash_by_fileds, batch_topic_dicts)]
    return [bt for bt in batch_topic_dicts if bt['hash_digest'] != topics_id_hash_dict.get(bt['topic_id'])]


def update_redis_and_mongo_to_latest(need_update_topics):
    if not need_update_topics:
        logger.warning('None of topic needs to be updated')
        return None
    for topic in need_update_topics:
        redis_cli.hset('topics', topic['topic_id'], topic['hash_digest'])
        mongo.update_one(
                col='topics',
                query={'topic_id': topic['topic_id']},
                data=topic,
                )
        logger.debug(f'Topic {topic["name"]} (id={topic["topic_id"]}) was updated in redis and mongo to the latest!')
    return True


def batch_process_topics_data(crawler, topic_dicts, batch, thread_num):
    topics_id_hash_dict = redis_cli.hgetall('topics')
    # Multi-thread crawling
    total = len(topic_dicts)
    for index in range(0, total, batch):
        pool = ThreadPool(processes=thread_num)
        logger.info(f'batch process topics: {index}/{total}')
        pool.map(crawler.get_topic_data, topic_dicts[index: index + batch])
        pool.close()
        pool.join()
        need_update_topics = get_need_update_topics(topics_id_hash_dict, topic_dicts[index: index + batch])
        update_redis_and_mongo_to_latest(need_update_topics)
    # Ordinary crawling
    # [*map(crawler.get_topic_data, topic_dicts)]
    # need_update_topics = get_need_update_topics(topics_id_hash_dict, topic_dicts)
    # update_redis_and_mongo_to_latest(need_update_topics)


def crawl():
    sync_redis_with_mongo()
    crawler = Crawler()
    all_topic_dicts = get_all_topics(crawler, thread_num=4)
    batch_process_topics_data(crawler, all_topic_dicts, batch=50, thread_num=8)


if __name__ == '__main__':
    crawl()

