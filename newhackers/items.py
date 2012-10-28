import time

from bs4 import BeautifulSoup

from newhackers.backend import rdb, update_page
from newhackers import tasks


def get_stories(page):
    """Return a page of stories

    :page: string - can be one of:
     - '' - retrieves stories from the first HN page
     - 'ask' - retrieves stories from the first page of Ask HN stories
     - '<hash>' - a page hash which represents an identifier of a common
       HN or Ask HN page

    Raises NotFound exception if the page was not found.

    """
    return _get_cache('/pages/' + page, page)


def get_comments(item):
    """Return a page of comments

    :item: int - the identifier of a comments page on HN

    Returns information about a submission and all the comments attached
    to it.

    """
    item = str(item)
    return _get_cache('/comments/' + item, 'item?id=' + item)


def _get_cache(db_key, page):
    """Retrieves an item from HN with caching

    :db_key: string - the database key where the item is stored
    :page: string - the path after the HN root from where the item is downloaded

    Returns a JSON document representing the resource.

    """
    try:
        stories = rdb[db_key]
    except KeyError:
        stories = update_page(db_key, page)
        rdb[db_key] = stories
        rdb[db_key+'/updated'] = time.time()
        return stories

    tasks.update.delay(db_key, page)

    return stories
