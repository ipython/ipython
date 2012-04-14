from IPython.parallel import *

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

view = client.load_balanced_view()
view.block=True

# will run on anything:
pids1 = [ view.apply(getpid) for i in range(len(client.ids)) ]
print(pids1)
# will only run on e0:
pids2 = [ view.apply(getpid2) for i in range(len(client.ids)) ]
print(pids2)

print("now test some dependency behaviors")

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
d1a = Dependency(mixed, all=False, failure=True) # yes
d1b = Dependency(mixed, all=False) # yes
d2a = Dependency(mixed, all=True, failure=True) # yes after / no follow
d2b = Dependency(mixed, all=True) # no
d3 = Dependency(failures, all=False) # no
d4 = Dependency(failures, all=False, failure=True) # yes
d5 = Dependency(failures, all=True, failure=True) # yes after / no follow
d6 = Dependency(successes, all=True, failure=True) # yes after / no follow

view.block = False
flags = view.temp_flags
with flags(after=d1a):
    r1a = view.apply(getpid)
with flags(follow=d1b):
    r1b = view.apply(getpid)
with flags(after=d2b, follow=d2a):
    r2a = view.apply(getpid)
with flags(after=d2a, follow=d2b):
    r2b = view.apply(getpid)
with flags(after=d3):
    r3 = view.apply(getpid)
with flags(after=d4):
    r4a = view.apply(getpid)
with flags(follow=d4):
    r4b = view.apply(getpid)
with flags(after=d3, follow=d4):
    r4c = view.apply(getpid)
with flags(after=d5):
    r5 = view.apply(getpid)
with flags(follow=d5, after=d3):
    r5b = view.apply(getpid)
with flags(follow=d6):
    r6 = view.apply(getpid)
with flags(after=d6, follow=d2b):
    r6b = view.apply(getpid)

def should_fail(f):
    try:
        f()
    except error.KernelError:
        pass
    else:
        print('should have raised')
        # raise Exception("should have raised")

# print(r1a.msg_ids)
r1a.get()
# print(r1b.msg_ids)
r1b.get()
# print(r2a.msg_ids)
should_fail(r2a.get)
# print(r2b.msg_ids)
should_fail(r2b.get)
# print(r3.msg_ids)
should_fail(r3.get)
# print(r4a.msg_ids)
r4a.get()
# print(r4b.msg_ids)
r4b.get()
# print(r4c.msg_ids)
should_fail(r4c.get)
# print(r5.msg_ids)
r5.get()
# print(r5b.msg_ids)
should_fail(r5b.get)
# print(r6.msg_ids)
should_fail(r6.get) # assuming > 1 engine
# print(r6b.msg_ids)
should_fail(r6b.get)
print('done')
