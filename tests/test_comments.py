import unittest

from newhackers import backend
from fixtures import COMMENTS, NO_COMMENTS, ASK_COMMENTS


class CommentsTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        with open(COMMENTS) as f:
            self.comments = backend.parse_comments(f.read())
        with open(NO_COMMENTS) as f:
            self.no_comments = backend.parse_comments(f.read())
        with open(ASK_COMMENTS) as f:
            self.ask_comments = backend.parse_comments(f.read())

    def test_parse_comments_returns(self):
        self.assertItemsEqual(
            ['title', 'link', 'score', 'author', 'time',
             'comments_no', 'comments'],
            self.comments)

    def test_parse_ask_comments_length(self):
        # our fixtures contain the special case where the comments
        # number isn't specified in the submission head
        self.assertEqual(self.ask_comments['comments_no'], -1)

    def test_parse_comments_length(self):
        self.assertEqual(self.comments['comments_no'],
                         len(self.comments['comments']))

    def test_parse_no_comments(self):
        self.assertItemsEqual(
            ['title', 'link', 'score', 'author', 'time',
             'comments_no', 'comments'],
            self.no_comments)

        self.assertEqual(self._pop_time(self.no_comments), {
                'author': u'twapi',
                'comments': [],
                'comments_no': 0,
                'link': u'http://browserfame.com/922/dns-prefetch-opera',
                'score': 1,
                'title': u'DNS Prefetching on Hovering Links in Opera'})

    def test_parse_ask_comments(self):
        self.assertItemsEqual(
            ['title', 'link', 'score', 'author', 'time',
             'comments_no', 'comments'],
            self.ask_comments)

    def test_parse_comments_first_comment(self):
        self.assertEqual(self._pop_time(self.comments['comments'][0]),
                         {'author': u'seldo',
                          'body': 'TEST! TEST! TEST!',
                          'link': u'4705763'})

    def _pop_time(self, comments):
        """Remote the 'time' item since it's relative and it messes the tests"""
        coms = comments.copy()
        self.assertIsInstance(coms.pop('time'), float)
        return coms


