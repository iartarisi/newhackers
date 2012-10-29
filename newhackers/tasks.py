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

from newhackers.backend import too_old, update_page
from newhackers.config import rdb
from newhackers.celer import celery
from newhackers.redis_lock import redis_lock, LockException


@celery.task
def update(db_key, page):
    try:
        with redis_lock(rdb, '/lock' + db_key):
            if too_old(db_key):
                stories = update_page(db_key, page)
                pipe = rdb.pipeline(True)
                pipe[db_key] = stories
                pipe[db_key + '/updated'] = time.time()
                pipe.execute()
    except LockException:
        pass

 

 
