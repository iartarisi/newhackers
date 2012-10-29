# -*- coding: utf-8 -*-
# This file is part of newhackers.
# Copyright (c) 2012 Ionuț Arțăriși

# cuZmeură is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.

# cuZmeură is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with cuZmeură. If not, see <http://www.gnu.org/licenses/>.

import time

from bs4 import BeautifulSoup

from newhackers.config import rdb
from newhackers.backend import update_page
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
    if page not in ['', 'ask']:
        page = "x?fnid=" + page
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
    :page: string - the path after the HN root from where the item
    is downloaded

    Returns a JSON document representing the resource.

    """
    try:
        stories = rdb[db_key]
    except KeyError:
        stories = update_page(db_key, page)
        rdb[db_key] = stories
        rdb[db_key + '/updated'] = time.time()
        return stories

    tasks.update.delay(db_key, page)

    return stories
