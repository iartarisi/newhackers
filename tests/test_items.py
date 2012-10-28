import unittest

import mock

from newhackers import config, items
from tests.fixtures import PAGE_ID, STORIES_JSON
from tests.utils import seconds_old, rdb


class ItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        items.rdb = rdb

    def tearDown(self):
        rdb.flushdb()

    def test_cache_first_page_cached(self):
        rdb.set("test_key", STORIES_JSON)

        with mock.patch.object(items, 'update_page') as update_page:
            self.assertEqual(STORIES_JSON,
                             items._get_cache('test_key', 'test_item'))
            update_page.assert_not_called()

    def test_cache_not_cached(self):
        with mock.patch.object(items, 'update_page', return_value='stories'
                               ) as update_page:
            self.assertEqual('stories',
                             items._get_cache('test_key', 'test_item'))
            update_page.assert_called_with('test_key', 'test_item')

    def test_cache_other_page_cached(self):
        rdb.set("test_key", STORIES_JSON)

        with mock.patch.object(items, 'update_page') as update_page:
            update_page.assert_not_called()
            self.assertEqual(STORIES_JSON,
                             items._get_cache('test_key', 'test_item'))

    def test_cache_cached_too_old_gets_update(self):
        rdb.set('test_key', STORIES_JSON)

        rdb.set("/test_key/updated", seconds_old(31))

        with mock.patch.object(config, 'CACHE_INTERVAL', 30):
            with mock.patch.object(items.tasks.update, 'delay') as update:
                self.assertEqual(STORIES_JSON,
                                 items._get_cache('test_key', 'test_item'))
                update.assert_called_with('test_key', 'test_item')

    def test_get_comments(self):
        with mock.patch.object(items, '_get_cache') as get_cache:
            items.get_comments('test_item')
            get_cache.assert_called_with('/comments/test_item',
                                         'item?id=test_item')

    def test_get_stories(self):
        with mock.patch.object(items, '_get_cache') as get_cache:
            items.get_stories('test_id')
            get_cache.assert_called_with('/pages/test_id', 'test_id')

