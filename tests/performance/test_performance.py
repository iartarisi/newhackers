#!/usr/bin/env python

import time

import grequests


URL = 'http://localhost:5000/ask'
CONCURRENT = 1000
REQUESTS = 10000


requests = [grequests.get(URL) for i in xrange(REQUESTS)]

beginning = time.time()
responses = grequests.map(requests, size=CONCURRENT)

total = time.time() - beginning

print "Requests: " + str(REQUESTS)
print "Concurrent: " + str(CONCURRENT)
print "Average time per request: " + str(total / REQUESTS)
print "Total time: " + str(total)
