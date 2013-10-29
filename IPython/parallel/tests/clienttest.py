"""base class for parallel client tests

Authors:

* Min RK
"""

#-------------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------
from __future__ import print_function

import sys
import tempfile
import time

from nose import SkipTest

import zmq
from zmq.tests import BaseZMQTestCase

from IPython.external.decorator import decorator

from IPython.parallel import error
from IPython.parallel import Client

from IPython.parallel.tests import launchers, add_engines

# simple tasks for use in apply tests

def segfault():
    """this will segfault"""
    import ctypes
    ctypes.memset(-1,0,1)

def crash():
    """from stdlib crashers in the test suite"""
    import types
    if sys.platform.startswith('win'):
        import ctypes
        ctypes.windll.kernel32.SetErrorMode(0x0002);
    args = [ 0, 0, 0, 0, b'\x04\x71\x00\x00', (), (), (), '', '', 1, b'']
    if sys.version_info[0] >= 3:
        # Python3 adds 'kwonlyargcount' as the second argument to Code
        args.insert(1, 0)
        
    co = types.CodeType(*args)
    exec(co)

def wait(n):
    """sleep for a time"""
    import time
    time.sleep(n)
    return n

def raiser(eclass):
    """raise an exception"""
    raise eclass()

def generate_output():
    """function for testing output
    
    publishes two outputs of each type, and returns
    a rich displayable object.
    """
    
    import sys
    from IPython.core.display import display, HTML, Math
    
    print("stdout")
    print("stderr", file=sys.stderr)
    
    display(HTML("<b>HTML</b>"))
    
    print("stdout2")
    print("stderr2", file=sys.stderr)
    
    display(Math(r"\alpha=\beta"))
    
    return Math("42")

# test decorator for skipping tests when libraries are unavailable
def skip_without(*names):
    """skip a test if some names are not importable"""
    @decorator
    def skip_without_names(f, *args, **kwargs):
        """decorator to skip tests in the absence of numpy."""
        for name in names:
            try:
                __import__(name)
            except ImportError:
                raise SkipTest
        return f(*args, **kwargs)
    return skip_without_names

#-------------------------------------------------------------------------------
# Classes
#-------------------------------------------------------------------------------


class ClusterTestCase(BaseZMQTestCase):
    timeout = 10
    
    def add_engines(self, n=1, block=True):
        """add multiple engines to our cluster"""
        self.engines.extend(add_engines(n))
        if block:
            self.wait_on_engines()

    def minimum_engines(self, n=1, block=True):
        """add engines until there are at least n connected"""
        self.engines.extend(add_engines(n, total=True))
        if block:
            self.wait_on_engines()
            
    
    def wait_on_engines(self, timeout=5):
        """wait for our engines to connect."""
        n = len(self.engines)+self.base_engine_count
        tic = time.time()
        while time.time()-tic < timeout and len(self.client.ids) < n:
            time.sleep(0.1)
        
        assert not len(self.client.ids) < n, "waiting for engines timed out"
    
    def client_wait(self, client, jobs=None, timeout=-1):
        """my wait wrapper, sets a default finite timeout to avoid hangs"""
        if timeout < 0:
            timeout = self.timeout
        return Client.wait(client, jobs, timeout)
    
    def connect_client(self):
        """connect a client with my Context, and track its sockets for cleanup"""
        c = Client(profile='iptest', context=self.context)
        c.wait = lambda *a, **kw: self.client_wait(c, *a, **kw)
        
        for name in filter(lambda n:n.endswith('socket'), dir(c)):
            s = getattr(c, name)
            s.setsockopt(zmq.LINGER, 0)
            self.sockets.append(s)
        return c
    
    def assertRaisesRemote(self, etype, f, *args, **kwargs):
        try:
            try:
                f(*args, **kwargs)
            except error.CompositeError as e:
                e.raise_exception()
        except error.RemoteError as e:
            self.assertEqual(etype.__name__, e.ename, "Should have raised %r, but raised %r"%(etype.__name__, e.ename))
        else:
            self.fail("should have raised a RemoteError")
            
    def _wait_for(self, f, timeout=10):
        """wait for a condition"""
        tic = time.time()
        while time.time() <= tic + timeout:
            if f():
                return
            time.sleep(0.1)
            self.client.spin()
        if not f():
            print("Warning: Awaited condition never arrived")
    
    def setUp(self):
        BaseZMQTestCase.setUp(self)
        self.client = self.connect_client()
        # start every test with clean engine namespaces:
        self.client.clear(block=True)
        self.base_engine_count=len(self.client.ids)
        self.engines=[]
    
    def tearDown(self):
        # self.client.clear(block=True)
        # close fds:
        for e in filter(lambda e: e.poll() is not None, launchers):
            launchers.remove(e)
        
        # allow flushing of incoming messages to prevent crash on socket close
        self.client.wait(timeout=2)
        # time.sleep(2)
        self.client.spin()
        self.client.close()
        BaseZMQTestCase.tearDown(self)
        # this will be redundant when pyzmq merges PR #88
        # self.context.term()
        # print tempfile.TemporaryFile().fileno(),
        # sys.stdout.flush()
        
