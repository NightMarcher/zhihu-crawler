# settings/flask_config.py
# -*- coding: utf-8 -*-

from datetime import timedelta

from crawling.main import crawl


class Basic:
    DEBUG = True
    TESTING = True
    JSON_AS_ASCII = False
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(seconds=15)
    SCHEDULER_API_ENABLED = True
    JOBS = [
                {
                    'id': 'crawl',
                    'func': crawl,
                    'args': '',
                    'trigger': {
                        'type': 'cron',
                        'day_of_week': '*',
                        'hour': '*',
                        'minute': '21',
                        'second': '0'
                        }
            },

                # {
                #     'id': '',
                #     'func': ,
                #     'args': '',
                #     'trigger': {
                #         'type': 'cron',
                #         'day_of_week': '',
                #         'hour': '',
                #         'minute': '',
                #         'second': ''
                #         }
            # }
    ]

