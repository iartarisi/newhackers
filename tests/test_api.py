import unittest

from flask import json
import mock
import redis
from werkzeug.exceptions import NotFound

from newhackers import app, auth, backend, exceptions, items, votes
from fixtures import COMMENTS_JSON, ITEM_ID, PAGE_ID, STORIES_JSON


class JSONApiTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.rdb = backend.rdb = redis.Redis(db=13)

    def tearDown(self):
        self.rdb.flushdb()

    def test_404_json(self):
        with app.test_request_context(
            path='/not-found', headers=[('Accept', 'application/json')]):
            self.assertRaises(NotFound, app.dispatch_request)
            response = app.full_dispatch_request()
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(json.loads(response.data),
                             {'error': "404: Not Found"})

    def test_stories_default(self):
        with mock.patch.object(items, "get_stories",
                               return_value=STORIES_JSON) as get_stories:
            response = self.app.get('/stories/')
            get_stories.assert_called_with('')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.data, STORIES_JSON)

    def test_ask_default(self):
        with mock.patch.object(items, "get_stories",
                               return_value=STORIES_JSON) as get_stories:
            response = self.app.get('/ask/')
            get_stories.assert_called_with('ask')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.data, STORIES_JSON)

    def test_stories_specific(self):
        with mock.patch.object(items, "get_stories",
                               return_value=STORIES_JSON) as get_stories:
            response = self.app.get('/stories/' + PAGE_ID)
            get_stories.assert_called_with(PAGE_ID)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.data, STORIES_JSON)

    def test_stories_404(self):
        with mock.patch.object(items, "get_stories",
                               side_effect=exceptions.NotFound
                               ) as get_stories:
            response = self.app.get('/stories/not-found')
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.content_type, 'application/json')
            get_stories.assert_called_with('not-found')

    def test_comments(self):
        with mock.patch.object(items, "get_comments",
                               return_value=COMMENTS_JSON) as get_comments:
            response = self.app.get('/comments/' + str(ITEM_ID))
            get_comments.assert_called_with(ITEM_ID)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.data, COMMENTS_JSON)

    def test_comments_404(self):
        with mock.patch.object(items, "get_comments",
                               side_effect=exceptions.NotFound
                               ) as get_comments:
            response = self.app.get('/comments/404')
            self.assertEqual(response.status_code, 404)
            get_comments.assert_called_with(404)

    def test_get_token(self):
        with mock.patch.object(auth, "get_token", return_value="token123"
                               ) as get_token:
            response = self.app.post('/get_token',
                                     data={'user': 'test_user',
                                           'password': 'test_pass'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data),
                             {'token': 'token123'})
            get_token.assert_called_with('test_user', 'test_pass')

    def test_get_token_403(self):
        with mock.patch.object(auth, "get_token",
                               side_effect=exceptions.ClientError('Evil Error')
                               ) as get_token:
            response = self.app.post('/get_token',
                                     data={'user': 'test_user',
                                           'password': 'test_pass'})
            get_token.assert_called_with('test_user', 'test_pass')
            self.assertEqual(response.status_code, 403)
            self.assertEqual(json.loads(response.data),
                             {'error': 'Evil Error'})

    def test_get_token_500(self):
        with mock.patch.object(auth, "get_token",
                               side_effect=exceptions.ServerError('Evil Error')
                               ) as get_token:
            response = self.app.post('/get_token',
                                     data={'user': 'test_user',
                                           'password': 'test_pass'})
            get_token.assert_caleed_with('test_user', 'test_pass')
            self.assertEqual(response.status_code, 500)
            self.assertEqual(json.loads(response.data),
                             {'error': 'Evil Error'})

    def test_vote(self):
        with mock.patch.object(votes, "vote", return_value=True) as vote:
            response = self.app.post('/vote',
                                     data={'token': 'token1',
                                           'direction': 'up',
                                           'item': '12345'})
            vote.assert_called_with('token1', 'up', '12345')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data),
                             {'vote': 'Success'})

    def test_vote_failed(self):
        with mock.patch.object(votes, "vote", return_value=False) as vote:
            response = self.app.post('/vote',
                                     data={'token': 'token1',
                                           'direction': 'up',
                                           'item': '12345'})
            vote.assert_called_with('token1', 'up', '12345')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data),
                             {'vote': 'Fail'})
