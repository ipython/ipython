"""toplevel setup/teardown for parallel tests."""

#-------------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import tempfile
import time
from subprocess import Popen, PIPE, STDOUT

from IPython.parallel import Client

processes = []
blackhole = tempfile.TemporaryFile()

# nose setup/teardown

def setup():
    cp = Popen('ipcontroller --profile iptest -r --log-level 10 --log-to-file'.split(), stdout=blackhole, stderr=STDOUT)
    processes.append(cp)
    time.sleep(.5)
    add_engines(1)
    c = Client(profile='iptest')
    while not c.ids:
        time.sleep(.1)
        c.spin()
    c.close()

def add_engines(n=1, profile='iptest'):
    rc = Client(profile=profile)
    base = len(rc)
    eps = []
    for i in range(n):
        ep = Popen(['ipengine']+ ['--profile', profile, '--log-level', '10', '--log-to-file'], stdout=blackhole, stderr=STDOUT)
        # ep.start()
        processes.append(ep)
        eps.append(ep)
    while len(rc) < base+n:
        time.sleep(.1)
        rc.spin()
    rc.close()
    return eps

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
                print "couldn't shutdown process: ", p
    
