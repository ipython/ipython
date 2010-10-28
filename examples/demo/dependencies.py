from IPython.zmq.parallel.client import *

client = Client('tcp://127.0.0.1:10101')

@require('numpy')
def norm(A):
    from numpy.linalg import norm
    return norm(A,2)

def checkpid(pid):
    import os
    return os.getpid() == pid

def checkhostname(host):
    import socket
    return socket.gethostname() == host

def getpid():
    import os
    return os.getpid()

pid0 = client.apply(getpid, targets=0, block=True)

@depend(checkpid, pid0)
def getpid2():
    import os
    return os.getpid()

rns = client[None]
rns.block=True

pids1 = [ rns.apply(getpid) for i in range(len(client.ids)) ]
pids2 = [ rns.apply(getpid2) for i in range(len(client.ids)) ]
print pids1
print pids2
