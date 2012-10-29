# -*- coding: utf-8 -*-
# This file is part of newhackers.
# Copyright (c) 2012 Ionuț Arțăriși

# cuZmeură is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.

# cuZmeură is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with cuZmeură. If not, see <http://www.gnu.org/licenses/>.

import unittest

import mock
import redis

from newhackers import auth, config


class TokenTest(unittest.TestCase):
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
