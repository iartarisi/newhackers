#!/usr/bin/env python

from setuptools import setup

setup(
    name="Hacker News API",
    version='0.1',
    long_description=__doc__,
    packages=['newhackers'],
    include_package_data=True,
    install_requires=['beautifulsoup4', 'celery', 'Flask', 'redis',
                      'requests', 'parsedatetime', 'gevent'],
    tests_require=['mock', 'nose', 'grequests'],
    test_suite='nose.collector')
