# settings/flask_config.py
# -*- coding: utf-8 -*-

from datetime import timedelta

from crawl import main as main_crawl


class Basic:
    DEBUG = True
    TESTING = True
    JSON_AS_ASCII = False
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(seconds=15)
    SCHEDULER_API_ENABLED = True
    JOBS = [
                {
                    'id': 'main_crawl',
                    'func': main_crawl,
                    'args': '',
                    'trigger': {
                        'type': 'cron',
                        'day_of_week': '*',
                        'hour': '*',
                        'minute': '24',
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

