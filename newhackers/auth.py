import logging

import requests
from bs4 import BeautifulSoup

from newhackers import config
from newhackers.exceptions import ClientError, ServerError


def get_token(user, password):
    """Login on HN and return a user token

    :user: username string
    :password: password string

    Returns a user token string which needs to be given as a parameter
    for API methods which require a user to be signed in such as
    commenting or voting.

    Raises a ClientError if authentication failed.

    """
    # XXX this is very dangerous. It has the potential to get us banned
    # and I don't think there's any way to rate limit it for multiple
    # users.
    r = requests.get(config.HN_LOGIN)
    soup = BeautifulSoup(r.content)
    try:
        fnid = soup.find('input', attrs=dict(name='fnid'))['value']
    except TypeError:
        logging.error("Failed parsing response from %s.\n%s",
                      config.HN_LOGIN, r.content)
        raise ServerError("Authentication failed. Unknown server error.")

    r = requests.post(config.HN_LOGIN_POST,
                      data={'fnid': fnid, 'u': user, 'p': password})

    # XXX HN returns 200 on failed authentication, so we have to EAFP
    try:
        user_token = r.cookies['user']
    except KeyError:
        raise ClientError("Authentication failed. Bad user/password.")
    else:
        return user_token
