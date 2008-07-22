#!/usr/bin/env python
# encoding: utf-8

from IPython.kernel import client
import time

tc = client.TaskClient()
mec = client.MultiEngineClient()

mec.execute('import time')

for i in range(24):
    tc.run(client.StringTask('time.sleep(1)'))

for i in range(6):
    time.sleep(1.0)
    print "Queue status (vebose=False)"
    print tc.queue_status()
    
for i in range(24):
    tc.run(client.StringTask('time.sleep(1)'))

for i in range(6):
    time.sleep(1.0)
    print "Queue status (vebose=True)"
    print tc.queue_status(True)

for i in range(12):
    tc.run(client.StringTask('time.sleep(2)'))

print "Queue status (vebose=True)"
print tc.queue_status(True)

qs = tc.queue_status(True)
sched = qs['scheduled']

for tid in sched[-4:]:
    tc.abort(tid)

for i in range(6):
    time.sleep(1.0)
    print "Queue status (vebose=True)"
    print tc.queue_status(True)

