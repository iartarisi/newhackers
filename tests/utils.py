from datetime import datetime, timedelta
import time


def seconds_old(secs):
    """Return an epoch float that's :secs: seconds old"""
    return time.mktime(
        (datetime.now() - timedelta(seconds=secs)).timetuple())
