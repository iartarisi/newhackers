from bs4 import BeautifulSoup

from newhackers.backend import rdb, too_old, update_page


def get_stories(page):
    """Return a page of stories

    :page: string - can be one of:
     - '' - retrieves stories from the first HN page
     - 'ask' - retrieves stories from the first page of Ask HN stories
     - '<hash>' - a page hash which represents an identifier of a common
       HN or Ask HN page

    Raises NotFound exception if the page was not found.

    """
    db_key = '/pages/' + page
    try:
        stories = rdb[db_key]
    except KeyError:
        stories = update_page(db_key, page)
        return stories

    if too_old(db_key):
        # background task
        update_page(db_key, page)

    return stories
