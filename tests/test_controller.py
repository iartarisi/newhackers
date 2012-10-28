import unittest

import mock
import redis

from newhackers import config, controller
from fixtures import PAGE_ID, STORIES_JSON
from utils import seconds_old


class ControllerTest(unittest.TestCase):
    def setUp(self):
        self.rdb = controller.rdb = redis.Redis(db=13)

    def tearDown(self):
        self.rdb.flushdb()

    def test_cache_first_page_cached(self):
        self.rdb.set("test_key", STORIES_JSON)

        with mock.patch.object(controller, 'update_page') as update_page:
            self.assertEqual(STORIES_JSON,
                             controller._get_cache('test_key', 'test_item'))
            update_page.assert_not_called()

    def test_cache_not_cached(self):
        with mock.patch.object(controller, 'update_page', return_value='stories'
                               ) as update_page:
            self.assertEqual('stories',
                             controller._get_cache('test_key', 'test_item'))
            update_page.assert_called_with('test_key', 'test_item')

    def test_cache_other_page_cached(self):
        self.rdb.set("test_key", STORIES_JSON)

        with mock.patch.object(controller, 'update_page') as update_page:
            update_page.assert_not_called()
            self.assertEqual(STORIES_JSON,
                             controller._get_cache('test_key', 'test_item'))

    def test_cache_cached_too_old_gets_update(self):
        self.rdb.set('test_key', STORIES_JSON)

        self.rdb.set("/test_key/updated", seconds_old(31))

        with mock.patch.object(config, 'CACHE_INTERVAL', 30):
            with mock.patch.object(controller.tasks.update, 'delay') as update:
                self.assertEqual(STORIES_JSON,
                                 controller._get_cache('test_key', 'test_item'))
                update.assert_called_with('test_key', 'test_item')

    def test_get_comments(self):
        with mock.patch.object(controller, '_get_cache') as get_cache:
            controller.get_comments('test_item')
            get_cache.assert_called_with('/comments/test_item',
                                         'item?id=test_item')

    def test_get_stories(self):
        with mock.patch.object(controller, '_get_cache') as get_cache:
            controller.get_stories('test_id')
            get_cache.assert_called_with('/pages/test_id', 'test_id')

