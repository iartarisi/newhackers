from datetime import datetime, timedelta
import time
import unittest

from bs4 import BeautifulSoup
import mock
import redis

from newhackers import backend, config
from newhackers.utils import valid_url
from fixtures import FRONT_PAGE, STORIES, STORIES_JSON
from utils import seconds_old


class BackendTest(unittest.TestCase):
    def setUp(self):
        self.rdb = backend.rdb = redis.Redis(db=13)

    def tearDown(self):
        self.rdb.flushdb()

    def test_time_too_old(self):
        with mock.patch.object(config, 'CACHE_INTERVAL', 30):
            self.rdb.set("my-item/updated", seconds_old(30))
            self.assertTrue(backend.too_old("my-item"))

            self.rdb.set("my-item/updated", seconds_old(29))
            self.assertFalse(backend.too_old("my-item"))

    def test_time_too_old_key_doesnt_exist(self):
        self.assertTrue(backend.too_old("bogus-item"))

    def test_update_page_not_found(self):
        mock_get = mock.Mock(return_value=mock.Mock(
                text='No such item.'))
        with mock.patch.object(backend.requests, "get", mock_get) as get:
            self.assertRaises(backend.NotFound, backend.update_page,
                              'test_key', 'test_url')
            get.assert_called_with(config.HN + 'test_url')

    def test_update_page_server_error(self):
        mock_get = mock.Mock(return_value=mock.Mock(
                text='Unexpected weirdness.'))
        with mock.patch.object(backend.requests, "get", mock_get) as get:
            self.assertRaises(backend.ServerError, backend.update_page,
                              'test_key', 'test_url')
            get.assert_called_with(config.HN + 'test_url')

    def test_update_page(self):
        RESPONSE_TEXT = '<html>good stories</html>'
        mock_get = mock.Mock(return_value=mock.Mock(
                text=RESPONSE_TEXT))
        with mock.patch.object(backend.requests, "get", mock_get) as get:
            with mock.patch.object(backend, "parse_stories",
                                   mock.Mock(return_value=STORIES)) as parse:
                stories_json = backend.update_page("test_key", "test_url")
                get.assert_called_with(config.HN + "test_url")
                parse.assert_called_with(RESPONSE_TEXT)
                self.assertEqual(self.rdb.get("test_key"), STORIES_JSON)
                self.assertEqual(stories_json, STORIES_JSON)


class ParseStoriesTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        with open(FRONT_PAGE) as f:
            self.stories, self.more = backend.parse_stories(f.read()).values()

    def test_parse_stories_right_length(self):
        self.assertEqual(len(self.stories), config.STORIES_PER_PAGE)

    def test_parse_stories_more_id(self):
        self.assertEqual(self.more, STORIES['more'])

    def test_parse_stories_titles_are_different(self):
        diff_titles = set(d['title'] for d in self.stories)
        # NB Stories aren't guaranteed to have different names in
        # real-life HN, but we got a lucky fixture
        self.assertEqual(len(diff_titles), config.STORIES_PER_PAGE)

    def test_parse_stories_title(self):
        self.assertEqual(self.stories[0]['title'], 'Dummy Title')

    def test_parse_stories_urls_are_different(self):
        diff_urls = set(s['link'] for s in self.stories)
        self.assertEqual(len(diff_urls), config.STORIES_PER_PAGE)

    def test_parse_stories_urls_are_valid(self):
        for story in self.stories:
            try:
                self.assertTrue(valid_url(story['link']),
                                "URL is invalid: " + story['link'])
            except AssertionError:
                # Ask HN isn't a valid url, but it's still good
                if not story['link'].startswith("item?id="):
                    raise

    def test_parse_stories_time(self):
        # first item is dated 22 hours ago
        self.assertAlmostEqual(
            self.stories[0]['time'],
            time.mktime((datetime.now() - timedelta(hours=22)).timetuple()),
            delta=1)

        # 2 day ago
        self.assertAlmostEqual(
            self.stories[1]['time'],
            time.mktime((datetime.now() - timedelta(days=2)).timetuple()),
            delta=1)

        # jobs post is dated one day ago
        self.assertAlmostEqual(
            self.stories[18]['time'],
            time.mktime((datetime.now() - timedelta(days=1)).timetuple()),
            delta=1)

    def test_parse_stories_comments(self):
        self.assertEqual(self.stories[0]['comments_no'], 56)
        self.assertEqual(self.stories[10]['comments_no'], 1)

        # this story has just the text comments, without any count
        self.assertEqual(self.stories[5]['comments_no'], -1)

        # Jobs
        self.assertIsNone(self.stories[19]['comments_no'])
        # Ask
        self.assertEqual(self.stories[18]['comments_no'], 65)

        # discuss
        self.assertEqual(self.stories[15]['comments_no'], 0)

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

    def test_parse_subtexts_no_comments(self):
        self.assertIsNone(backend._parse_subtexts(BeautifulSoup()))
