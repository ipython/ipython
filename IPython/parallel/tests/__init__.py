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

import os
import tempfile
import time
from subprocess import Popen

from IPython.utils.path import get_ipython_dir
from IPython.parallel import Client
from IPython.parallel.apps.launcher import (LocalProcessLauncher,
                                                  ipengine_cmd_argv,
                                                  ipcontroller_cmd_argv,
                                                  SIGKILL,
                                                  ProcessStateError,
)

# globals
launchers = []
blackhole = open(os.devnull, 'w')

# Launcher class
class TestProcessLauncher(LocalProcessLauncher):
    """subclass LocalProcessLauncher, to prevent extra sockets and threads being created on Windows"""
    def start(self):
        if self.state == 'before':
            self.process = Popen(self.args,
                stdout=blackhole, stderr=blackhole,
                env=os.environ,
                cwd=self.work_dir
            )
            self.notify_start(self.process.pid)
            self.poll = self.process.poll
        else:
            s = 'The process was already started and has state: %r' % self.state
            raise ProcessStateError(s)

# nose setup/teardown

def setup():
    cluster_dir = os.path.join(get_ipython_dir(), 'profile_iptest')
    engine_json = os.path.join(cluster_dir, 'security', 'ipcontroller-engine.json')
    client_json = os.path.join(cluster_dir, 'security', 'ipcontroller-client.json')
    for json in (engine_json, client_json):
        if os.path.exists(json):
            os.remove(json)
    
    cp = TestProcessLauncher()
    cp.cmd_and_args = ipcontroller_cmd_argv + \
                ['--profile=iptest', '--log-level=50', '--ping=250', '--dictdb']
    cp.start()
    launchers.append(cp)
    tic = time.time()
    while not os.path.exists(engine_json) or not os.path.exists(client_json):
        if cp.poll() is not None:
            print cp.poll()
            raise RuntimeError("The test controller failed to start.")
        elif time.time()-tic > 15:
            raise RuntimeError("Timeout waiting for the test controller to start.")
        time.sleep(0.1)
    add_engines(1)

def add_engines(n=1, profile='iptest', total=False):
    """add a number of engines to a given profile.
    
    If total is True, then already running engines are counted, and only
    the additional engines necessary (if any) are started.
    """
    rc = Client(profile=profile)
    base = len(rc)
    
    if total:
        n = max(n - base, 0)
    
    eps = []
    for i in range(n):
        ep = TestProcessLauncher()
        ep.cmd_and_args = ipengine_cmd_argv + [
            '--profile=%s' % profile,
            '--log-level=50',
            '--InteractiveShell.colors=nocolor'
            ]
        ep.start()
        launchers.append(ep)
        eps.append(ep)
    tic = time.time()
    while len(rc) < base+n:
        if any([ ep.poll() is not None for ep in eps ]):
            raise RuntimeError("A test engine failed to start.")
        elif time.time()-tic > 15:
            raise RuntimeError("Timeout waiting for engines to connect.")
        time.sleep(.1)
        rc.spin()
    rc.close()
    return eps

def teardown():
    time.sleep(1)
    while launchers:
        p = launchers.pop()
        if p.poll() is None:
            try:
                p.stop()
            except Exception as e:
                print e
                pass
        if p.poll() is None:
            time.sleep(.25)
        if p.poll() is None:
            try:
                print 'cleaning up test process...'
                p.signal(SIGKILL)
            except:
                print "couldn't shutdown process: ", p
    blackhole.close()
    
