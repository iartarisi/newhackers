from datetime import datetime, timedelta
import json
import re
import time

from bs4 import BeautifulSoup
from parsedatetime import parsedatetime as pdt
import redis


CACHE_INTERVAL = 60  # seconds
STORIES_PER_PAGE = 30

cal = pdt.Calendar()
rdb = redis.Redis(8)


class ClientError(Exception): pass
class ServerError(Exception): pass


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

    allowed_age = timedelta(seconds=CACHE_INTERVAL)
    if age < allowed_age:
        return False
    else:
        return True

def get_stories(page=None):
    """Return a page of stories as a list of story dicts

    Returns None if the page was not found

    """
    key = ("/story/" + page) if page else "/story"

    try:
        stories = rdb[key]
    except KeyError:
        stories = update_page(page)
        return json.loads(stories)

    if too_old(key):
        # background task
        update_page(page)
    
    return json.loads(stories)

    
def parse_stories(page):
    """Parse stories from an HN stories page

    :page: an HTML document which contains 30 stories

    Returns a list of dicts. e.g.

    [{'title': "I sooo don't like Apple anymore",
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

      ...]

    """
    soup = BeautifulSoup(page)

    # There are STORIES_PER_PAGE HN Stories per page
    # each story link is divided into two <td>s:
    # - the number of the story (first story on the first page is 1.)
    # - the title and link of the story
    # The title and the link don't have a valign attribute
    # Finally there is a 'More' link to the next page of stories.
    titles = soup.find_all("td", "title", valign=False)
    more_link = titles.pop(-1)
    assert len(titles) == STORIES_PER_PAGE

    stories = [{'title': title.text.strip(),
                'link': title.find("a")["href"]}
               for title in titles]

    # Some other data about each submission is stored in <td
    # class="subtext"> elements
    metadata = soup.find_all("td", "subtext")
    assert len(metadata) == STORIES_PER_PAGE

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
                stories[s]['comments'] = int(re.search(
                    "(\d+)\s+comments?", meta.text).group(1))
        else:  # Jobs post
            stories[s]['time'] = _decode_time(meta.text.strip())
            stories[s]['comments'] = None
            stories[s]['score'] = None
            stories[s]['author'] = None
    return stories

def _decode_time(timestamp):
    """Decode time from a relative timestamp to a localtime float"""
    return time.mktime(cal.parse(timestamp)[0])
