# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils
from presence_analyzer.main import app


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv',
)

TEST_DATA_XML = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'users_test.xml',
)


# pylint: disable=E1103
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update(
            {
                'DATA_CSV': TEST_DATA_CSV,
                'DATA_XML': TEST_DATA_XML
            }
        )
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday')

    def test_api_users_v2(self):
        """
        Test users listingv2.
        """
        resp = self.client.get('/api/v2/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 84)
        self.assertEqual(
            data[u"10"],
            {
                u'image': u'https://intranet.stxnext.pl/api/images/users/10',
                u'name': u'Maciej Z.'
            }
        )

    def test_mean_time_weekday_view(self):
        """
        Checking inversed presence time of given user grouped by weekday.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')

        sample_data = json.loads(resp.data)
        self.assertEqual(sample_data, [
            [u'Mon', 0],
            [u'Tue', 30047.0],
            [u'Wed', 24465.0],
            [u'Thu', 23705.0],
            [u'Fri', 0],
            [u'Sat', 0],
            [u'Sun', 0],
            ]
        )

    def test_presence_weekday_view(self):
        """
        Checking inversed totla presence time of given user grouped by
        weekaday.
        """
        resp = self.client.get('api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')

        sample_data = json.loads(resp.data)
        self.assertEqual(sample_data, [
            [u'Weekday', 'Presence (s)'],
            [u'Mon', 0],
            [u'Tue', 30047.0],
            [u'Wed', 24465.0],
            [u'Thu', 23705.0],
            [u'Fri', 0],
            [u'Sat', 0],
            [u'Sun', 0],
            ]
        )

    def test_presence_start_end_view(self):
        """
        Testing returned avg starts, ends of given user grouped by weekeday.
        """
        resp = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')

        sample_data = json.loads(resp.data)
        self.assertEqual(sample_data, [
            [u'Mon', 0, 0],
            [u'Tue', 34745.0, 64792.0],
            [u'Wed', 33592.0, 58057.0],
            [u'Thu', 38926.0, 62631.0],
            [u'Fri', 0, 0],
            [u'Sat', 0, 0],
            [u'Sun', 0, 0],
        ])

    def test_templates_render(self):
        """
        Testing returned templates.
        """
        resp = self.client.get('/presence_weekday')
        self.assertIn('Presence by weekday', resp.data)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/mean_time_weekdays')
        self.assertIn('Presence mean time by weekday', resp.data)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/presence_start_end')
        self.assertIn('Presence start end', resp.data)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/bad_page_name')
        self.assertIn('page not found', resp.data)
        self.assertEqual(resp.status_code, 404)


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update(
            {
                'DATA_CSV': TEST_DATA_CSV,
                'DATA_XML': TEST_DATA_XML
            }
        )

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(data[10][sample_date]['start'],
                         datetime.time(9, 39, 5))

    def test_get_xml_data(self):
        """
        Test parsing XML file.
        """
        data = utils.get_xml_data()
        self.assertIsInstance(data, dict)
        sample_data = {
            'image': u'https://intranet.stxnext.pl/api/images/users/19',
            'name': u'Anna K.'
        }
        self.assertEqual(sample_data, data[19])
        sample_data = {
            'image': u'https://intranet.stxnext.pl/api/images/users/160',
            'name': u'Olga K.'
        }
        self.assertIn(sample_data, data.values())
        self.assertItemsEqual(data[10].keys(), [u'image', u'name'])

    def test_group_by_weekday(self):
        """
        Test groups presence entries by weeekday.
        """
        sample_data = utils.get_data()
        result = utils.group_by_weekday(sample_data[10])
        self.assertIsInstance(result, dict)
        box = {
            0: [],
            1: [30047],
            2: [24465],
            3: [23705],
            4: [],
            5: [],
            6: [],
        }
        self.assertDictEqual(box, result)
        result = utils.group_by_weekday(sample_data[11])
        self.assertIsInstance(result, dict)
        box = {
            0: [24123],
            1: [16564],
            2: [25321],
            3: [22969, 22999],
            4: [6426],
            5: [],
            6: [],
        }
        self.assertDictEqual(box, result)

    def test_seconds_since_midnight(self):
        """
        Testing results of seconds_since_midnight function.
        """
        result = utils.seconds_since_midnight(datetime.time(00, 00, 30))
        self.assertEqual(result, 30)
        result = utils.seconds_since_midnight(datetime.time(00, 10, 30))
        self.assertEqual(result, 630)
        result = utils.seconds_since_midnight(datetime.time(10, 10, 30))
        self.assertEqual(result, 36630)

    def test_interval(self):
        """
        Testing calculated time between end and start.
        """
        result = utils.interval(
            datetime.time(01, 00, 00), datetime.time(10, 00, 00)
        )
        self.assertEqual(result, 32400)
        result = utils.interval(
            datetime.time(01, 00, 00), datetime.time(17, 00, 00)
        )
        self.assertEqual(result, 57600)
        result = utils.interval(
            datetime.time(01, 05, 00), datetime.time(11, 10, 15)
        )
        self.assertEqual(result, 36315)

    def test_mean(self):
        """
        Testing calculated avgerage of list.
        """
        self.assertEqual(utils.mean([]), 0)
        self.assertEqual(utils.mean([
            1,
            2,
            3,
            78,
            119,
        ]), 40.6)
        self.assertAlmostEqual(utils.mean([
            1.5,
            2.2,
            78.31054,
            19.86465484,
        ]), 25.4687987)
        self.assertAlmostEqual(utils.mean([
            74.51,
            0.9243,
            78.64,
            19.545,
        ]), 43.404825)
        self.assertAlmostEqual(utils.mean([
            74.53,
            53.22,
            24.75,
            19.5345,
        ]), 43.00862501)
        self.assertEqual(utils.mean([
            54.2,
            234.4,
            59.93,
            43.4,
        ]), 97.9825)

    def test_count_avg_group_by_weekday(self):
        """
        Testing returned presence starts, ends by weekday.
        """
        sample_data = utils.get_data()
        days = utils.count_avg_group_by_weekday(
            sample_data[10],
        )
        self.assertEqual(
            days,
            {
                0: {'start': [], 'end': []},
                1: {'start': [34745], 'end': [64792]},
                2: {'start': [33592], 'end': [58057]},
                3: {'start': [38926], 'end': [62631]},
                4: {'start': [], 'end': []},
                5: {'start': [], 'end': []},
                6: {'start': [], 'end': []},
            }
        )
        days = utils.count_avg_group_by_weekday(
            sample_data[11],
        )
        self.assertAlmostEqual(
            days,
            {
                0: {'start': [33134], 'end': [57257]},
                1: {'start': [33590], 'end': [50154]},
                2: {'start': [33206], 'end': [58527]},
                3: {'start': [37116, 34088], 'end': [60085, 57087]},
                4: {'start': [47816], 'end': [54242]},
                5: {'start': [], 'end': []},
                6: {'start': [], 'end': []},
            }
        )


def suite():
    """
    Default test suite.
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()
