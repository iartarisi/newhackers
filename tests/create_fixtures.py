#!/usr/bin/env python

import urllib2

from bs4 import BeautifulSoup


def download(link, output):
    soup = BeautifulSoup(urllib2.urlopen(link))

    with open("fixtures/" + output, "w") as f:
        f.write(soup.prettify().encode('utf-8'))
    print("Downloaded %s to %s." % (link, output))


def front_page():
    # this is a nice page for tests (stories 91 to 120) which also contains
    # an Ask HN link and a hiring link
    # XXX this link expires
    download("http://news.ycombinator.org/x?fnid=yRifb5Grj7", "front_page.html")

        
def normal_comments():
    # a normal page with an outside link and comments
    download("http://news.ycombinator.org/item?id=4705067", "comments.html")


def ask_hn_comments():
    download("http://news.ycombinator.org/item?id=4655144", "ask_comments.html")


def no_comments():
    # an HN submission without comments
    download("http://news.ycombinator.org/item?id=4706068", "no_comments.html")


if __name__ == "__main__":
    normal_comments()
    ask_hn_comments()
    no_comments()
