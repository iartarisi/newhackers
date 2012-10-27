import json
import unittest

import redis

from newhackers import app, backend, config


TEST_USER = 'trichechus'
TEST_PASS = 'manatus'


class FunctionalTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        backend.rdb = redis.Redis(db=13)

    def test_get_token(self):
        resp = self.app.post('/get_token', data={'user': TEST_USER,
                                                 'password': TEST_PASS})
        self.assertEqual(resp.status_code, 200)
        r_data = json.loads(resp.data)
        self.assertIn('token', r_data)
        self.assertLessEqual(len(r_data['token']), 10)

    def test_get_token_bad_creds(self):
        resp = self.app.post('/get_token',
                             data={'user': 'pg',
                                   'password': 'not_pgs_real_password'})
        self.assertEqual(resp.status_code, 403)
        r_data = json.loads(resp.data)
        self.assertIn('error', r_data)
        self.assertIn('Authentication failed', r_data['error'])

    def test_front_page(self):
        resp = self.app.get('/stories/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        r_data = json.loads(resp.data)
        self.assertItemsEqual(['more', 'stories'], r_data)
        self.assertEqual(len(r_data['stories']), config.STORIES_PER_PAGE)
        self.assertItemsEqual(
            ['time', 'comments', 'score', 'author', 'title', 'link'],
            r_data['stories'][0])

    def test_not_found_page(self):
        resp = self.app.get('/stories/NOT_FOUND')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.content_type, 'application/json')
        r_data = json.loads(resp.data)
        self.assertEqual(r_data, {'error': '404: Not Found'})

    def test_ask_hn(self):
        resp = self.app.get('/ask/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        r_data = json.loads(resp.data)
        self.assertItemsEqual(('more', 'stories'), r_data)
        for story in r_data['stories']:
            self.assertTrue(story['link'].startswith('item?id='))
