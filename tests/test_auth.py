import unittest

import mock
import redis

from newhackers import auth, config


class TokenTest(unittest.TestCase):
    def setUp(self):
        self.rdb = auth.rdb = redis.Redis(db=13)

    def tearDown(self):
        self.rdb.flushdb()

    def test_token(self):
        FNID = "foo42"
        mock_get = mock.Mock(return_value=mock.Mock(
                content='<input name="fnid" value="%s">foobar</input>' % FNID))
        mock_post = mock.Mock(return_value=mock.Mock(
                cookies={'user': 'user_token'}))

        with mock.patch.object(auth.requests, "get", mock_get) as get:
            with mock.patch.object(auth.requests, "post", mock_post) as post:
                tok = auth.get_token("test_user", "test_pass")
                get.assert_called_with(config.HN_LOGIN)
                post.assert_called_with(config.HN_LOGIN_POST,
                                        data={'u': "test_user",
                                              'p': "test_pass",
                                              'fnid': "foo42"})
                self.assertEqual(tok, "user_token")

    def test_token_failed_get(self):
        mock_get = mock.Mock(return_value=mock.Mock(
                content='blueberries'))

        with mock.patch.object(auth.logging, "error") as log_error:
            with mock.patch.object(auth.requests, "get", mock_get) as get:
                self.assertRaises(auth.ServerError,
                                  auth.get_token, "test_user", "test_pass")
                self.assertIn("Failed parsing response",
                              log_error.call_args[0][0])
                self.assertIn("blueberries", log_error.call_args[0][2])

    def test_token_failed_post(self):
        FNID = "foo42"
        mock_get = mock.Mock(return_value=mock.Mock(
                content='<input name="fnid" value="%s">foobar</input>' % FNID))
        mock_post = mock.Mock(return_value=mock.Mock(cookies={}))

        with mock.patch.object(auth.requests, "get", mock_get) as get:
            with mock.patch.object(auth.requests, "post", mock_post) as post:
                with self.assertRaisesRegexp(auth.ClientError,
                                             ".*Bad user/password.*") as exc:
                    auth.get_token("bad_user", "bad_pass")
