"""Tests for parallel client.py"""

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
from tempfile import mktemp

import zmq

from IPython.zmq.parallel import client as clientmod
from IPython.zmq.parallel import error
from IPython.zmq.parallel.asyncresult import AsyncResult, AsyncHubResult
from IPython.zmq.parallel.view import LoadBalancedView, DirectView

from clienttest import ClusterTestCase, segfault, wait, add_engines

def setup():
    add_engines(4)

class TestClient(ClusterTestCase):
    
    def test_ids(self):
        n = len(self.client.ids)
        self.add_engines(3)
        self.assertEquals(len(self.client.ids), n+3)
    
    def test_view_indexing(self):
        """test index access for views"""
        self.add_engines(2)
        targets = self.client._build_targets('all')[-1]
        v = self.client[:]
        self.assertEquals(v.targets, targets)
        t = self.client.ids[2]
        v = self.client[t]
        self.assert_(isinstance(v, DirectView))
        self.assertEquals(v.targets, t)
        t = self.client.ids[2:4]
        v = self.client[t]
        self.assert_(isinstance(v, DirectView))
        self.assertEquals(v.targets, t)
        v = self.client[::2]
        self.assert_(isinstance(v, DirectView))
        self.assertEquals(v.targets, targets[::2])
        v = self.client[1::3]
        self.assert_(isinstance(v, DirectView))
        self.assertEquals(v.targets, targets[1::3])
        v = self.client[:-3]
        self.assert_(isinstance(v, DirectView))
        self.assertEquals(v.targets, targets[:-3])
        v = self.client[-1]
        self.assert_(isinstance(v, DirectView))
        self.assertEquals(v.targets, targets[-1])
        self.assertRaises(TypeError, lambda : self.client[None])
    
    def test_targets(self):
        """test various valid targets arguments"""
        build = self.client._build_targets
        ids = self.client.ids
        idents,targets = build(None)
        self.assertEquals(ids, targets)
    
    def test_clear(self):
        """test clear behavior"""
        # self.add_engines(2)
        v = self.client[:]
        v.block=True
        v.push(dict(a=5))
        v.pull('a')
        id0 = self.client.ids[-1]
        self.client.clear(targets=id0)
        self.client[:-1].pull('a')
        self.assertRaisesRemote(NameError, self.client[id0].get, 'a')
        self.client.clear(block=True)
        for i in self.client.ids:
            # print i
            self.assertRaisesRemote(NameError, self.client[i].get, 'a')
    
    def test_get_result(self):
        """test getting results from the Hub."""
        c = clientmod.Client(profile='iptest')
        # self.add_engines(1)
        t = c.ids[-1]
        ar = c[t].apply_async(wait, 1)
        # give the monitor time to notice the message
        time.sleep(.25)
        ahr = self.client.get_result(ar.msg_ids)
        self.assertTrue(isinstance(ahr, AsyncHubResult))
        self.assertEquals(ahr.get(), ar.get())
        ar2 = self.client.get_result(ar.msg_ids)
        self.assertFalse(isinstance(ar2, AsyncHubResult))
        c.close()
    
    def test_ids_list(self):
        """test client.ids"""
        # self.add_engines(2)
        ids = self.client.ids
        self.assertEquals(ids, self.client._ids)
        self.assertFalse(ids is self.client._ids)
        ids.remove(ids[-1])
        self.assertNotEquals(ids, self.client._ids)
    
    def test_queue_status(self):
        # self.addEngine(4)
        ids = self.client.ids
        id0 = ids[0]
        qs = self.client.queue_status(targets=id0)
        self.assertTrue(isinstance(qs, dict))
        self.assertEquals(sorted(qs.keys()), ['completed', 'queue', 'tasks'])
        allqs = self.client.queue_status()
        self.assertTrue(isinstance(allqs, dict))
        self.assertEquals(sorted(allqs.keys()), self.client.ids)
        for eid,qs in allqs.items():
            self.assertTrue(isinstance(qs, dict))
            self.assertEquals(sorted(qs.keys()), ['completed', 'queue', 'tasks'])

    def test_shutdown(self):
        # self.addEngine(4)
        ids = self.client.ids
        id0 = ids[0]
        self.client.shutdown(id0, block=True)
        while id0 in self.client.ids:
            time.sleep(0.1)
            self.client.spin()
        
        self.assertRaises(IndexError, lambda : self.client[id0])
        
    def test_result_status(self):
        pass
        # to be written
