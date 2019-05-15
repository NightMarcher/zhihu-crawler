# app.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from datetime import datetime

from pandas import DataFrame as DF
from flask import Blueprint, Flask
from flask import request, session, render_template, url_for
from flask_apscheduler import APScheduler
from flask_bootstrap import Bootstrap
from pyecharts.charts import Line, Page, Scatter
from pyecharts.globals import ThemeType
from pyecharts import options as opts
import pymongo

from settings.constant import DISPLAY_TOPIC_NUM, PER_PAGE, SUMMARY_ATTR_DICT
from utils.mongo import mongo
from utils.toolkit import Pagination, redis_cli

app = Flask(__name__)
app.config.from_object('settings.flask_config.Basic')
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
bootstrap = Bootstrap(app)
logger = app.logger


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/summary_pagination/', methods=['GET', 'POST'])
def summary_pagination():
    summary_type = request.args.get('summary_type')
    search_params = SUMMARY_ATTR_DICT[summary_type]['search_params']
    topic_summaries = [*mongo.find(col=summary_type + '_topics_summary', fields=search_params + ['summary_last_updated']).sort('summary_last_updated', pymongo.DESCENDING)]
    summary_dicts = [{
        'summary_title': ts['summary_last_updated'].strftime(SUMMARY_ATTR_DICT[summary_type]['summary_title_fmt']) + '话题总结',
        search_params[0]: ts[search_params[0]],
        search_params[1]: ts[search_params[1]],
        } for ts in topic_summaries
    ]
    page = request.args.get('page', 1, int)
    pagination = Pagination(summary_dicts, per_page=PER_PAGE, page=page)
    return render_template('pagination.html', summary_pagination=pagination, summary_type=summary_type, summary_pagination_title=SUMMARY_ATTR_DICT[summary_type]['key_word']+'话题总结')


def render_lines(df, title, drop_column):
    df.sort_values(by=drop_column, ascending=False, inplace=True)
    df.drop(columns=drop_column, inplace=True)
    xlabels = [*df.columns]
    init_opts = opts.InitOpts(
                        theme=ThemeType.SHINE,
                        )
    global_opts = {
            'title_opts': opts.TitleOpts(title=title),
            'tooltip_opts': opts.TooltipOpts(trigger='axis'),
            'legend_opts': opts.LegendOpts(type_='scroll', orient='vertical', pos_right='0%', pos_top='5%'),
            'toolbox_opts': opts.ToolboxOpts(is_show=True),
            # 'datazoom_opts': opts.DataZoomOpts(is_show=True),
            'yaxis_opts': opts.AxisOpts(is_scale=True, min_='dataMin', max_='dataMax'),
            }
    l = Line(init_opts).add_xaxis(xlabels).set_global_opts(**global_opts)
    index = 0
    for nt in df.itertuples():
        if index == DISPLAY_TOPIC_NUM:
            break
        l = l.add_yaxis(nt[0], y_axis=tuple(nt[1:]))
        index += 1
    return l

@app.route('/summary/', methods=['GET', 'POST'])
def summary():
    summary_type = request.args['summary_type']
    query_dict = {sp: request.args[sp] for sp in SUMMARY_ATTR_DICT[summary_type]['search_params']}
    topic_summary_dict = mongo.find_one(col=summary_type + '_topics_summary', query=query_dict)
    df = DF.from_dict(topic_summary_dict['follower_num_dict'])
    # logger.debug(f'### {topic_summary_dict}')
    summary_title = summary_type
    pages = (
            render_lines(df, 'follower_num_dict', 'var')
        )
    REMOTE_HOST = "https://pyecharts.github.io/assets/js"
    return render_template('summary.html', summary_type=summary_type, host=REMOTE_HOST, script_list=[pages.load_javascript()], summary_title=summary_title, chart=pages.render_embed())


if __name__ == '__main__':
    app.run()

