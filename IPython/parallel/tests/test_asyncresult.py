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

import nose.tools as nt

from IPython.utils.io import capture_output

from IPython.parallel.error import TimeoutError
from IPython.parallel import error, Client
from IPython.parallel.tests import add_engines
from .clienttest import ClusterTestCase
from IPython.utils.py3compat import iteritems

def setup():
    add_engines(2, total=True)

def wait(n):
    import time
    time.sleep(n)
    return n

def echo(x):
    return x

class AsyncResultTest(ClusterTestCase):

    def test_single_result_view(self):
        """various one-target views get the right value for single_result"""
        eid = self.client.ids[-1]
        ar = self.client[eid].apply_async(lambda : 42)
        self.assertEqual(ar.get(), 42)
        ar = self.client[[eid]].apply_async(lambda : 42)
        self.assertEqual(ar.get(), [42])
        ar = self.client[-1:].apply_async(lambda : 42)
        self.assertEqual(ar.get(), [42])

    def test_get_after_done(self):
        ar = self.client[-1].apply_async(lambda : 42)
        ar.wait()
        self.assertTrue(ar.ready())
        self.assertEqual(ar.get(), 42)
        self.assertEqual(ar.get(), 42)

    def test_get_before_done(self):
        ar = self.client[-1].apply_async(wait, 0.1)
        self.assertRaises(TimeoutError, ar.get, 0)
        ar.wait(0)
        self.assertFalse(ar.ready())
        self.assertEqual(ar.get(), 0.1)

    def test_get_after_error(self):
        ar = self.client[-1].apply_async(lambda : 1/0)
        ar.wait(10)
        self.assertRaisesRemote(ZeroDivisionError, ar.get)
        self.assertRaisesRemote(ZeroDivisionError, ar.get)
        self.assertRaisesRemote(ZeroDivisionError, ar.get_dict)
    
    def test_get_dict(self):
        n = len(self.client)
        ar = self.client[:].apply_async(lambda : 5)
        self.assertEqual(ar.get(), [5]*n)
        d = ar.get_dict()
        self.assertEqual(sorted(d.keys()), sorted(self.client.ids))
        for eid,r in iteritems(d):
            self.assertEqual(r, 5)
    
    def test_get_dict_single(self):
        view = self.client[-1]
        for v in (list(range(5)), 5, ('abc', 'def'), 'string'):
            ar = view.apply_async(echo, v)
            self.assertEqual(ar.get(), v)
            d = ar.get_dict()
            self.assertEqual(d, {view.targets : v})
    
    def test_get_dict_bad(self):
        ar = self.client[:].apply_async(lambda : 5)
        ar2 = self.client[:].apply_async(lambda : 5)
        ar = self.client.get_result(ar.msg_ids + ar2.msg_ids)
        self.assertRaises(ValueError, ar.get_dict)
    
    def test_list_amr(self):
        ar = self.client.load_balanced_view().map_async(wait, [0.1]*5)
        rlist = list(ar)
    
    def test_getattr(self):
        ar = self.client[:].apply_async(wait, 0.5)
        self.assertEqual(ar.engine_id, [None] * len(ar))
        self.assertRaises(AttributeError, lambda : ar._foo)
        self.assertRaises(AttributeError, lambda : ar.__length_hint__())
        self.assertRaises(AttributeError, lambda : ar.foo)
        self.assertFalse(hasattr(ar, '__length_hint__'))
        self.assertFalse(hasattr(ar, 'foo'))
        self.assertTrue(hasattr(ar, 'engine_id'))
        ar.get(5)
        self.assertRaises(AttributeError, lambda : ar._foo)
        self.assertRaises(AttributeError, lambda : ar.__length_hint__())
        self.assertRaises(AttributeError, lambda : ar.foo)
        self.assertTrue(isinstance(ar.engine_id, list))
        self.assertEqual(ar.engine_id, ar['engine_id'])
        self.assertFalse(hasattr(ar, '__length_hint__'))
        self.assertFalse(hasattr(ar, 'foo'))
        self.assertTrue(hasattr(ar, 'engine_id'))

    def test_getitem(self):
        ar = self.client[:].apply_async(wait, 0.5)
        self.assertEqual(ar['engine_id'], [None] * len(ar))
        self.assertRaises(KeyError, lambda : ar['foo'])
        ar.get(5)
        self.assertRaises(KeyError, lambda : ar['foo'])
        self.assertTrue(isinstance(ar['engine_id'], list))
        self.assertEqual(ar.engine_id, ar['engine_id'])
    
    def test_single_result(self):
        ar = self.client[-1].apply_async(wait, 0.5)
        self.assertRaises(KeyError, lambda : ar['foo'])
        self.assertEqual(ar['engine_id'], None)
        self.assertTrue(ar.get(5) == 0.5)
        self.assertTrue(isinstance(ar['engine_id'], int))
        self.assertTrue(isinstance(ar.engine_id, int))
        self.assertEqual(ar.engine_id, ar['engine_id'])
    
    def test_abort(self):
        e = self.client[-1]
        ar = e.execute('import time; time.sleep(1)', block=False)
        ar2 = e.apply_async(lambda : 2)
        ar2.abort()
        self.assertRaises(error.TaskAborted, ar2.get)
        ar.get()
    
    def test_len(self):
        v = self.client.load_balanced_view()
        ar = v.map_async(lambda x: x, list(range(10)))
        self.assertEqual(len(ar), 10)
        ar = v.apply_async(lambda x: x, list(range(10)))
        self.assertEqual(len(ar), 1)
        ar = self.client[:].apply_async(lambda x: x, list(range(10)))
        self.assertEqual(len(ar), len(self.client.ids))
    
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
            self.assertEqual(hr.serial_time, ar.serial_time)
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
        self.assertEqual(io.stderr, '')
        self.assertEqual('5555\n', io.stdout)

        ar = v.execute("a=5")
        ar.get(5)
        with capture_output() as io:
            ar.display_outputs()
        self.assertEqual(io.stderr, '')
        self.assertEqual(io.stdout, '')
        
    def test_display_empty_streams_type(self):
        """empty stdout/err are not displayed (groupby type)"""
        self.minimum_engines(1)
        
        v = self.client[:]
        ar = v.execute("print (5555)")
        ar.get(5)
        with capture_output() as io:
            ar.display_outputs()
        self.assertEqual(io.stderr, '')
        self.assertEqual(io.stdout.count('5555'), len(v), io.stdout)
        self.assertFalse('\n\n' in io.stdout, io.stdout)
        self.assertEqual(io.stdout.count('[stdout:'), len(v), io.stdout)

        ar = v.execute("a=5")
        ar.get(5)
        with capture_output() as io:
            ar.display_outputs()
        self.assertEqual(io.stderr, '')
        self.assertEqual(io.stdout, '')

    def test_display_empty_streams_engine(self):
        """empty stdout/err are not displayed (groupby engine)"""
        self.minimum_engines(1)
        
        v = self.client[:]
        ar = v.execute("print (5555)")
        ar.get(5)
        with capture_output() as io:
            ar.display_outputs('engine')
        self.assertEqual(io.stderr, '')
        self.assertEqual(io.stdout.count('5555'), len(v), io.stdout)
        self.assertFalse('\n\n' in io.stdout, io.stdout)
        self.assertEqual(io.stdout.count('[stdout:'), len(v), io.stdout)

        ar = v.execute("a=5")
        ar.get(5)
        with capture_output() as io:
            ar.display_outputs('engine')
        self.assertEqual(io.stderr, '')
        self.assertEqual(io.stdout, '')
    
    def test_await_data(self):
        """asking for ar.data flushes outputs"""
        self.minimum_engines(1)
        
        v = self.client[-1]
        ar = v.execute('\n'.join([
            "import time",
            "from IPython.kernel.zmq.datapub import publish_data",
            "for i in range(5):",
            "    publish_data(dict(i=i))",
            "    time.sleep(0.1)",
        ]), block=False)
        found = set()
        tic = time.time()
        # timeout after 10s
        while time.time() <= tic + 10:
            if ar.data:
                i = ar.data['i']
                found.add(i)
                if i == 4:
                    break
            time.sleep(0.05)
        
        ar.get(5)
        nt.assert_in(4, found)
        self.assertTrue(len(found) > 1, "should have seen data multiple times, but got: %s" % found)
    
    def test_not_single_result(self):
        save_build = self.client._build_targets
        def single_engine(*a, **kw):
            idents, targets = save_build(*a, **kw)
            return idents[:1], targets[:1]
        ids = single_engine('all')[1]
        self.client._build_targets = single_engine
        for targets in ('all', None, ids):
            dv = self.client.direct_view(targets=targets)
            ar = dv.apply_async(lambda : 5)
            self.assertEqual(ar.get(10), [5])
        self.client._build_targets = save_build


