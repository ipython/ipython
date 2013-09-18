"""Tests for dependency.py

Authors:

* Min RK
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

# import
import os

from IPython.utils.pickleutil import can, uncan

import IPython.parallel as pmod
from IPython.parallel.util import interactive

from IPython.parallel.tests import add_engines
from .clienttest import ClusterTestCase

def setup():
    add_engines(1, total=True)

@pmod.require('time')
def wait(n):
    time.sleep(n)
    return n

@pmod.interactive
def func(x):
    return x*x

mixed = map(str, range(10))
completed = map(str, range(0,10,2))
failed = map(str, range(1,10,2))

class DependencyTest(ClusterTestCase):
    
    def setUp(self):
        ClusterTestCase.setUp(self)
        self.user_ns = {'__builtins__' : __builtins__}
        self.view = self.client.load_balanced_view()
        self.dview = self.client[-1]
        self.succeeded = set(map(str, range(0,25,2)))
        self.failed = set(map(str, range(1,25,2)))
    
    def assertMet(self, dep):
        self.assertTrue(dep.check(self.succeeded, self.failed), "Dependency should be met")
        
    def assertUnmet(self, dep):
        self.assertFalse(dep.check(self.succeeded, self.failed), "Dependency should not be met")
        
    def assertUnreachable(self, dep):
        self.assertTrue(dep.unreachable(self.succeeded, self.failed), "Dependency should be unreachable")
    
    def assertReachable(self, dep):
        self.assertFalse(dep.unreachable(self.succeeded, self.failed), "Dependency should be reachable")
    
    def cancan(self, f):
        """decorator to pass through canning into self.user_ns"""
        return uncan(can(f), self.user_ns)
    
    def test_require_imports(self):
        """test that @require imports names"""
        @self.cancan
        @pmod.require('urllib')
        @interactive
        def encode(dikt):
            return urllib.urlencode(dikt)
        # must pass through canning to properly connect namespaces
        self.assertEqual(encode(dict(a=5)), 'a=5')
    
    def test_success_only(self):
        dep = pmod.Dependency(mixed, success=True, failure=False)
        self.assertUnmet(dep)
        self.assertUnreachable(dep)
        dep.all=False
        self.assertMet(dep)
        self.assertReachable(dep)
        dep = pmod.Dependency(completed, success=True, failure=False)
        self.assertMet(dep)
        self.assertReachable(dep)
        dep.all=False
        self.assertMet(dep)
        self.assertReachable(dep)

    def test_failure_only(self):
        dep = pmod.Dependency(mixed, success=False, failure=True)
        self.assertUnmet(dep)
        self.assertUnreachable(dep)
        dep.all=False
        self.assertMet(dep)
        self.assertReachable(dep)
        dep = pmod.Dependency(completed, success=False, failure=True)
        self.assertUnmet(dep)
        self.assertUnreachable(dep)
        dep.all=False
        self.assertUnmet(dep)
        self.assertUnreachable(dep)
    
    def test_require_function(self):
        
        @pmod.interactive
        def bar(a):
            return func(a)

        @pmod.require(func)
        @pmod.interactive
        def bar2(a):
            return func(a)
        
        self.client[:].clear()
        self.assertRaisesRemote(NameError, self.view.apply_sync, bar, 5)
        ar = self.view.apply_async(bar2, 5)
        self.assertEqual(ar.get(5), func(5))

    def test_require_object(self):
        
        @pmod.require(foo=func)
        @pmod.interactive
        def bar(a):
            return foo(a)

        ar = self.view.apply_async(bar, 5)
        self.assertEqual(ar.get(5), func(5))
