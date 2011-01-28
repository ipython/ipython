"""toplevel setup/teardown for prallel tests."""
import time

from IPython.zmq.parallel.ipcluster import launch_process
from IPython.zmq.parallel.entry_point import select_random_ports
# from multiprocessing import Process

cluster_logs = dict(
    regport=0,
    processes = [],
)

def setup():
    p = select_random_ports(1)[0]
    cluster_logs['regport']=p
    cp = launch_process('controller',('--scheduler lru --ping 100 --regport %i'%p).split())
    # cp.start()
    cluster_logs['processes'].append(cp)
    add_engine(p)
    time.sleep(2)

def add_engine(port=None):
    if port is None:
        port = cluster_logs['regport']
    ep = launch_process('engine', ['--regport',str(port)])
    # ep.start()
    cluster_logs['processes'].append(ep)
    return ep

def teardown():
    time.sleep(1)
    processes = cluster_logs['processes']
    while processes:
        p = processes.pop()
        if p.poll() is None:
            try:
                print 'terminating'
                p.terminate()
            except Exception, e:
                print e
                pass
        if p.poll() is None:
            time.sleep(.25)
        if p.poll() is None:
            try:
                print 'killing'
                p.kill()
            except:
                print "couldn't shutdown process: ",p
    
    
