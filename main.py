# main.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging

from utils.mongo import Mongo
from utils.toolkit import logging_init, redis_init
from crawling.crawler import Crawler

logging_init()
logger = logging.getLogger(__name__)


def get_all_topics():
    crawler = Crawler()
    home_topics = crawler.get_home_topics() or []
    logger.info(f'{len(home_topics)} home topics were found.')
    all_topics = []
    for ht in home_topics:
        topics = crawler.get_topics_by_home_topic(ht) or []
        logger.info(f'{len(topics)} topics were found under home topic {ht}.')
        all_topics.extend(topics)
        break # for debug
    return all_topics


if __name__ == '__main__':
    redis = redis_init()
    topics = get_all_topics()
    crawler = Crawler()
    topic_iter = map(crawler.get_topic_data, topics)

