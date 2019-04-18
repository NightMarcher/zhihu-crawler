# utils/toolkit.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging, os, time
import logging.config
from datetime import datetime, timedelta, timezone
from functools import wraps

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


def redis_init():
    with open('settings/redis.yaml', 'r') as f:
        redis_config = yaml.safe_load(f.read())
    try:
        pool = ConnectionPool(host=redis_config['host'], port=redis_config['port'], db=redis_config['db'], decode_responses=True)
    except Exception as e:
        logger.exception('Redis Connecting Failed!')
    redis = Redis(connection_pool=pool)
    return redis


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

