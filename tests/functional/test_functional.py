import json
import unittest

from newhackers import app, backend


TEST_USER = 'trichechus'
TEST_PASS = 'manatus'


class FunctionalTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

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
