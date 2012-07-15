"""Tests for asyncresult.py

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

import time

from IPython.utils.io import capture_output

from IPython.parallel.error import TimeoutError
from IPython.parallel import error, Client
from IPython.parallel.tests import add_engines
from .clienttest import ClusterTestCase

def setup():
    add_engines(2, total=True)

def wait(n):
    import time
    time.sleep(n)
    return n

class AsyncResultTest(ClusterTestCase):

    def test_single_result_view(self):
        """various one-target views get the right value for single_result"""
        eid = self.client.ids[-1]
        ar = self.client[eid].apply_async(lambda : 42)
        self.assertEquals(ar.get(), 42)
        ar = self.client[[eid]].apply_async(lambda : 42)
        self.assertEquals(ar.get(), [42])
        ar = self.client[-1:].apply_async(lambda : 42)
        self.assertEquals(ar.get(), [42])

    def test_get_after_done(self):
        ar = self.client[-1].apply_async(lambda : 42)
        ar.wait()
        self.assertTrue(ar.ready())
        self.assertEquals(ar.get(), 42)
        self.assertEquals(ar.get(), 42)

    def test_get_before_done(self):
        ar = self.client[-1].apply_async(wait, 0.1)
        self.assertRaises(TimeoutError, ar.get, 0)
        ar.wait(0)
        self.assertFalse(ar.ready())
        self.assertEquals(ar.get(), 0.1)

    def test_get_after_error(self):
        ar = self.client[-1].apply_async(lambda : 1/0)
        ar.wait(10)
        self.assertRaisesRemote(ZeroDivisionError, ar.get)
        self.assertRaisesRemote(ZeroDivisionError, ar.get)
        self.assertRaisesRemote(ZeroDivisionError, ar.get_dict)
    
    def test_get_dict(self):
        n = len(self.client)
        ar = self.client[:].apply_async(lambda : 5)
        self.assertEquals(ar.get(), [5]*n)
        d = ar.get_dict()
        self.assertEquals(sorted(d.keys()), sorted(self.client.ids))
        for eid,r in d.iteritems():
            self.assertEquals(r, 5)
    
    def test_list_amr(self):
        ar = self.client.load_balanced_view().map_async(wait, [0.1]*5)
        rlist = list(ar)
    
    def test_getattr(self):
        ar = self.client[:].apply_async(wait, 0.5)
        self.assertRaises(AttributeError, lambda : ar._foo)
        self.assertRaises(AttributeError, lambda : ar.__length_hint__())
        self.assertRaises(AttributeError, lambda : ar.foo)
        self.assertRaises(AttributeError, lambda : ar.engine_id)
        self.assertFalse(hasattr(ar, '__length_hint__'))
        self.assertFalse(hasattr(ar, 'foo'))
        self.assertFalse(hasattr(ar, 'engine_id'))
        ar.get(5)
        self.assertRaises(AttributeError, lambda : ar._foo)
        self.assertRaises(AttributeError, lambda : ar.__length_hint__())
        self.assertRaises(AttributeError, lambda : ar.foo)
        self.assertTrue(isinstance(ar.engine_id, list))
        self.assertEquals(ar.engine_id, ar['engine_id'])
        self.assertFalse(hasattr(ar, '__length_hint__'))
        self.assertFalse(hasattr(ar, 'foo'))
        self.assertTrue(hasattr(ar, 'engine_id'))

    def test_getitem(self):
        ar = self.client[:].apply_async(wait, 0.5)
        self.assertRaises(TimeoutError, lambda : ar['foo'])
        self.assertRaises(TimeoutError, lambda : ar['engine_id'])
        ar.get(5)
        self.assertRaises(KeyError, lambda : ar['foo'])
        self.assertTrue(isinstance(ar['engine_id'], list))
        self.assertEquals(ar.engine_id, ar['engine_id'])
    
    def test_single_result(self):
        ar = self.client[-1].apply_async(wait, 0.5)
        self.assertRaises(TimeoutError, lambda : ar['foo'])
        self.assertRaises(TimeoutError, lambda : ar['engine_id'])
        self.assertTrue(ar.get(5) == 0.5)
        self.assertTrue(isinstance(ar['engine_id'], int))
        self.assertTrue(isinstance(ar.engine_id, int))
        self.assertEquals(ar.engine_id, ar['engine_id'])
    
    def test_abort(self):
        e = self.client[-1]
        ar = e.execute('import time; time.sleep(1)', block=False)
        ar2 = e.apply_async(lambda : 2)
        ar2.abort()
        self.assertRaises(error.TaskAborted, ar2.get)
        ar.get()
    
    def test_len(self):
        v = self.client.load_balanced_view()
        ar = v.map_async(lambda x: x, range(10))
        self.assertEquals(len(ar), 10)
        ar = v.apply_async(lambda x: x, range(10))
        self.assertEquals(len(ar), 1)
        ar = self.client[:].apply_async(lambda x: x, range(10))
        self.assertEquals(len(ar), len(self.client.ids))
    
    def test_wall_time_single(self):
        v = self.client.load_balanced_view()
        ar = v.apply_async(time.sleep, 0.25)
        self.assertRaises(TimeoutError, getattr, ar, 'wall_time')
        ar.get(2)
        self.assertTrue(ar.wall_time < 1.)
        self.assertTrue(ar.wall_time > 0.2)

    def test_wall_time_multi(self):
        self.minimum_engines(4)
        v = self.client[:]
        ar = v.apply_async(time.sleep, 0.25)
        self.assertRaises(TimeoutError, getattr, ar, 'wall_time')
        ar.get(2)
        self.assertTrue(ar.wall_time < 1.)
        self.assertTrue(ar.wall_time > 0.2)

    def test_serial_time_single(self):
        v = self.client.load_balanced_view()
        ar = v.apply_async(time.sleep, 0.25)
        self.assertRaises(TimeoutError, getattr, ar, 'serial_time')
        ar.get(2)
        self.assertTrue(ar.serial_time < 1.)
        self.assertTrue(ar.serial_time > 0.2)

    def test_serial_time_multi(self):
        self.minimum_engines(4)
        v = self.client[:]
        ar = v.apply_async(time.sleep, 0.25)
        self.assertRaises(TimeoutError, getattr, ar, 'serial_time')
        ar.get(2)
        self.assertTrue(ar.serial_time < 2.)
        self.assertTrue(ar.serial_time > 0.8)

    def test_elapsed_single(self):
        v = self.client.load_balanced_view()
        ar = v.apply_async(time.sleep, 0.25)
        while not ar.ready():
            time.sleep(0.01)
            self.assertTrue(ar.elapsed < 1)
        self.assertTrue(ar.elapsed < 1)
        ar.get(2)

    def test_elapsed_multi(self):
        v = self.client[:]
        ar = v.apply_async(time.sleep, 0.25)
        while not ar.ready():
            time.sleep(0.01)
            self.assertTrue(ar.elapsed < 1)
        self.assertTrue(ar.elapsed < 1)
        ar.get(2)

    def test_hubresult_timestamps(self):
        self.minimum_engines(4)
        v = self.client[:]
        ar = v.apply_async(time.sleep, 0.25)
        ar.get(2)
        rc2 = Client(profile='iptest')
        # must have try/finally to close second Client, otherwise
        # will have dangling sockets causing problems
        try:
            time.sleep(0.25)
            hr = rc2.get_result(ar.msg_ids)
            self.assertTrue(hr.elapsed > 0., "got bad elapsed: %s" % hr.elapsed)
            hr.get(1)
            self.assertTrue(hr.wall_time < ar.wall_time + 0.2, "got bad wall_time: %s > %s" % (hr.wall_time, ar.wall_time))
            self.assertEquals(hr.serial_time, ar.serial_time)
        finally:
            rc2.close()

    def test_display_empty_streams_single(self):
        """empty stdout/err are not displayed (single result)"""
        self.minimum_engines(1)
        
        v = self.client[-1]
        ar = v.execute("print (5555)")
        ar.get(5)
        with capture_output() as io:
            ar.display_outputs()
        self.assertEquals(io.stderr, '')
        self.assertEquals('5555\n', io.stdout)

        ar = v.execute("a=5")
        ar.get(5)
        with capture_output() as io:
            ar.display_outputs()
        self.assertEquals(io.stderr, '')
        self.assertEquals(io.stdout, '')
        
    def test_display_empty_streams_type(self):
        """empty stdout/err are not displayed (groupby type)"""
        self.minimum_engines(1)
        
        v = self.client[:]
        ar = v.execute("print (5555)")
        ar.get(5)
        with capture_output() as io:
            ar.display_outputs()
        self.assertEquals(io.stderr, '')
        self.assertEquals(io.stdout.count('5555'), len(v), io.stdout)
        self.assertFalse('\n\n' in io.stdout, io.stdout)
        self.assertEquals(io.stdout.count('[stdout:'), len(v), io.stdout)

        ar = v.execute("a=5")
        ar.get(5)
        with capture_output() as io:
            ar.display_outputs()
        self.assertEquals(io.stderr, '')
        self.assertEquals(io.stdout, '')

    def test_display_empty_streams_engine(self):
        """empty stdout/err are not displayed (groupby engine)"""
        self.minimum_engines(1)
        
        v = self.client[:]
        ar = v.execute("print (5555)")
        ar.get(5)
        with capture_output() as io:
            ar.display_outputs('engine')
        self.assertEquals(io.stderr, '')
        self.assertEquals(io.stdout.count('5555'), len(v), io.stdout)
        self.assertFalse('\n\n' in io.stdout, io.stdout)
        self.assertEquals(io.stdout.count('[stdout:'), len(v), io.stdout)

        ar = v.execute("a=5")
        ar.get(5)
        with capture_output() as io:
            ar.display_outputs('engine')
        self.assertEquals(io.stderr, '')
        self.assertEquals(io.stdout, '')
        

