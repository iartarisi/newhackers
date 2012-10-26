import unittest

from flask import json
import redis
from werkzeug.exceptions import NotFound

from newhackers import app, backend


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
