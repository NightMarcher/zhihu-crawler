# utils/mongo.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
from datetime import datetime

import pymongo, yaml

logger = logging.getLogger(__name__)


class Mongo:
    def __init__(self):
        with open('settings/mongo.yaml', 'r') as f:
            mongo_config = yaml.safe_load(f.read())
        try:
            self._client = pymongo.MongoClient(mongo_config['host'], mongo_config['port'])
        except Exception as e:
            logger.exception('Mongo Connecting Failed!')
        else:
            self._db = self._client[mongo_config['db']]

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        # cannot close client
        self._client.close()

    def find(self, col, query=None, fields=None, **kwargs):
        # TODO batch_size, limit, max_time_ms, sort
        return self._db[col].find(query, fields, **kwargs)

    def find_one(self, col, query=None, fields=None, **kwargs):
        # TODO max_time_ms
        return self._db[col].find_one(query, fields, **kwargs)

    def update_one(self, col, query, data, upsert=True):
        if not isinstance(data, dict):
            logger.warning(f'Following data is not instance of dict, MongoDB can not be updated!\n{data}')
            return None
        data['last_upserted'] = datetime.utcnow()
        cur = self._db[col].update_one(query, {'$set': data}, upsert=upsert)
        if cur.upserted_id is not None:
            logger.debug(f'Mongo collection {cur.upserted_id} was inserted!')
        elif cur.modified_count is 0:
            logger.error(f'Following query updated failed!\nquery={query}, matched_count={cur.matched_count}, modified_count={cur.modified_count}')

