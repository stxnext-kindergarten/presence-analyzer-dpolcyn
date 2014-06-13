# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import threading
import time
from json import dumps
from functools import wraps
from datetime import datetime

from flask import Response

from presence_analyzer.main import app

import xml
import urllib2
from lxml import etree

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103

CACHE = {}


def cache(key, duration):
    """
Cache function.
If called item in function, return item.
If not return item and add to cache.
"""
    def _cache(function):
        def __cache(*args, **kwargs):
            if key in CACHE:
                if (time.time() - CACHE[key]['time']) < duration:
                    return CACHE[key]['value']

            result = function(*args, **kwargs)
            CACHE[key] = {
                'value': result,
                'time': time.time()
            }

            return CACHE[key]['value']
        return __cache
    return _cache


def lock(function):
    """
Decorator. If thread is executing the function and another one
want to call the function, then second one will immediately
receive a return value.
"""
    function.locker = threading.Lock()

    @wraps(function)
    def locking(*args, **kwargs):
        with function.locker:
            result = function(*args, **kwargs)
        return result
    return locking


def jsonify(function):
    """
Creates a response with the JSON representation of wrapped function result.
"""
    @wraps(function)
    def inner(*args, **kwargs):
        return Response(dumps(function(*args, **kwargs)),
                        mimetype='application/json')
    return inner


@lock
@cache('user_id', 600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
                },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
                },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = {i: [] for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
Calculates arithmetic mean. Returns zero for empty lists.
"""
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def count_avg_group_by_weekday(items):
    """
    Groups presence starts, ends by weekday.
    """
    result = {i: {'start': [], 'end': []} for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()]['start'].append(seconds_since_midnight(start))
        result[date.weekday()]['end'].append(seconds_since_midnight(end))

    return result


def update_user_xml():
    """
    Downloading data from remote adres to xml file.
    """
    with open(app.config['DATA_XML'], 'w+') as xmlfile:
        remote_data = urllib2.urlopen('http://sargo.bolt.stxnext.pl/users.xml')
        new_data = remote_data.read()
        xmlfile.write(new_data)


def get_xml_data():
    """
    Get and parse data from xml file.
    """
    with open(app.config['DATA_XML'], 'r') as xmlfile:
        tree = etree.parse(xmlfile)
        server = tree.find('server')
        host = server.find('host').text
        protocol = server.find('protocol').text
        users = tree.find('users')
        profile = {
            int(user.get('id')): {
                'name': unicode(user.find('name').text),
                'image': "{protocol}://{host}{image}".format(
                    protocol=protocol,
                    host=host,
                    image=user.find('avatar').text,
                )
            }
            for user in users.findall('user')
        }
        return profile
