# -*- coding: utf-8 -*-
"""test LoadBalancedView objects

Authors:

* Min RK
"""
#-------------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import sys
import time

import zmq
from nose import SkipTest

from IPython import parallel  as pmod
from IPython.parallel import error

from IPython.parallel.tests import add_engines

from .clienttest import ClusterTestCase, crash, wait, skip_without

def setup():
    add_engines(3)

class TestLoadBalancedView(ClusterTestCase):

    def setUp(self):
        ClusterTestCase.setUp(self)
        self.view = self.client.load_balanced_view()

    def test_z_crash_task(self):
        """test graceful handling of engine death (balanced)"""
        raise SkipTest("crash tests disabled, due to undesirable crash reports")
        # self.add_engines(1)
        ar = self.view.apply_async(crash)
        self.assertRaisesRemote(error.EngineError, ar.get, 10)
        eid = ar.engine_id
        tic = time.time()
        while eid in self.client.ids and time.time()-tic < 5:
            time.sleep(.01)
            self.client.spin()
        self.assertFalse(eid in self.client.ids, "Engine should have died")

    def test_map(self):
        def f(x):
            return x**2
        data = range(16)
        r = self.view.map_sync(f, data)
        self.assertEquals(r, map(f, data))

    def test_map_unordered(self):
        def f(x):
            return x**2
        def slow_f(x):
            import time
            time.sleep(0.05*x)
            return x**2
        data = range(16,0,-1)
        reference = map(f, data)
        
        amr = self.view.map_async(slow_f, data, ordered=False)
        self.assertTrue(isinstance(amr, pmod.AsyncMapResult))
        # check individual elements, retrieved as they come
        # list comprehension uses __iter__
        astheycame = [ r for r in amr ]
        # Ensure that at least one result came out of order:
        self.assertNotEquals(astheycame, reference, "should not have preserved order")
        self.assertEquals(sorted(astheycame, reverse=True), reference, "result corrupted")

    def test_map_ordered(self):
        def f(x):
            return x**2
        def slow_f(x):
            import time
            time.sleep(0.05*x)
            return x**2
        data = range(16,0,-1)
        reference = map(f, data)
        
        amr = self.view.map_async(slow_f, data)
        self.assertTrue(isinstance(amr, pmod.AsyncMapResult))
        # check individual elements, retrieved as they come
        # list(amr) uses __iter__
        astheycame = list(amr)
        # Ensure that results came in order
        self.assertEquals(astheycame, reference)
        self.assertEquals(amr.result, reference)

    def test_map_iterable(self):
        """test map on iterables (balanced)"""
        view = self.view
        # 101 is prime, so it won't be evenly distributed
        arr = range(101)
        # so that it will be an iterator, even in Python 3
        it = iter(arr)
        r = view.map_sync(lambda x:x, arr)
        self.assertEquals(r, list(arr))

    
    def test_abort(self):
        view = self.view
        ar = self.client[:].apply_async(time.sleep, .5)
        ar = self.client[:].apply_async(time.sleep, .5)
        time.sleep(0.2)
        ar2 = view.apply_async(lambda : 2)
        ar3 = view.apply_async(lambda : 3)
        view.abort(ar2)
        view.abort(ar3.msg_ids)
        self.assertRaises(error.TaskAborted, ar2.get)
        self.assertRaises(error.TaskAborted, ar3.get)

    def test_retries(self):
        add_engines(3)
        view = self.view
        view.timeout = 1 # prevent hang if this doesn't behave
        def fail():
            assert False
        for r in range(len(self.client)-1):
            with view.temp_flags(retries=r):
                self.assertRaisesRemote(AssertionError, view.apply_sync, fail)

        with view.temp_flags(retries=len(self.client), timeout=0.25):
            self.assertRaisesRemote(error.TaskTimeout, view.apply_sync, fail)

    def test_invalid_dependency(self):
        view = self.view
        with view.temp_flags(after='12345'):
            self.assertRaisesRemote(error.InvalidDependency, view.apply_sync, lambda : 1)

    def test_impossible_dependency(self):
        if len(self.client) < 2:
            add_engines(2)
        view = self.client.load_balanced_view()
        ar1 = view.apply_async(lambda : 1)
        ar1.get()
        e1 = ar1.engine_id
        e2 = e1
        while e2 == e1:
            ar2 = view.apply_async(lambda : 1)
            ar2.get()
            e2 = ar2.engine_id

        with view.temp_flags(follow=[ar1, ar2]):
            self.assertRaisesRemote(error.ImpossibleDependency, view.apply_sync, lambda : 1)


    def test_follow(self):
        ar = self.view.apply_async(lambda : 1)
        ar.get()
        ars = []
        first_id = ar.engine_id

        self.view.follow = ar
        for i in range(5):
            ars.append(self.view.apply_async(lambda : 1))
        self.view.wait(ars)
        for ar in ars:
            self.assertEquals(ar.engine_id, first_id)

    def test_after(self):
        view = self.view
        ar = view.apply_async(time.sleep, 0.5)
        with view.temp_flags(after=ar):
            ar2 = view.apply_async(lambda : 1)

        ar.wait()
        ar2.wait()
        self.assertTrue(ar2.started >= ar.completed, "%s not >= %s"%(ar.started, ar.completed))
