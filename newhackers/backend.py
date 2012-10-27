from datetime import datetime, timedelta
import json
import re
import time

from bs4 import BeautifulSoup
from parsedatetime import parsedatetime as pdt
import redis
import requests

from newhackers import config
from newhackers.exceptions import ServerError, NotFound


cal = pdt.Calendar()
rdb = redis.Redis(db=8)


def too_old(key):
    """Check if an item in the redis database is too old

    We're following a convention which says that a last_updated
    timestamp is stored in 'key/updated'. If we can't find the
    timestamp, then the item is too old, so we return True.

    We check if this timestamp (a float of seconds since the epoch) is
    too old according to CACHE_INTERVAL

    """
    try:
        updated = float(rdb[key + "/updated"])
    except KeyError:
        return True
    else:
        age = datetime.now() - datetime.fromtimestamp(updated)

    allowed_age = timedelta(seconds=config.CACHE_INTERVAL)
    if age < allowed_age:
        return False
    else:
        return True


def update_page(db_key, url):
    """Updates a page in the database

    The page is downloaded, parsed and then stored in the database as a
    JSON string. This string is also returned by the function.
    
    :db_key: a redis string of the key where the stories page will be stored
    :url: the HN URL path where the page will be downloaded from

    Raises NotFound when the page could not be found on the remote
    server or ServerError in case the server returned a response that we
    could not understand. (It's still the server's fault because it
    doesn't even have sensible status codes)

    """
    res = requests.get(config.HN + url)
    # HN is ignorant of HTTP status codes
    # all errors seem to be plain text sentences
    if res.text in ['No such item.', 'Unknown.']:
        raise NotFound

    if not res.text.startswith("<html>"):
        raise ServerError("HN is weird.")

    stories = parse_stories(res.text)
    stories_json = json.dumps(stories)

    rdb[db_key] = stories_json

    return stories_json


def parse_stories(page):
    """Parse stories from an HN stories page

    :page: an HTML document which contains 30 stories

    Returns a dict with a more link and a list of stories dicts. E.g.

    {'more': '4AVKeJz9TP',
     'stories': [
          {'title': "I sooo don't like Apple anymore",
           'link': "http://iwoz.woo",
           'comments': 1337,
           'score': 42,
           'time': 1350901062.0,
           'author': 'woz'},

          {'title': "Work for my startup for free",
           'link': "item?id=1111",
           'time': 1351333328.0,
           'score': None,
           'author': None,
           'comments': None},

           ...]}

    """
    soup = BeautifulSoup(page)

    more, stories = _parse_links(soup)
    assert len(stories) == config.STORIES_PER_PAGE

    subtexts = _parse_subtexts(soup)
    assert len(subtexts) == config.STORIES_PER_PAGE

    for story, subtext in zip(stories, subtexts):
        story.update(subtext)
    
    return dict(stories=stories, more=more)


def _parse_links(soup):
    """Return a more link and a list of title/link dicts

    Returns e.g.

    ('RDXC3fdF',
     [{'title': "I sooo don't like Apple anymore",
       'link': "http://iwoz.woo"},
      {'title': "Work for my startup for free",
       'link': "item?id=1111"}
       ...]
    )

    """
    # each story link is divided into two <td>s:
    # - the number of the story (first story on the first page is 1.)
    # - the title and link of the story
    # The title and the link don't have a valign attribute
    # Finally there is a 'More' link to the next page of stories.
    titles = soup.find_all("td", "title", valign=False)
    more = _extract_more(titles.pop(-1))

    stories = [{'title': title.text.strip(),
                'link': title.find("a")["href"]}
               for title in titles]

    return more, stories


def _parse_subtexts(soup):
    """Returns a list of dictionaries with stories metadata

    Returns e.g.
    
     [{'comments': 1337,
       'score': 42,
       'time': 1350901062.0,
       'author': 'woz'},

      {'time': 1351333328.0,
       'score': None,
       'author': None,
       'comments': None},
      ...]

    Returns None if no comments were found

    """
    # Some other data about each submission is stored in <td
    # class="subtext"> elements
    metadata = soup.find_all("td", "subtext")
    if not metadata:
        return None

    stories = [{} for i in range(len(metadata))]

    # The content of the <td class="subtext"> differs. There are three classes:
    # 1. normal stories with all the metadata (Ask HNs included)
    # 2. stories without comments - contain a discuss link instead of
    # number of comments
    # 3. Jobs - no comments, no author, no score
    for s, meta in enumerate(metadata):
        # Jobs post
        if 'point' in meta.text:
            story_time = re.search('\s+(.*?)\s+\|', meta.text).group(1)
            stories[s]['time'] = _decode_time(story_time)
            stories[s]['score'] = int(re.search(
                    "(\d+)\s+points?", meta.text).group(1))
            stories[s]['author'] = meta.a.text.strip()
            if 'discuss' in meta.text:  # Zero comments
                stories[s]['comments'] = 0
            else:
                try:
                    stories[s]['comments'] = int(re.search(
                            "(\d+)\s+comments?", meta.text).group(1))
                except AttributeError:
                    # I found an instance where there was just the text
                    # 'comments', without any count. I'm assuming that
                    # even stranger things could happen
                    stories[s]['comments'] = -1

        else:  # Jobs post
            stories[s]['time'] = _decode_time(meta.text.strip())
            stories[s]['comments'] = None
            stories[s]['score'] = None
            stories[s]['author'] = None

    return stories


def _extract_more(more_soup):
    """Extract a page identifier from the <a> element in a BeautifulSoup"""
    return more_soup.find("a")['href'].split('fnid=')[-1]


def _decode_time(timestamp):
    """Decode time from a relative timestamp to a localtime float"""
    return time.mktime(cal.parse(timestamp)[0])


