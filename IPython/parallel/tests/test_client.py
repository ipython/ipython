"""Tests for parallel client.py

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

from __future__ import division

import time
from datetime import datetime
from tempfile import mktemp

import zmq

from IPython.parallel.client import client as clientmod
from IPython.parallel import error
from IPython.parallel import AsyncResult, AsyncHubResult
from IPython.parallel import LoadBalancedView, DirectView

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
    
    def test_lbview_targets(self):
        """test load_balanced_view targets"""
        v = self.client.load_balanced_view()
        self.assertEquals(v.targets, None)
        v = self.client.load_balanced_view(-1)
        self.assertEquals(v.targets, [self.client.ids[-1]])
        v = self.client.load_balanced_view('all')
        self.assertEquals(v.targets, None)
    
    def test_dview_targets(self):
        """test direct_view targets"""
        v = self.client.direct_view()
        self.assertEquals(v.targets, 'all')
        v = self.client.direct_view('all')
        self.assertEquals(v.targets, 'all')
        v = self.client.direct_view(-1)
        self.assertEquals(v.targets, self.client.ids[-1])
    
    def test_lazy_all_targets(self):
        """test lazy evaluation of rc.direct_view('all')"""
        v = self.client.direct_view()
        self.assertEquals(v.targets, 'all')
        
        def double(x):
            return x*2
        seq = range(100)
        ref = [ double(x) for x in seq ]
        
        # add some engines, which should be used
        self.add_engines(2)
        n1 = len(self.client.ids)
        
        # simple apply
        r = v.apply_sync(lambda : 1)
        self.assertEquals(r, [1] * n1)
        
        # map goes through remotefunction
        r = v.map_sync(double, seq)
        self.assertEquals(r, ref)

        # add a couple more engines, and try again
        self.add_engines(2)
        n2 = len(self.client.ids)
        self.assertNotEquals(n2, n1)
        
        # apply
        r = v.apply_sync(lambda : 1)
        self.assertEquals(r, [1] * n2)
        
        # map
        r = v.map_sync(double, seq)
        self.assertEquals(r, ref)
    
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
        self.client.clear(targets=id0, block=True)
        a = self.client[:-1].get('a')
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
        intkeys = list(allqs.keys())
        intkeys.remove('unassigned')
        self.assertEquals(sorted(intkeys), sorted(self.client.ids))
        unassigned = allqs.pop('unassigned')
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
    
    def test_db_query_dt(self):
        """test db query by date"""
        hist = self.client.hub_history()
        middle = self.client.db_query({'msg_id' : hist[len(hist)//2]})[0]
        tic = middle['submitted']
        before = self.client.db_query({'submitted' : {'$lt' : tic}})
        after = self.client.db_query({'submitted' : {'$gte' : tic}})
        self.assertEquals(len(before)+len(after),len(hist))
        for b in before:
            self.assertTrue(b['submitted'] < tic)
        for a in after:
            self.assertTrue(a['submitted'] >= tic)
        same = self.client.db_query({'submitted' : tic})
        for s in same:
            self.assertTrue(s['submitted'] == tic)
    
    def test_db_query_keys(self):
        """test extracting subset of record keys"""
        found = self.client.db_query({'msg_id': {'$ne' : ''}},keys=['submitted', 'completed'])
        for rec in found:
            self.assertEquals(set(rec.keys()), set(['msg_id', 'submitted', 'completed']))
    
    def test_db_query_msg_id(self):
        """ensure msg_id is always in db queries"""
        found = self.client.db_query({'msg_id': {'$ne' : ''}},keys=['submitted', 'completed'])
        for rec in found:
            self.assertTrue('msg_id' in rec.keys())
        found = self.client.db_query({'msg_id': {'$ne' : ''}},keys=['submitted'])
        for rec in found:
            self.assertTrue('msg_id' in rec.keys())
        found = self.client.db_query({'msg_id': {'$ne' : ''}},keys=['msg_id'])
        for rec in found:
            self.assertTrue('msg_id' in rec.keys())
    
    def test_db_query_in(self):
        """test db query with '$in','$nin' operators"""
        hist = self.client.hub_history()
        even = hist[::2]
        odd = hist[1::2]
        recs = self.client.db_query({ 'msg_id' : {'$in' : even}})
        found = [ r['msg_id'] for r in recs ]
        self.assertEquals(set(even), set(found))
        recs = self.client.db_query({ 'msg_id' : {'$nin' : even}})
        found = [ r['msg_id'] for r in recs ]
        self.assertEquals(set(odd), set(found))
    
    def test_hub_history(self):
        hist = self.client.hub_history()
        recs = self.client.db_query({ 'msg_id' : {"$ne":''}})
        recdict = {}
        for rec in recs:
            recdict[rec['msg_id']] = rec
        
        latest = datetime(1984,1,1)
        for msg_id in hist:
            rec = recdict[msg_id]
            newt = rec['submitted']
            self.assertTrue(newt >= latest)
            latest = newt
        ar = self.client[-1].apply_async(lambda : 1)
        ar.get()
        time.sleep(0.25)
        self.assertEquals(self.client.hub_history()[-1:],ar.msg_ids)
    
    def test_resubmit(self):
        def f():
            import random
            return random.random()
        v = self.client.load_balanced_view()
        ar = v.apply_async(f)
        r1 = ar.get(1)
        # give the Hub a chance to notice:
        time.sleep(0.5)
        ahr = self.client.resubmit(ar.msg_ids)
        r2 = ahr.get(1)
        self.assertFalse(r1 == r2)

    def test_resubmit_inflight(self):
        """ensure ValueError on resubmit of inflight task"""
        v = self.client.load_balanced_view()
        ar = v.apply_async(time.sleep,1)
        # give the message a chance to arrive
        time.sleep(0.2)
        self.assertRaisesRemote(ValueError, self.client.resubmit, ar.msg_ids)
        ar.get(2)

    def test_resubmit_badkey(self):
        """ensure KeyError on resubmit of nonexistant task"""
        self.assertRaisesRemote(KeyError, self.client.resubmit, ['invalid'])

    def test_purge_results(self):
        # ensure there are some tasks
        for i in range(5):
            self.client[:].apply_sync(lambda : 1)
        # Wait for the Hub to realise the result is done:
        # This prevents a race condition, where we
        # might purge a result the Hub still thinks is pending.
        time.sleep(0.1)
        rc2 = clientmod.Client(profile='iptest')
        hist = self.client.hub_history()
        ahr = rc2.get_result([hist[-1]])
        ahr.wait(10)
        self.client.purge_results(hist[-1])
        newhist = self.client.hub_history()
        self.assertEquals(len(newhist)+1,len(hist))
        rc2.spin()
        rc2.close()
        
    def test_purge_all_results(self):
        self.client.purge_results('all')
        hist = self.client.hub_history()
        self.assertEquals(len(hist), 0)

