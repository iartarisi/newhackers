import json
import random
import unittest

from newhackers import app, backend, config
from tests.utils import rdb


TEST_USER = 'trichechus'
TEST_PASS = 'manatus'


class FunctionalTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        backend.rdb = rdb

    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        rdb.flushdb()

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
            ['time', 'comments_no', 'score', 'author', 'title', 'link'],
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
        self.assertItemsEqual(
            ['time', 'comments_no', 'score', 'author', 'title', 'link'],
            r_data['stories'][0])

    def test_comments(self):
        resp = self.app.get('/comments/4706103')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        r_data = json.loads(resp.data)
        self.assertItemsEqual(
            ['title', 'link', 'score', 'author', 'time',
             'comments_no', 'comments'],
            r_data)
        for comment in r_data['comments']:
            self.assertItemsEqual(['author', 'body', 'link', 'time'], comment)

    def test_vote(self):
        # this is more complicated, we need a token and an item we
        # haven't voted on yet

        # get a random story from the Ask HN page and we cross our
        # fingers that we don't get a collision next time we run this
        # test because we can't vote on the same item twice
        resp = self.app.get('/ask/')
        stories = json.loads(resp.data)['stories']
        item = random.choice(stories)['link'].split('item?id=')[1]

        # get our test user's token
        resp = self.app.post('/get_token', data={'user': TEST_USER,
                                                 'password': TEST_PASS})
        token = json.loads(resp.data)['token']

        # vote
        resp = self.app.post('/vote', data={'token': token,
                                            'direction': 'up',
                                            'item': item})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data), {'vote': 'Success'})
