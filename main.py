# -*- coding: utf-8 -*-

from __future__ import absolute_import

from crawling.crawler import Crawler
from utils.toolkit import logging

logger = logging.getLogger(__name__)
ZHIHU_URL = 'https://www.zhihu.com'

if __name__ == '__main__':
    crawler = Crawler(ZHIHU_URL)

    top_topics = crawler.get_top_topics()
    logger.info(f'{len(top_topics)} top topics were found!')

    all_topics = []
    for top_topic in top_topics:
        topics = crawler.get_all_topics(top_topic)
        logger.info(f'{len(topics)} topics were found under top topic {top_topic}!')
        all_topics.extend(topics)
        break # debug

    for topic in all_topics:
        topic_info = crawler.get_topic_info(topic)
        break # debug
