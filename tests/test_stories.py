import unittest

import mock
import redis

from newhackers import config, controller
from fixtures import PAGE_ID, STORIES_JSON
from utils import seconds_old


class StoriesTest(unittest.TestCase):
    def setUp(self):
        self.rdb = controller.rdb = redis.Redis(db=13)

    def tearDown(self):
        self.rdb.flushdb()

    def test_get_stories_first_page_cached(self):
        self.rdb.set("/pages/front_page", STORIES_JSON)

        with mock.patch.object(controller, 'update_page') as update_page:
            self.assertEqual(STORIES_JSON, controller.get_stories('front_page'))
            update_page.assert_not_called()

    def test_get_stories_not_cached(self):
        with mock.patch.object(controller, 'update_page', return_value='stories'
                               ) as update_page:
            self.assertEqual('stories', controller.get_stories('front_page'))
            update_page.assert_called_with('/pages/front_page', 'front_page')

    def test_get_stories_other_page_cached(self):
        self.rdb.set("/pages/" + PAGE_ID, STORIES_JSON)

        with mock.patch.object(controller, 'update_page') as update_page:
            update_page.assert_not_called()
            self.assertEqual(STORIES_JSON, controller.get_stories(PAGE_ID))

    def test_get_stories_cached_too_old_gets_update(self):
        self.rdb.set("/pages/" + PAGE_ID, STORIES_JSON)

        self.rdb.set("/pages/%s/updated" % PAGE_ID, seconds_old(31))

        with mock.patch.object(config, 'CACHE_INTERVAL', 30):
            with mock.patch.object(controller, 'update_page') as update_page:
                self.assertEqual(STORIES_JSON, controller.get_stories(PAGE_ID))
                update_page.assert_called_with('/pages/' + PAGE_ID, PAGE_ID)
