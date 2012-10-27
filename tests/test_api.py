import unittest

from flask import json
import mock
import redis
from werkzeug.exceptions import NotFound

from newhackers import app, backend, token
from fixtures import PAGE_ID, STORIES, STORIES_JSON


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
        with mock.patch.object(backend, "get_stories",
                               return_value=STORIES_JSON) as get_stories:
            response = self.app.get('/stories/')
            get_stories.assert_called_with('')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.data, STORIES_JSON)

    def test_ask_default(self):
        with mock.patch.object(backend, "get_stories",
                               return_value=STORIES_JSON) as get_stories:
            response = self.app.get('/ask/')
            get_stories.assert_called_with('ask')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.data, STORIES_JSON)

    def test_stories_specific(self):
        with mock.patch.object(backend, "get_stories",
                               return_value=STORIES_JSON) as get_stories:
            response = self.app.get('/stories/' + PAGE_ID)
            get_stories.assert_called_with(PAGE_ID)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.data, STORIES_JSON)

    def test_stories_404(self):
        with mock.patch.object(backend, "get_stories",
                               side_effect=backend.NotFound
                               ) as get_stories:
            response = self.app.get('/stories/not-found')
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.content_type, 'application/json')
            get_stories.assert_called_with('not-found')
            
    def test_get_token(self):
        with mock.patch.object(token, "get_token", return_value="token123"
                               ) as get_token:
            response = self.app.post('/get_token',
                                     data={'user': 'test_user',
                                           'password': 'test_pass'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data),
                             {'token': 'token123'})
            get_token.assert_called_with('test_user', 'test_pass')
            
    def test_get_token_403(self):
        with mock.patch.object(token, "get_token",
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
        with mock.patch.object(token, "get_token",
                               side_effect=exceptions.ServerError('Evil Error')
                               ) as get_token:
            response = self.app.post('/get_token',
                                     data={'user': 'test_user',
                                           'password': 'test_pass'})
            get_token.assert_caleed_with('test_user', 'test_pass')
            self.assertEqual(response.status_code, 500)
            self.assertEqual(json.loads(response.data),
                             {'error': 'Evil Error'})
