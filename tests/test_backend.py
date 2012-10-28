import unittest

import mock

from newhackers import backend, config
from newhackers.exceptions import ClientError
from tests.fixtures import COMMENTS, COMMENTS_JSON, STORIES, STORIES_JSON
from tests.utils import seconds_old, rdb


class BackendTest(unittest.TestCase):
    def setUp(self):
        backend.rdb = rdb

    def tearDown(self):
        rdb.flushdb()

    def test_time_too_old(self):
        with mock.patch.object(config, 'CACHE_INTERVAL', 30):
            rdb.set("my-item/updated", seconds_old(30))
            self.assertTrue(backend.too_old("my-item"))

            rdb.set("my-item/updated", seconds_old(29))
            self.assertFalse(backend.too_old("my-item"))

    def test_time_too_old_key_doesnt_exist(self):
        self.assertTrue(backend.too_old("bogus-item"))

    def test_update_page_not_found(self):
        mock_get = mock.Mock(return_value=mock.Mock(
                text='No such item.'))
        with mock.patch.object(backend.requests, "get", mock_get) as get:
            self.assertRaises(backend.NotFound, backend.update_page,
                              '/pages/test_key', 'test_url')
            get.assert_called_with(config.HN + 'test_url')

    def test_update_page_server_error(self):
        mock_get = mock.Mock(return_value=mock.Mock(
                text='Unexpected weirdness.'))
        with mock.patch.object(backend.requests, "get", mock_get) as get:
            self.assertRaises(backend.ServerError, backend.update_page,
                              '/pages/test_key', 'test_url')
            get.assert_called_with(config.HN + 'test_url')

    def test_update_page_stories(self):
        RESPONSE_TEXT = '<html>good stories</html>'
        mock_get = mock.Mock(return_value=mock.Mock(
                text=RESPONSE_TEXT))
        with mock.patch.object(backend.requests, "get", mock_get) as get:
            with mock.patch.object(backend, "parse_stories",
                                   mock.Mock(return_value=STORIES)) as parse:
                stories_json = backend.update_page("/pages/test_key", "test_url")
                get.assert_called_with(config.HN + "test_url")
                parse.assert_called_with(RESPONSE_TEXT)
                self.assertEqual(stories_json, STORIES_JSON)

    def test_update_page_comments(self):
        RESPONSE_TEXT = '<html>good stories</html>'
        mock_get = mock.Mock(return_value=mock.Mock(
                text=RESPONSE_TEXT))
        with mock.patch.object(backend.requests, "get", mock_get) as get:
            with mock.patch.object(backend, "parse_comments",
                                   mock.Mock(return_value=COMMENTS)) as parse:
                coms_json = backend.update_page("/comments/test_key", "test_url")
                get.assert_called_with(config.HN + "test_url")
                parse.assert_called_with(RESPONSE_TEXT)
                self.assertEqual(coms_json, COMMENTS_JSON)

    def test_hn_get_cant_make_vote(self):
        mock_get = mock.Mock(return_value=mock.Mock(
                text="Can't make that vote."))
        with mock.patch.object(backend.requests, "get", mock_get) as get:
            self.assertRaises(ClientError, backend.hn_get,
                              "vote-for-me", cookies={'user': 'me'})
            get.assert_called_with(config.HN + "vote-for-me",
                                   cookies={'user': 'me'})
    
