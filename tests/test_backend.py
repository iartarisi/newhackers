from datetime import datetime, timedelta
import time
import unittest

import mock
import redis

from newhackers import backend
from fixtures import FRONT_PAGE


def seconds_old(secs):
    """Return an epoch float that's :secs: seconds old"""
    return time.mktime(
        (datetime.now() - timedelta(seconds=secs)).timetuple())


class ParseStoriesTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        with open(FRONT_PAGE) as f:
            self.stories = backend.parse_stories(f.read())

    def test_parse_stories_right_length(self):
        self.assertEqual(len(self.stories), backend.STORIES_PER_PAGE)

    def test_parse_stories_titles_are_different(self):
        diff_titles = set(d['title'] for d in self.stories)
        # NB Stories aren't guaranteed to have different names in
        # real-life HN, but we got a lucky fixture
        self.assertEqual(len(diff_titles), backend.STORIES_PER_PAGE)

    def test_parse_stories_time(self):
        def almost_equal(a, b):
            """A more approximate equality comparison to suit our test env"""
            return a + 1 == b or a == b + 1 or self.assertEqual(a, b)

        # first item is dated 22 hours ago
        almost_equal(self.stories[0]['time'], time.mktime(
                (datetime.now() - timedelta(hours=22)).timetuple()))

        # 2 day ago
        almost_equal(self.stories[1]['time'], time.mktime(
                (datetime.now() - timedelta(days=2)).timetuple()))

        # jobs post is dated one day ago
        almost_equal(self.stories[18]['time'], time.mktime(
                (datetime.now() - timedelta(days=1)).timetuple()))
            
    def test_parse_stories_comments(self):
        self.assertEqual(self.stories[0]['comments'], 56)
        self.assertEqual(self.stories[10]['comments'], 1)
        
        # Jobs
        self.assertIsNone(self.stories[19]['comments'])
        # Ask
        self.assertEqual(self.stories[18]['comments'], 65)

        # discuss
        self.assertEqual(self.stories[15]['comments'], 0)

    def test_parse_stories_points(self):
        self.assertEqual(self.stories[0]['score'], 68)

        # Jobs
        self.assertIsNone(self.stories[19]['score'])
        # Ask HN
        self.assertEqual(self.stories[18]['score'], 118)
        
    def test_parse_stories_author(self):
        self.assertEqual(self.stories[0]['author'], "kine")

        # Jobs
        self.assertIsNone(self.stories[19]['author'])
        # Ask
        self.assertEqual(self.stories[18]['author'], "DonnyV")

class BackendTest(unittest.TestCase):
    def setUp(self):
        self.rdb = backend.rdb = redis.Redis(db=13)

    def tearDown(self):
        self.rdb.flushdb()

    def test_time_too_old(self):
        with mock.patch.object(backend, 'CACHE_INTERVAL', 30):
            self.rdb.set("my-item/updated", seconds_old(30))
            self.assertTrue(backend.too_old("my-item"))

            self.rdb.set("my-item/updated", seconds_old(29))
            self.assertFalse(backend.too_old("my-item"))

    def test_time_too_old_key_doesnt_exist(self):
        self.assertTrue(backend.too_old("bogus-item"))
