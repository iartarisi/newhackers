#!/usr/bin/env python
from __future__ import absolute_import

from celery import Celery

celery = Celery('newhackers.celer',
                include=['newhackers.backend'])

# Optional configuration, see the application user guide.
celery.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
    BROKER_URL = 'redis://localhost:6379/0',
)

if __name__ == '__main__':
    celery.start()
