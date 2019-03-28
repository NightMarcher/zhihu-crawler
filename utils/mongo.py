# utils/mongo.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from datetime import datetime
import logging

import pymongo, yaml

logger = logging.getLogger(__name__)
with open('settings/mongo.yaml', 'r') as f:
    mongo_config = yaml.load(f.read())


class Mongo:
    def __init__(self):
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

    def find(self, col, filters=None, fields=None, **kwargs):
        # TODO batch_size, limit, max_time_ms, sort
        return self._db[col].find(filters, fields, **kwargs)

    def update_one(self, col, query, data, upsert=True):
        if not isinstance(data, dict):
            logger.warning(f'Following data is not instance of dict, MongoDB can not be updated!\n{data}')
            return None
        data['last_updated'] = datetime.utcnow()
        cur = self._db[col].update_one(query, {'$set': data}, upsert=upsert)
        if cur.upserted_id is None:
            logger.error(f'Following query updated failed!\n{query}')
        else:
            logger.debug(f'Mongo collection {cur.upserted_id} updated succeed!')
