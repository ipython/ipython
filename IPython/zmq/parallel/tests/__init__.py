"""toplevel setup/teardown for parallel tests."""

import tempfile
import time
from subprocess import Popen, PIPE, STDOUT

from IPython.zmq.parallel.ipcluster import launch_process
from IPython.zmq.parallel.entry_point import select_random_ports

processes = []
blackhole = tempfile.TemporaryFile()

# nose setup/teardown

def setup():
    cp = Popen('ipcontrollerz --profile iptest -r --log-level 40'.split(), stdout=blackhole, stderr=STDOUT)
    processes.append(cp)
    time.sleep(.5)
    add_engine()
    time.sleep(2)

def add_engine(profile='iptest'):
    ep = Popen(['ipenginez']+ ['--profile', profile, '--log-level', '40'], stdout=blackhole, stderr=STDOUT)
    # ep.start()
    processes.append(ep)
    return ep

def teardown():
    time.sleep(1)
    while processes:
        p = processes.pop()
        if p.poll() is None:
            try:
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
    
