from datetime import datetime, timedelta
import time
import unittest

from bs4 import BeautifulSoup

from newhackers import config, parsers
from newhackers.utils import valid_url
from tests.fixtures import (COMMENTS_PAGE, NO_COMMENTS, ASK_COMMENTS,
                            FRONT_PAGE, STORIES)


class CommentsTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        with open(COMMENTS_PAGE) as f:
            self.comments = parsers.parse_comments(f.read())
        with open(NO_COMMENTS) as f:
            self.no_comments = parsers.parse_comments(f.read())
        with open(ASK_COMMENTS) as f:
            self.ask_comments = parsers.parse_comments(f.read())

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

    def test_parse_comments_no_comments(self):
        self.assertIsNone(parsers._parse_comments(BeautifulSoup()))
        
    def test_parse_comments_deleted(self):
        soup = BeautifulSoup("<span class='comhead'>Story title</span>"
                             "<span class='comhead'></span>"
                             "<span class='comment'>I comment</span>")
        self.assertListEqual([], parsers._parse_comments(soup))

    def _pop_time(self, comments):
        """Remote the 'time' item since it's relative and it messes the tests"""
        coms = comments.copy()
        self.assertIsInstance(coms.pop('time'), float)
        return coms


class ParseStoriesTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        with open(FRONT_PAGE) as f:
            self.stories, self.more = parsers.parse_stories(f.read()).values()

    def test_parse_stories_right_length(self):
        self.assertEqual(len(self.stories), config.STORIES_PER_PAGE)

    def test_parse_stories_more_id(self):
        self.assertEqual(self.more, STORIES['more'])

    def test_parse_stories_titles_are_different(self):
        diff_titles = set(d['title'] for d in self.stories)
        # NB Stories aren't guaranteed to have different names in
        # real-life HN, but we got a lucky fixture
        self.assertEqual(len(diff_titles), config.STORIES_PER_PAGE)

    def test_parse_stories_title(self):
        self.assertEqual(self.stories[0]['title'], 'Dummy Title')

    def test_parse_stories_urls_are_different(self):
        diff_urls = set(s['link'] for s in self.stories)
        self.assertEqual(len(diff_urls), config.STORIES_PER_PAGE)

    def test_parse_stories_urls_are_valid(self):
        for story in self.stories:
            try:
                self.assertTrue(valid_url(story['link']),
                                "URL is invalid: " + story['link'])
            except AssertionError:
                # Ask HN isn't a valid url, but it's still good
                if not story['link'].startswith("item?id="):
                    raise

    def test_parse_stories_time(self):
        # first item is dated 22 hours ago
        self.assertAlmostEqual(
            self.stories[0]['time'],
            time.mktime((datetime.now() - timedelta(hours=22)).timetuple()),
            delta=1)

        # 2 day ago
        self.assertAlmostEqual(
            self.stories[1]['time'],
            time.mktime((datetime.now() - timedelta(days=2)).timetuple()),
            delta=1)

        # jobs post is dated one day ago
        self.assertAlmostEqual(
            self.stories[18]['time'],
            time.mktime((datetime.now() - timedelta(days=1)).timetuple()),
            delta=1)

    def test_parse_stories_comments(self):
        self.assertEqual(self.stories[0]['comments_no'], 56)
        self.assertEqual(self.stories[10]['comments_no'], 1)

        # this story has just the text comments, without any count
        self.assertEqual(self.stories[5]['comments_no'], -1)

        # Jobs
        self.assertIsNone(self.stories[19]['comments_no'])
        # Ask
        self.assertEqual(self.stories[18]['comments_no'], 65)

        # discuss
        self.assertEqual(self.stories[15]['comments_no'], 0)

    def test_parse_stories_points(self):
        self.assertEqual(self.stories[0]['score'], 68)

        # Jobs
        self.assertIsNone(self.stories[19]['score'])
        # Ask HN
        self.assertEqual(self.stories[18]['score'], 118)

    def test_parse_stories_author(self):
        self.assertEqual(self.stories[0]['author'], "kine")

        # Jobs
        self.assertIsNone(self.stories[19]['author'])
        # Ask
        self.assertEqual(self.stories[18]['author'], "DonnyV")

    def test_parse_subtexts_no_comments(self):
        self.assertIsNone(parsers._parse_subtexts(BeautifulSoup()))
