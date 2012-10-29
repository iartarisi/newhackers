# Copyright Manning or Josiah Carlson?
# http://dr-josiah.blogspot.cz/2012/01/creating-lock-with-redis.html

import time

import redis

import contextlib, uuid


class LockException(Exception): pass


@contextlib.contextmanager
def redis_lock(conn, lockname, atime=10, ltime=10):
    identifier = str(uuid.uuid4())
    if acquire_lock(**locals()) != identifier:
        raise LockException("could not acquire lock")
    try:
        yield identifier
    finally:
        if not release_lock(conn, lockname, identifier):
            raise LockException("lock was lost")


def acquire_lock(conn, lockname, identifier, atime=10, ltime=10):
    end = time.time() + atime
    while end > time.time():
        if conn.setnx(lockname, identifier):
            conn.expire(lockname, ltime)
            return identifier
        elif not conn.ttl(lockname):
            conn.expire(lockname, ltime)
 
        time.sleep(.001)
    return False


def release_lock(conn, lockname, identifier):
    pipe = conn.pipeline(True)
 
    while True:
        try:
            pipe.watch(lockname)
            if pipe.get(lockname) == identifier:
                pipe.multi()
                pipe.delete(lockname)
                pipe.execute()
                return True
 
            pipe.unwatch()
            break
 
        except redis.exceptions.WatchError:
            pass
 
    # we lost the lock
    return False
