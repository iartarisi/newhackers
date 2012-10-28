from bs4 import BeautifulSoup
import requests

from newhackers.backend import hn_get
from newhackers.exceptions import ClientError


def vote(token, direction, item):
    """Vote for an item

    :token: an authentication token which will be sent as a Cookie
    :item: string identifying the item
    :direction: either 'up' or 'down'
    """
    assert direction in ['up', 'down']

    res = hn_get("item?id=" + item, cookies={'user': token})
    vote_link = _find_vote_link(res.text, item, direction)
    
    if not vote_link:
        raise ClientError("Could not find vote link.")

    res = hn_get(vote_link, cookies={'user': token})
    if res.text == '':
        return True
    

def _find_vote_link(page, item, direction):
    """Return a vote link (HN path) for this item

    :page: a string of an HN page containing the item
    :item: string identifying the item
    :direction: either 'up' or 'down'

    """
    soup = BeautifulSoup(page)
    elem = soup.find(id='%s_%s' % (direction, item))
    try:
        return elem['href']
    except (KeyError, TypeError):
        return None
