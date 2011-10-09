#!/usr/bin/env python
# encoding: utf-8

from IPython.parallel import Client
import time
import sys
flush = sys.stdout.flush

rc = Client()
v = rc.load_balanced_view()
mux = rc[:]


for i in range(24):
    v.apply(time.sleep, 1)

for i in range(6):
    time.sleep(1.0)
    print "Queue status (vebose=False)"
    print v.queue_status(verbose=False)
    flush()
    
for i in range(24):
    v.apply(time.sleep, 1)

for i in range(6):
    time.sleep(1.0)
    print "Queue status (vebose=True)"
    print v.queue_status(verbose=True)
    flush()

for i in range(12):
    v.apply(time.sleep, 2)

print "Queue status (vebose=True)"
print v.queue_status(verbose=True)
flush()

# qs = v.queue_status(verbose=True)
# queued = qs['scheduled']

for msg_id in v.history[-4:]:
    v.abort(msg_id)

for i in range(6):
    time.sleep(1.0)
    print "Queue status (vebose=True)"
    print v.queue_status(verbose=True)
    flush()

