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

from newhackers import votes
from newhackers.exceptions import ClientError
from tests.fixtures import COMMENTS_PAGE, FRONT_PAGE


STORY_ID = '4698446'
COMMENT_ID = '4705841'


class VotesTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        with open(COMMENTS_PAGE) as f:
            self.comments = f.read()
        with open(FRONT_PAGE) as f:
            self.front_page = f.read()

    def test__find_vote_link_story_up(self):
        self.assertEqual(votes._find_vote_link(self.front_page, STORY_ID, 'up'),
                         u'vote?for=4698446&dir=up&whence=%2f%78%3f%66%6e%69%64%3d%79%52%69%66%62%35%47%72%6a%37')

    def test__find_vote_link_story_down(self):
        self.assertIsNone(
            votes._find_vote_link(self.front_page, STORY_ID, 'down'))

    def test__find_vote_link_comment_up(self):
        self.assertEqual(votes._find_vote_link(self.comments, COMMENT_ID, 'up'),
                         u'vote?for=4705841&dir=up&whence=%69%74%65%6d%3f%69%64%3d%34%37%30%35%30%36%37')

    def test__find_vote_link_commen_down(self):
        self.assertIsNone(
            votes._find_vote_link(self.comments, COMMENT_ID, 'down'))

    def test_vote_no_link(self):
        with mock.patch.object(votes, "hn_get") as hn_get:
            with mock.patch.object(votes, "_find_vote_link",
                                   return_value=None) as find_vote:
                self.assertRaises(ClientError, votes.vote,
                                  "token1", "up", "1234")
                hn_get.assert_called_with('item?id=1234',
                                          cookies={'user': 'token1'})
                find_vote.assert_called_with(hn_get().text, "1234", "up")

    def test_vote(self):
        mock_get = mock.Mock(return_value=mock.Mock(
                text=""))
        with mock.patch.object(votes, "hn_get", mock_get) as hn_get:
            with mock.patch.object(votes, "_find_vote_link",
                                   return_value="good_vote_link") as find_vote:
                self.assertTrue(votes.vote("token1", "up", "1234"))
                hn_get.assert_any_call('item?id=1234',
                                          cookies={'user': 'token1'})
                hn_get.assert_any_call('good_vote_link',
                                       cookies={'user': 'token1'})
                find_vote.assert_called_with(hn_get().text, "1234", "up")

    def test_vote_failed(self):
        mock_get = mock.Mock(return_value=mock.Mock(
                text="fail"))
        with mock.patch.object(votes, "hn_get", mock_get) as hn_get:
            with mock.patch.object(votes, "_find_vote_link",
                                   return_value="good_vote_link") as find_vote:
                self.assertIsNone(votes.vote("token1", "up", "1234"))
                hn_get.assert_any_call('item?id=1234',
                                       cookies={'user': 'token1'})
                hn_get.assert_any_call('good_vote_link',
                                       cookies={'user': 'token1'})
                find_vote.assert_called_with(hn_get().text, "1234", "up")

    def test_vote_wrong_direction(self):
        self.assertRaises(ClientError, votes.vote,
                          "token", "left", "item")
