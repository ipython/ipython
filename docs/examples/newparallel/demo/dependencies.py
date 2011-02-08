from IPython.zmq.parallel import error
from IPython.zmq.parallel.dependency import Dependency
from IPython.zmq.parallel.client import *

client = Client()

# this will only run on machines that can import numpy:
@require('numpy')
def norm(A):
    from numpy.linalg import norm
    return norm(A,2)

def checkpid(pid):
    """return the pid of the engine"""
    import os
    return os.getpid() == pid

def checkhostname(host):
    import socket
    return socket.gethostname() == host

def getpid():
    import os
    return os.getpid()

pid0 = client[0].apply_sync(getpid)

# this will depend on the pid being that of target 0:
@depend(checkpid, pid0)
def getpid2():
    import os
    return os.getpid()

view = client[None]
view.block=True

# will run on anything:
pids1 = [ view.apply(getpid) for i in range(len(client.ids)) ]
print pids1
# will only run on e0:
pids2 = [ view.apply(getpid2) for i in range(len(client.ids)) ]
print pids2

print "now test some dependency behaviors"

def wait(t):
    import time
    time.sleep(t)
    return t

# fail after some time:
def wait_and_fail(t):
    import time
    time.sleep(t)
    return 1/0

successes = [ view.apply_async(wait, 1).msg_ids[0] for i in range(len(client.ids)) ]
failures = [ view.apply_async(wait_and_fail, 1).msg_ids[0] for i in range(len(client.ids)) ]

mixed = [failures[0],successes[0]]
d1a = Dependency(mixed, mode='any', success_only=False) # yes
d1b = Dependency(mixed, mode='any', success_only=True) # yes
d2a = Dependency(mixed, mode='all', success_only=False) # yes after / no follow
d2b = Dependency(mixed, mode='all', success_only=True) # no
d3 = Dependency(failures, mode='any', success_only=True) # no
d4 = Dependency(failures, mode='any', success_only=False) # yes
d5 = Dependency(failures, mode='all', success_only=False) # yes after / no follow
d6 = Dependency(successes, mode='all', success_only=False) # yes after / no follow

client.block = False

r1a = client.apply(getpid, after=d1a)
r1b = client.apply(getpid, follow=d1b)
r2a = client.apply(getpid, after=d2b, follow=d2a)
r2b = client.apply(getpid, after=d2a, follow=d2b)
r3 = client.apply(getpid, after=d3)
r4a = client.apply(getpid, after=d4)
r4b = client.apply(getpid, follow=d4)
r4c = client.apply(getpid, after=d3, follow=d4)
r5 = client.apply(getpid, after=d5)
r5b = client.apply(getpid, follow=d5, after=d3)
r6 = client.apply(getpid, follow=d6)
r6b = client.apply(getpid, after=d6, follow=d2b)

def should_fail(f):
    try:
        f()
    except error.KernelError:
        pass
    else:
        print 'should have raised'
        # raise Exception("should have raised")

# print r1a.msg_ids
r1a.get()
# print r1b.msg_ids
r1b.get()
# print r2a.msg_ids
should_fail(r2a.get)
# print r2b.msg_ids
should_fail(r2b.get)
# print r3.msg_ids
should_fail(r3.get)
# print r4a.msg_ids
r4a.get()
# print r4b.msg_ids
r4b.get()
# print r4c.msg_ids
should_fail(r4c.get)
# print r5.msg_ids
r5.get()
# print r5b.msg_ids
should_fail(r5b.get)
# print r6.msg_ids
should_fail(r6.get) # assuming > 1 engine
# print r6b.msg_ids
should_fail(r6b.get)
print 'done'
