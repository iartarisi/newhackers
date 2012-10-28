from datetime import datetime, timedelta
import json

import redis
import requests

from newhackers import config
from newhackers.parsers import parse_stories, parse_comments
from newhackers.exceptions import ClientError, NotFound, ServerError


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


def update_page(db_key, path):
    """Updates a page in the database

    The page is downloaded, parsed and then stored in the database as a
    JSON string. This string is also returned by the function.
    
    :db_key: a redis string of the key where the stories page will be stored
    :path: the HN URL path where the page will be downloaded from

    Raises NotFound when the page could not be found on the remote
    server or ServerError in case the server returned a response that we
    could not understand. (It's still the server's fault because it
    doesn't even have sensible status codes)

    """
    res = hn_get(path)
    if db_key.startswith('/pages'):
        result = parse_stories(res.text)
    elif db_key.startswith('/comments'):
        result = parse_comments(res.text)
    else:
        raise TypeError('Wrong DB Key.')

    return json.dumps(result)


def hn_get(*args, **kwargs):
    """Download an HN page.

    The arguments are the same as for the `requests.get` function.

    Return a requests Response object

    """
    # add the domain name to the first argument which is the path
    args = tuple([config.HN + args[0]] + list(args[1:]))

    res = requests.get(*args, **kwargs)
    # HN is ignorant of HTTP status codes
    # all errors seem to be plain text sentences
    if res.text in ['No such item.', 'Unknown.', 'Unknown or expired link.']:
        raise NotFound

    if res.text == "Can't make that vote.":
        raise ClientError(res.text)

    # An empty string as a response body is ok, that's the good response
    # when voting
    if not res.text.startswith("<html>") and res.text != '':
        raise ServerError("HN is weird.")
    
    return res
