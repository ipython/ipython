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

