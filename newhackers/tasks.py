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
                pipe[db_key+'/updated'] = time.time()
                pipe.execute()
    except LockException:
        pass

 

 
