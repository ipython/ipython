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


from IPython.parallel.error import TimeoutError

from IPython.parallel.tests import add_engines
from .clienttest import ClusterTestCase

def setup():
    add_engines(2)

def wait(n):
    import time
    time.sleep(n)
    return n

class AsyncResultTest(ClusterTestCase):

    def test_single_result(self):
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


