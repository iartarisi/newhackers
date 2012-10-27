from datetime import datetime, timedelta
import time
import unittest

import mock
import redis

from newhackers import backend
from newhackers.utils import valid_url
from fixtures import FRONT_PAGE, PAGE_ID, STORIES, STORIES_JSON


def seconds_old(secs):
    """Return an epoch float that's :secs: seconds old"""
    return time.mktime(
        (datetime.now() - timedelta(seconds=secs)).timetuple())


class ParseStoriesTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        with open(FRONT_PAGE) as f:
            self.stories, self.more = backend.parse_stories(f.read()).values()
            
    def test_parse_stories_right_length(self):
        self.assertEqual(len(self.stories), backend.STORIES_PER_PAGE)

    def test_parse_stories_more_id(self):
        self.assertEqual(self.more, STORIES['more'])

    def test_parse_stories_titles_are_different(self):
        diff_titles = set(d['title'] for d in self.stories)
        # NB Stories aren't guaranteed to have different names in
        # real-life HN, but we got a lucky fixture
        self.assertEqual(len(diff_titles), backend.STORIES_PER_PAGE)

    def test_parse_stories_urls_are_different(self):
        diff_urls = set(s['link'] for s in self.stories)
        self.assertEqual(len(diff_urls), backend.STORIES_PER_PAGE)

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
        self.assertEqual(self.stories[0]['comments'], 56)
        self.assertEqual(self.stories[10]['comments'], 1)

        # this story has just the text comments, without any count
        self.assertEqual(self.stories[5]['comments'], -1)
        
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

    def test_get_stories_first_page_cached(self):
        self.rdb.set("/pages/front_page", STORIES_JSON)

        with mock.patch.object(backend, 'update_page') as update_page:
            self.assertEqual(STORIES_JSON, backend.get_stories('front_page'))
            update_page.assert_not_called()

    def test_get_stories_not_cached(self):
        with mock.patch.object(backend, 'update_page', return_value='stories'
                               ) as update_page:
            self.assertEqual('stories', backend.get_stories('front_page'))
            update_page.assert_called_with('/pages/front_page', 'front_page')

    def test_get_stories_other_page_cached(self):
        self.rdb.set("/pages/" + PAGE_ID, STORIES_JSON)

        with mock.patch.object(backend, 'update_page') as update_page:
            self.assertEqual(STORIES_JSON, backend.get_stories(PAGE_ID))
            update_page.assert_not_called()

    def test_get_stories_cached_too_old_gets_update(self):
        self.rdb.set("/pages/" + PAGE_ID, STORIES_JSON)

        self.rdb.set("/pages/%s/updated" % PAGE_ID, seconds_old(31))
        
        with mock.patch.object(backend, 'CACHE_INTERVAL', 30):
            with mock.patch.object(backend, 'update_page') as update_page:
                self.assertEqual(STORIES_JSON, backend.get_stories(PAGE_ID))
                update_page.assert_called_with('/pages/' + PAGE_ID, PAGE_ID)

    def test_get_token(self):
        FNID = "foo42"
        mock_get = mock.Mock(return_value=mock.Mock(
                content='<input name="fnid" value="%s">foobar</input>' % FNID))
        mock_post = mock.Mock(return_value=mock.Mock(
                cookies={'user': 'user_token'}))

        with mock.patch.object(backend.requests, "get", mock_get) as get:
            with mock.patch.object(backend.requests, "post", mock_post) as post:
                token = backend.get_token("test_user", "test_pass")
                get.assert_called_with(backend.HN_LOGIN)
                post.assert_called_with(backend.HN_LOGIN_POST,
                                        data={'u': "test_user",
                                              'p': "test_pass",
                                              'fnid': "foo42"})
                self.assertEqual(token, "user_token")

    def test_get_token_failed_get(self):
        mock_get = mock.Mock(return_value=mock.Mock(
                content='blueberries'))

        with mock.patch.object(backend.logging, "error") as log_error:
            with mock.patch.object(backend.requests, "get", mock_get) as get:
                self.assertRaises(backend.ServerError,
                                  backend.get_token, "test_user", "test_pass")
                self.assertIn("Failed parsing response",
                              log_error.call_args[0][0])
                self.assertIn("blueberries", log_error.call_args[0][0])
                
    def test_post_token_failed_post(self):
        FNID = "foo42"
        mock_get = mock.Mock(return_value=mock.Mock(
                content='<input name="fnid" value="%s">foobar</input>' % FNID))
        mock_post = mock.Mock(return_value=mock.Mock(cookies={}))

        with mock.patch.object(backend.requests, "get", mock_get) as get:
            with mock.patch.object(backend.requests, "post", mock_post) as post:
                with self.assertRaisesRegexp(
                    backend.ClientError, ".*Bad user/password.*") as exc:
                    backend.get_token("bad_user", "bad_pass")

    def test_update_page_not_found(self):
        mock_get = mock.Mock(return_value=mock.Mock(
                text='No such item.'))
        with mock.patch.object(backend.requests, "get", mock_get) as get:
            self.assertRaises(backend.NotFound, backend.update_page,
                              'test_key', 'test_url')
            get.assert_called_with(backend.HN + 'test_url')

    def test_update_page_server_error(self):
        mock_get = mock.Mock(return_value=mock.Mock(
                text='Unexpected weirdness.'))
        with mock.patch.object(backend.requests, "get", mock_get) as get:
            self.assertRaises(backend.ServerError, backend.update_page,
                              'test_key', 'test_url')
            get.assert_called_with(backend.HN + 'test_url')

    def test_update_page(self):
        RESPONSE_TEXT = '<html>good stories</html>'
        mock_get = mock.Mock(return_value=mock.Mock(
                text=RESPONSE_TEXT))
        with mock.patch.object(backend.requests, "get", mock_get) as get:
            with mock.patch.object(backend, "parse_stories",
                                   mock.Mock(return_value=STORIES)) as parse:
                stories_json = backend.update_page("test_key", "test_url")
                get.assert_called_with(backend.HN + "test_url")
                parse.assert_called_with(RESPONSE_TEXT)
                self.assertEqual(self.rdb.get("test_key"), STORIES_JSON)
