#!/usr/bin/env python

import urllib2

from bs4 import BeautifulSoup

# this is a nice page for tests (stories 91 to 120) which also contains
# an Ask HN link and a hiring link
HN_STORIES = "http://news.ycombinator.org/x?fnid=yRifb5Grj7"

def create_fixtures():
    soup = BeautifulSoup(urllib2.urlopen(HN_STORIES))

    with open("fixtures/front_page.html", "w") as f:
        f.write(soup.prettify().encode('utf-8'))

if __name__ == "__main__":
    create_fixtures()
