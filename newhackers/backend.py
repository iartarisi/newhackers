from datetime import datetime, timedelta
import json
import time

import redis
import requests

from newhackers import config
from newhackers.parsers import parse_stories, parse_comments
from newhackers.exceptions import NotFound, ServerError


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
    if res.text in ['No such item.', 'Unknown.', 'Unknown or expired link.']:
        raise NotFound

    if not res.text.startswith("<html>"):
        raise ServerError("HN is weird.")

    if db_key.startswith('/pages'):
        result = parse_stories(res.text)
    elif db_key.startswith('/comments'):
        result = parse_comments(res.text)
    else:
        raise TypeError('Wrong DB Key.')

    return json.dumps(result)
