# utils/toolkit.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging.config
import logging, os, time
from datetime import timezone
from functools import wraps
from math import ceil

import requests, yaml
from redis import ConnectionPool, Redis

from settings.constant import LOCAL_TZ

logger = logging.getLogger(__name__)


def logging_init():
    with open('settings/logging.yaml', 'r') as f:
        logging_config = yaml.safe_load(f.read())
        log_dir = logging_config['handlers']['file']['filename']
    if not os.path.exists('log/'):
        os.mkdir('log/')
    if not os.path.exists(log_dir):
        with open(log_dir, 'w') as f:
            f.write('### ### ### Started ### ### ###\n')
    logging.config.dictConfig(logging_config)

logging_init()


def redis_init():
    with open('settings/redis.yaml', 'r') as f:
        redis_config = yaml.safe_load(f.read())
    try:
        pool = ConnectionPool(host=redis_config['host'], port=redis_config['port'], db=redis_config['db'], decode_responses=True)
    except Exception as e:
        logger.exception('Redis Connecting Failed!')
    return Redis(connection_pool=pool)

redis_cli = redis_init()


class AttrDict(dict):
    def __getattr__(self, attr):
        try:
            value = self[attr]
        except KeyError:
            raise AttributeError(f'Attribute "{attr}" does not exist.')
        if isinstance(value, dict):
            value = AttrDict(value)
        return value

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError(f'Attribute "{attr}" does not exist.')


class Pagination:
    def __init__(self, seq, per_page, page=1):
        self.seq = seq
        self.per_page = per_page
        self.page = page
        self.total = len(seq)
        self.pages = ceil(self.total / per_page)

    def get_items(self):
        return self.seq[self.per_page * (self.page - 1): self.per_page * self.page]

    def iter_pages(self):
        return range(1, self.pages + 1)

    @property
    def has_prev(self):
        return False if self.page == 1 else True

    @property
    def prev_num(self):
        return self.page - 1 if self.has_prev else 1

    @property
    def has_next(self):
        return True if self.page < self.pages else False

    @property
    def next_num(self):
        return self.page + 1 if self.has_next else self.pages


def get_http_respense(url, method=None, rtype=None, timeout=5, **payload):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        }
    try:
        response = requests.request(method, url, timeout=timeout, headers=headers, **payload)
    except Exception as e:
        logger.exception('HTTP Exception Found!')
        return None, str(e)
    if not response.ok:
        return False, f'URL: {response.url}, Status Code: {response.status_code}, Reason: {response.reason}'
    else:
        if rtype is 'JSON':
            return True, response.json()
        elif rtype is 'HTML':
            response.encoding = 'UTF-8'
            return True, response.text


def utc_2_local_datetime(utc_datetime):
    return utc_datetime.replace(tzinfo=timezone.utc).astimezone(LOCAL_TZ)


def timecost(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.clock()
        result = func(*args, **kwargs)
        end = time.clock()
        logger.debug(f'Running Time: {end - start:.3f} Seconds')
        return result
    return wrapper

