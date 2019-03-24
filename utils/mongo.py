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
        self._client.close()

    def update_one(self, query, data, collection, upsert=True):
        if not isinstance(data, dict):
            logger.warning(f'data {data} is not instance of dict, can not be updated!')
            return None
        data['last_updated'] = datetime.utcnow()
        result = self._db[collection].update_one(query, {'$set': data}, upsert=upsert)
        return result.upserted_id

