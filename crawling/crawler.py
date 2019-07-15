# crawling/crawler.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging, os, time
from operator import itemgetter

from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from settings.constant import CHROME_DRIVER_PATH, ZHIHU_URL
from utils.toolkit import get_http_respense, timecost

logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self):
        self.main_url = ZHIHU_URL
        self.webdriver_dir = CHROME_DRIVER_PATH

    def open_main_page(self):
        try:
            element = WebDriverWait(wd, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'Qrcode-content')))
            # element = WebDriverWait(wd, 5).until(lambda wd: wd.find_element_by_class_name('Qrcode-content'))
        except Exception as e:
            logger.exception('Exception Found!')
        finally:
            wd.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            qr_img_url = element.find_element_by_tag_name('img').get_attribute('src')

    @timecost
    def get_home_topics(self):
        url = os.path.join(self.main_url, 'topics')
        flag, result = get_http_respense(url, method='GET', rtype='HTML')
        if not flag:
            logger.error(f'Got unusual http response:\n{result}')
            return None
        tree = etree.HTML(result)
        try:
            home_topic_elements = tree.xpath('//li[@class="zm-topic-cat-item"]/a')
        except Exception as e:
            logger.exception(f'Home topic page was changed!\n{e}')
            return None
        home_topics = [hte.text for hte in home_topic_elements]
        logger.info(f'{len(home_topics)} home topics were found:\n{home_topics}')
        return home_topics

    @timecost
    def get_topics_by_home_topic(self, home_topic):
        options = webdriver.ChromeOptions()
        options.add_argument('lang=zh_CN.UTF-8')
        options.add_argument('--headless') # for debug
        wd = webdriver.Chrome(self.webdriver_dir, chrome_options=options)
        wd.implicitly_wait(0.1)
        url = os.path.join(self.main_url, 'topics#' + home_topic)
        wd.get(url)
        click_times = 0
        while True:
            try:
                wd.find_element_by_xpath('//a[@class="zg-btn-white zu-button-more"]').click()
                logger.debug(f'{home_topic} Click +1!')
            except Exception as e:
                logger.info(f'Click {click_times} time(s) under home topic {home_topic}')
                break # for debug
            else:
                click_times += 1
                time.sleep(1)
                break # for debug
        tree = etree.HTML(wd.page_source)
        try:
            topic_elements = tree.xpath('//div[@class="item"]//a[@target="_blank"]')
        except Exception as e:
            logger.exception(f'Sub home topic pages were changed!\n{e}')
            return None
        topic_dicts = [
                        {
                        'topic_id': te.get('href').split(r'/')[-1],
                        'name': te.find('strong').text,
                        }
                    for te in topic_elements]
        logger.info(f'{len(topic_dicts)} topics were found under home topic {home_topic}:\n{topic_dicts}.')
        return topic_dicts

    def _get_relative_topic_ids(self, topic_id, relative_type, page_size):
        offset = 0
        topic_ids = []
        while True:
            url = os.path.join(self.main_url, f'api/v3/topics/{topic_id}/{relative_type}?limit={page_size}&offset={offset}')
            flag, result = get_http_respense(url, method='GET', rtype='JSON')
            if not flag:
                logger.error(f'Got unusual http response:\n{result}')
                return None
            data = result.get('data')
            if not data:
                return topic_ids
            topic_ids.extend(map(itemgetter('id'), data))
            offset += page_size

    @timecost
    def get_topic_data(self, topic):
        # topic data
        url = os.path.join(self.main_url, f'topic/{topic["topic_id"]}/hot')
        flag, result = get_http_respense(url, method='GET', rtype='HTML')
        if not flag:
            logger.error(f'Got unusual http response:\n{result}')
            return None
        tree = etree.HTML(result)
        try:
            number_board = tree.xpath('//strong[@class="NumberBoard-itemValue"]')
        except Exception as e:
            logger.exception(f'Number board was changed!\n{e}')
            return None
        follower_num, question_num = tuple(map(lambda nb: int(nb.get('title')), number_board))
        # relative topic ids
        parent_topic_ids = self._get_relative_topic_ids(topic['topic_id'], 'parent', 10)
        children_topic_ids = self._get_relative_topic_ids(topic['topic_id'], 'children', 10)
        logger.info(f'Crawled data for topic {topic["name"]}:\nfollower_num: {follower_num}, question_num: {question_num}, parent_topic_ids: {parent_topic_ids}, children_topic_ids: {children_topic_ids}')
        # update data
        topic.update({
                'follower_num': follower_num,
                'question_num': question_num,
                'parent_topic_ids': parent_topic_ids,
                'children_topic_ids': children_topic_ids,
                })

