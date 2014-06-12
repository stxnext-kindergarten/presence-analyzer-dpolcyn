# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from flask import (
    redirect,
    make_response,
)
from flask.ext.mako import render_template
from mako.exceptions import TopLevelLookupException
import locale
from collections import defaultdict, OrderedDict

from presence_analyzer.main import app
from presence_analyzer.utils import (
    jsonify,
    get_data,
    mean,
    group_by_weekday,
    count_avg_group_by_weekday,
    get_xml_data,
)

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/templates/presence_weekday')


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [{'user_id': i, 'name': 'User {0}'.format(str(i))}
            for i in data.keys()]


@app.route('/api/v2/users', methods=['GET'])
@jsonify
def users_xml_view():
    """
    Users listing for dropdown.
    """
    data = get_xml_data()
    locale.setlocale(locale.LC_COLLATE, 'pl_PL.UTF-8')
    sorted_data = sorted(
        data.iteritems(),
        key=lambda x: x[1]['name'],
        cmp=locale.strcoll,
    )

    return sorted_data


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])

    result = [(calendar.day_abbr[weekday], mean(intervals))
              for weekday, intervals in weekdays.items()]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], sum(intervals))
              for weekday, intervals in weekdays.items()]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Return avg start, end time of given user grouped by weekday.
    """
    data = get_data()

    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = count_avg_group_by_weekday(data[user_id])
    result = [
        (
            calendar.day_abbr[weekday],
            mean(intervals['start']),
            mean(intervals['end']),
        )
        for weekday, intervals in weekdays.items()
    ]
    return result


@app.route('/<string:template_name>', methods=['GET'])
def templates_renderer(template_name):
    """
    Render templates.
    """
    try:
        return render_template(template_name + ".html")
    except TopLevelLookupException:
        return make_response("page not found", 404)
