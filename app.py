# app.py
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from datetime import datetime

from pandas import DataFrame as DF
from flask import Blueprint, Flask
from flask import request, session, render_template, url_for
from flask_apscheduler import APScheduler
from flask_bootstrap import Bootstrap
from pyecharts.charts import Bar, Line, Scatter
from pyecharts import options as opts
import pymongo

from settings.constant import DISPLAY_TOPIC_NUM, INIT_OPTS, PER_PAGE, REMOTE_HOST, SUMMARY_ATTR_DICT
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
    return render_template('pagination.html', summary_pagination=pagination, summary_type=summary_type, summary_pagination_title=SUMMARY_ATTR_DICT[summary_type]['key_word'] + '话题总结')


def render_line(df, title, sort_by):
    df.sort_values(by=sort_by, ascending=False, inplace=True)
    df.drop(columns=sort_by, inplace=True)
    df = df.diff(axis='columns').fillna(0)
    line_global_opts = {
            'legend_opts': opts.LegendOpts(type_='scroll', orient='vertical', pos_right='0%', pos_top='5%'),
            'title_opts': opts.TitleOpts(title=title),
            'toolbox_opts': opts.ToolboxOpts(),
            'tooltip_opts': opts.TooltipOpts(trigger='axis'),
            'xaxis_opts': opts.AxisOpts(name='日期', type_='time'),
            'yaxis_opts': opts.AxisOpts(name='日变化', type_='value'),
            }
    line = Line(INIT_OPTS).set_global_opts(**line_global_opts).add_xaxis([*df.columns])
    index = 0
    topics = []
    for nt in df.itertuples():
        if index == DISPLAY_TOPIC_NUM:
            break
        line = line.add_yaxis(series_name=nt[0], y_axis=[*nt[1:]], is_smooth=True)
        topics.append(nt[0])
        index += 1
    return line, topics


def render_bar(sr, title):
    bar_global_opts = {
            'legend_opts': opts.LegendOpts(is_show=False),
            'title_opts': opts.TitleOpts(title=title),
            'toolbox_opts': opts.ToolboxOpts(),
            'tooltip_opts': opts.TooltipOpts(axis_pointer_type='shadow', trigger='axis'),
            'xaxis_opts': opts.AxisOpts(name='话题名', type_='category'),
            'yaxis_opts': opts.AxisOpts(name='数量', type_=None),
            }
    return (
            Bar(INIT_OPTS)
            .set_global_opts(**bar_global_opts)
            .add_xaxis([*sr.index])
            .add_yaxis(series_name='', yaxis_data=sr.tolist())
            .set_series_opts(label_opts=opts.LabelOpts(position='right'))
            .reversal_axis()
        )


def render_scatter(df, title):
    # TODO display scatter with right labels
    df.sort_values(by='question_num_summary', inplace=True)
    scatter_global_opts = {
            'legend_opts': opts.LegendOpts(is_show=False),
            'title_opts': opts.TitleOpts(title=title),
            'toolbox_opts': opts.ToolboxOpts(),
            'tooltip_opts': opts.TooltipOpts(axis_pointer_type='cross', formatter='{b}: {@}'),
            'xaxis_opts': opts.AxisOpts(name='问题数', type_='value'),
            'yaxis_opts': opts.AxisOpts(name='关注人数', type_='value'),
            }
    return (
            Scatter(INIT_OPTS)
            .set_global_opts(**scatter_global_opts)
            .add_xaxis(df.loc[:, 'question_num_summary'].tolist())
            .add_yaxis(series_name='', y_axis=df.loc[:, 'follower_num_summary'].tolist(), symbol_size=3)
        )


@app.route('/summary/', methods=['GET', 'POST'])
def summary():
    summary_type = request.args['summary_type']
    query_dict = {sp: request.args[sp] for sp in SUMMARY_ATTR_DICT[summary_type]['search_params']}
    topic_summary_dict = mongo.find_one(col=summary_type + '_topics_summary', query=query_dict)
    summary_title = topic_summary_dict['summary_last_updated'].strftime(SUMMARY_ATTR_DICT[summary_type]['summary_title_fmt']) + '话题总结'
    # topic question display
    question_num_df = DF.from_dict(topic_summary_dict['question_num_dict'])
    question_line, topics = render_line(question_num_df, title='话题问题数变化', sort_by='var')
    last_day_question_sr = question_num_df.iloc[:, -1].loc[topics]
    question_bar = render_bar(last_day_question_sr, title=f'话题问题数({last_day_question_sr.name})')
    # topic follower display
    follower_num_df = DF.from_dict(topic_summary_dict['follower_num_dict'])
    follower_line, topics = render_line(follower_num_df, title='话题关注人数变化', sort_by='var')
    last_day_follower_sr = follower_num_df.iloc[:, -1].loc[topics]
    follower_bar = render_bar(last_day_follower_sr, title=f'话题关注人数({last_day_follower_sr.name})')
    # topic question/follower display
    topic_follower_question_df = DF.from_dict(topic_summary_dict['topic_follower_question_dict'])
    scatter = render_scatter(topic_follower_question_df, title='话题总览')
    charts = [question_line, follower_line, question_bar, follower_bar, scatter]
    scripts = [c.load_javascript() for c in charts]
    return render_template('summary.html', summary_type=summary_type, summary_title=summary_title, host=REMOTE_HOST, scripts=scripts, charts=charts)


if __name__ == '__main__':
    app.run()

