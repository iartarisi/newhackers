#!/usr/bin/env python

from setuptools import setup

setup(
    name="Hacker News API",
    version='0.1',
    long_description=__doc__,
    packages=['newhackers'],
    include_package_data=True,
    install_requires=['Flask', 'redis', 'requests'],
    tests_require=['mock'],
    test_suite='tests')
