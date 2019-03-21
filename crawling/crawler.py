# -*- coding: utf-8 -*-

from __future__ import absolute_import
import datetime, time

from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from utils.toolkit import get_http_respense, logging, timecost

logger = logging.getLogger(__name__)
CHROME_DRIVER_PATH = 'crawling/chromedriver'

class TopTopicsLocatingError(Exception):
    def __init__(self, error_msg):
        super(TopTopicsLocatingError, self).__init__()
        self.error_msg = error_msg


class TopicInfoCrawlingError(object):
    def __init__(self, error_msg):
        super(TopicInfoCrawlingError, self).__init__()
        self.error_msg = error_msg


class Crawler:
    def __init__(self, main_url):
        self.main_url = main_url

    def open_main_page(self):
        try:
            element = WebDriverWait(wd, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'Qrcode-content')))
            # element = WebDriverWait(wd, 5).until(lambda wd: wd.find_element_by_class_name('Qrcode-content'))
        except Exception as e:
            logger.exception('Exception Found!')
        finally:
            wd.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            qr_img_url = element.find_element_by_tag_name('img').get_attribute('src')

    @timecost
    def get_top_topics(self):
        try:
            flag, info = get_http_respense(self.main_url+'/topics', method='GET', rtype='HTML')
        except Exception as e:
            raise e
        if flag is False:
            logger.error(f'Got unusual http response:\n{info}')
            raise TopTopicsLocatingError('Cannot locate top topics!')
        tree = etree.HTML(info)
        top_topic_elements = tree.xpath('//li[@class="zm-topic-cat-item"]/a')
        top_topics = [ele.text for ele in top_topic_elements]
        logger.debug(f'top topics:\n{top_topics}')
        return top_topics

    @timecost
    def get_all_topics(self, top_topic):
        options = webdriver.ChromeOptions()
        options.add_argument('lang=zh_CN.UTF-8')
        options.add_argument('--headless')
        wd = webdriver.Chrome(CHROME_DRIVER_PATH, chrome_options=options)
        wd.implicitly_wait(0.1)
        wd.get(self.main_url + '/topics#' + top_topic)
        click_times = 0
        while True:
            try:
                wd.find_element_by_xpath('//a[@class="zg-btn-white zu-button-more"]').click()
                logger.debug('Click +1!')
            except Exception:
                logger.info(f'Click {click_times} time(s) under top topic {top_topic}')
                break
            else:
                click_times += 1
                time.sleep(1)
                break # debug
        tree = etree.HTML(wd.page_source)
        topic_elements = tree.xpath('//div[@class="item"]//a[@target="_blank"]')
        topics = [
                    {
                    'topic_id': ele.get('href').split(r'/')[-1],
                    'name': ele.find('strong').text,
                    }
                for ele in topic_elements]
        logger.debug(f'topics:\n{topics}')
        return topics

    def _get_relative_topic_ids_by_page(self, topic_id, topic_type, page_size):
        offset = 0
        topic_ids = []
        while True:
            try:
                flag, info = get_http_respense(f'{self.main_url}/api/v3/topics/{topic_id}/{topic_type}?limit={page_size}&offset={offset}', method='GET', rtype='JSON')
            except Exception as e:
                raise e
            if flag is False:
                logger.error(f'Got unusual http response:\n{info}')
                raise TopicInfoCrawlingError('Cannot get relative topic info correctly!')
            if not info['data']:
                return topic_ids
            infos = [item['id'] for item in info['data'] if item['id'] != topic_id]
            topic_ids.extend(infos)
            offset += page_size

    @timecost
    def get_topic_info(self, topic):
        logger.debug(f'Crawling Topic {topic["name"]}')
        # topic main info
        try:
            flag, info = get_http_respense(self.main_url+f'/topic/{topic["topic_id"]}/top-answers', method='GET', rtype='HTML')
        except Exception as e:
            raise e
        if flag is False:
            logger.error(f'Got unusual http response:\n{info}')
            raise TopicInfoCrawlingError('Cannot get main topic info correctly!')
        tree = etree.HTML(info)
        number_board = tree.xpath('//strong[@class="NumberBoard-itemValue"]')
        follower_num, question_num = number_board[0].get('title'), number_board[1].get('title')
        logger.debug(f'follower num: {follower_num}, question num: {question_num}')
        # relative topic info
        parent_topic_ids = self._get_relative_topic_ids_by_page(topic["topic_id"], 'parent', 10)
        children_topic_ids = self._get_relative_topic_ids_by_page(topic["topic_id"], 'children', 10)
        logger.debug(f'parent_topic_ids: {parent_topic_ids}, children_topic_ids: {children_topic_ids}')
        topic.update({
                    'follower_num': follower_num,
                    'question_num': question_num,
                    'parent_topic_ids': parent_topic_ids,
                    'children_topic_ids': children_topic_ids,
                    })
        return topic

