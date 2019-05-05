# settings/flask_config.py
# -*- coding: utf-8 -*-

from datetime import timedelta

from crawling.main import crawl
from analyzing.analyzer import analyze


def do_jobs_in_sequence(*funcs):
    for func in funcs:
        func()


class Basic:
    DEBUG = True
    TESTING = True
    JSON_AS_ASCII = False
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(seconds=15)
    SCHEDULER_API_ENABLED = True
    JOBS = [
                {
                    'id': 'crawl_and_analyze',
                    'func': analyze,
                    # 'func': do_jobs_in_sequence,
                    # 'args': (crawl, analyze),
                    'trigger': {
                        'type': 'cron',
                        'day_of_week': '*',
                        'hour': '23',
                        'minute': '50',
                        # 'hour': '*/4',
                        # 'minute': '30',
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

