from flask import json

FRONT_PAGE = "tests/fixtures/front_page.html"
COMMENTS = "tests/fixtures/comments.html"
NO_COMMENTS = "tests/fixtures/no_comments.html"
ASK_COMMENTS = "tests/fixtures/ask_comments.html"
STORIES = {'more': "4AVKeJz9TP",  # this is tied to the current front_page.html
           'stories': [{u'title': u"I sooo don't like Apple anymore",
                        u'link': u"http://iwoz.woo",
                        u'comments': u"1337",
                        u'score': u"42",
                        u'time': u"1350901062.0",
                        u'author': u"woz"},
                       {u'title': u"Work for my startup for free",
                        u'link': u"item?id=1111",
                        u'time': 1351333328.0,
                        u'score': None,
                        u'author': None,
                        u'comments': None}]}
STORIES_JSON = json.dumps(STORIES)
PAGE_ID = "qwerty54"
