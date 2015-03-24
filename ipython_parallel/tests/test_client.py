"""Tests for parallel client.py"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import division

import time
from datetime import datetime

import zmq

from IPython import parallel
from IPython.parallel.client import client as clientmod
from IPython.parallel import error
from IPython.parallel import AsyncResult, AsyncHubResult
from IPython.parallel import LoadBalancedView, DirectView

from .clienttest import ClusterTestCase, segfault, wait, add_engines

def setup():
    add_engines(4, total=True)

class TestClient(ClusterTestCase):
    
    def test_ids(self):
        n = len(self.client.ids)
        self.add_engines(2)
        self.assertEqual(len(self.client.ids), n+2)
    
    def test_iter(self):
        self.minimum_engines(4)
        engine_ids = [ view.targets for view in self.client ]
        self.assertEqual(engine_ids, self.client.ids)
    
    def test_view_indexing(self):
        """test index access for views"""
        self.minimum_engines(4)
        targets = self.client._build_targets('all')[-1]
        v = self.client[:]
        self.assertEqual(v.targets, targets)
        t = self.client.ids[2]
        v = self.client[t]
        self.assertTrue(isinstance(v, DirectView))
        self.assertEqual(v.targets, t)
        t = self.client.ids[2:4]
        v = self.client[t]
        self.assertTrue(isinstance(v, DirectView))
        self.assertEqual(v.targets, t)
        v = self.client[::2]
        self.assertTrue(isinstance(v, DirectView))
        self.assertEqual(v.targets, targets[::2])
        v = self.client[1::3]
        self.assertTrue(isinstance(v, DirectView))
        self.assertEqual(v.targets, targets[1::3])
        v = self.client[:-3]
        self.assertTrue(isinstance(v, DirectView))
        self.assertEqual(v.targets, targets[:-3])
        v = self.client[-1]
        self.assertTrue(isinstance(v, DirectView))
        self.assertEqual(v.targets, targets[-1])
        self.assertRaises(TypeError, lambda : self.client[None])
    
    def test_lbview_targets(self):
        """test load_balanced_view targets"""
        v = self.client.load_balanced_view()
        self.assertEqual(v.targets, None)
        v = self.client.load_balanced_view(-1)
        self.assertEqual(v.targets, [self.client.ids[-1]])
        v = self.client.load_balanced_view('all')
        self.assertEqual(v.targets, None)
    
    def test_dview_targets(self):
        """test direct_view targets"""
        v = self.client.direct_view()
        self.assertEqual(v.targets, 'all')
        v = self.client.direct_view('all')
        self.assertEqual(v.targets, 'all')
        v = self.client.direct_view(-1)
        self.assertEqual(v.targets, self.client.ids[-1])
    
    def test_lazy_all_targets(self):
        """test lazy evaluation of rc.direct_view('all')"""
        v = self.client.direct_view()
        self.assertEqual(v.targets, 'all')
        
        def double(x):
            return x*2
        seq = list(range(100))
        ref = [ double(x) for x in seq ]
        
        # add some engines, which should be used
        self.add_engines(1)
        n1 = len(self.client.ids)
        
        # simple apply
        r = v.apply_sync(lambda : 1)
        self.assertEqual(r, [1] * n1)
        
        # map goes through remotefunction
        r = v.map_sync(double, seq)
        self.assertEqual(r, ref)

        # add a couple more engines, and try again
        self.add_engines(2)
        n2 = len(self.client.ids)
        self.assertNotEqual(n2, n1)
        
        # apply
        r = v.apply_sync(lambda : 1)
        self.assertEqual(r, [1] * n2)
        
        # map
        r = v.map_sync(double, seq)
        self.assertEqual(r, ref)
    
    def test_targets(self):
        """test various valid targets arguments"""
        build = self.client._build_targets
        ids = self.client.ids
        idents,targets = build(None)
        self.assertEqual(ids, targets)
    
    def test_clear(self):
        """test clear behavior"""
        self.minimum_engines(2)
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
            self.assertRaisesRemote(NameError, self.client[i].get, 'a')
    
    def test_get_result(self):
        """test getting results from the Hub."""
        c = clientmod.Client(profile='iptest')
        t = c.ids[-1]
        ar = c[t].apply_async(wait, 1)
        # give the monitor time to notice the message
        time.sleep(.25)
        ahr = self.client.get_result(ar.msg_ids[0], owner=False)
        self.assertIsInstance(ahr, AsyncHubResult)
        self.assertEqual(ahr.get(), ar.get())
        ar2 = self.client.get_result(ar.msg_ids[0])
        self.assertNotIsInstance(ar2, AsyncHubResult)
        self.assertEqual(ahr.get(), ar2.get())
        c.close()
    
    def test_get_execute_result(self):
        """test getting execute results from the Hub."""
        c = clientmod.Client(profile='iptest')
        t = c.ids[-1]
        cell = '\n'.join([
            'import time',
            'time.sleep(0.25)',
            '5'
        ])
        ar = c[t].execute("import time; time.sleep(1)", silent=False)
        # give the monitor time to notice the message
        time.sleep(.25)
        ahr = self.client.get_result(ar.msg_ids[0], owner=False)
        self.assertIsInstance(ahr, AsyncHubResult)
        self.assertEqual(ahr.get().execute_result, ar.get().execute_result)
        ar2 = self.client.get_result(ar.msg_ids[0])
        self.assertNotIsInstance(ar2, AsyncHubResult)
        self.assertEqual(ahr.get(), ar2.get())
        c.close()
    
    def test_ids_list(self):
        """test client.ids"""
        ids = self.client.ids
        self.assertEqual(ids, self.client._ids)
        self.assertFalse(ids is self.client._ids)
        ids.remove(ids[-1])
        self.assertNotEqual(ids, self.client._ids)
    
    def test_queue_status(self):
        ids = self.client.ids
        id0 = ids[0]
        qs = self.client.queue_status(targets=id0)
        self.assertTrue(isinstance(qs, dict))
        self.assertEqual(sorted(qs.keys()), ['completed', 'queue', 'tasks'])
        allqs = self.client.queue_status()
        self.assertTrue(isinstance(allqs, dict))
        intkeys = list(allqs.keys())
        intkeys.remove('unassigned')
        print("intkeys", intkeys)
        intkeys = sorted(intkeys)
        ids = self.client.ids
        print("client.ids", ids)
        ids = sorted(self.client.ids)
        self.assertEqual(intkeys, ids)
        unassigned = allqs.pop('unassigned')
        for eid,qs in allqs.items():
            self.assertTrue(isinstance(qs, dict))
            self.assertEqual(sorted(qs.keys()), ['completed', 'queue', 'tasks'])

    def test_shutdown(self):
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
        self.assertEqual(len(before)+len(after),len(hist))
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
            self.assertEqual(set(rec.keys()), set(['msg_id', 'submitted', 'completed']))
    
    def test_db_query_default_keys(self):
        """default db_query excludes buffers"""
        found = self.client.db_query({'msg_id': {'$ne' : ''}})
        for rec in found:
            keys = set(rec.keys())
            self.assertFalse('buffers' in keys, "'buffers' should not be in: %s" % keys)
            self.assertFalse('result_buffers' in keys, "'result_buffers' should not be in: %s" % keys)
    
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
    
    def test_db_query_get_result(self):
        """pop in db_query shouldn't pop from result itself"""
        self.client[:].apply_sync(lambda : 1)
        found = self.client.db_query({'msg_id': {'$ne' : ''}})
        rc2 = clientmod.Client(profile='iptest')
        # If this bug is not fixed, this call will hang:
        ar = rc2.get_result(self.client.history[-1])
        ar.wait(2)
        self.assertTrue(ar.ready())
        ar.get()
        rc2.close()
    
    def test_db_query_in(self):
        """test db query with '$in','$nin' operators"""
        hist = self.client.hub_history()
        even = hist[::2]
        odd = hist[1::2]
        recs = self.client.db_query({ 'msg_id' : {'$in' : even}})
        found = [ r['msg_id'] for r in recs ]
        self.assertEqual(set(even), set(found))
        recs = self.client.db_query({ 'msg_id' : {'$nin' : even}})
        found = [ r['msg_id'] for r in recs ]
        self.assertEqual(set(odd), set(found))
    
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
        self.assertEqual(self.client.hub_history()[-1:],ar.msg_ids)
    
    def _wait_for_idle(self):
        """wait for the cluster to become idle, according to the everyone."""
        rc = self.client
        
        # step 0. wait for local results
        # this should be sufficient 99% of the time.
        rc.wait(timeout=5)
        
        # step 1. wait for all requests to be noticed
        # timeout 5s, polling every 100ms
        msg_ids = set(rc.history)
        hub_hist = rc.hub_history()
        for i in range(50):
            if msg_ids.difference(hub_hist):
                time.sleep(0.1)
                hub_hist = rc.hub_history()
            else:
                break
        
        self.assertEqual(len(msg_ids.difference(hub_hist)), 0)
        
        # step 2. wait for all requests to be done
        # timeout 5s, polling every 100ms
        qs = rc.queue_status()
        for i in range(50):
            if qs['unassigned'] or any(qs[eid]['tasks'] + qs[eid]['queue'] for eid in qs if eid != 'unassigned'):
                time.sleep(0.1)
                qs = rc.queue_status()
            else:
                break
        
        # ensure Hub up to date:
        self.assertEqual(qs['unassigned'], 0)
        for eid in [ eid for eid in qs if eid != 'unassigned' ]:
            self.assertEqual(qs[eid]['tasks'], 0)
            self.assertEqual(qs[eid]['queue'], 0)
    
    
    def test_resubmit(self):
        def f():
            import random
            return random.random()
        v = self.client.load_balanced_view()
        ar = v.apply_async(f)
        r1 = ar.get(1)
        # give the Hub a chance to notice:
        self._wait_for_idle()
        ahr = self.client.resubmit(ar.msg_ids)
        r2 = ahr.get(1)
        self.assertFalse(r1 == r2)

    def test_resubmit_chain(self):
        """resubmit resubmitted tasks"""
        v = self.client.load_balanced_view()
        ar = v.apply_async(lambda x: x, 'x'*1024)
        ar.get()
        self._wait_for_idle()
        ars = [ar]
        
        for i in range(10):
            ar = ars[-1]
            ar2 = self.client.resubmit(ar.msg_ids)
        
        [ ar.get() for ar in ars ]

    def test_resubmit_header(self):
        """resubmit shouldn't clobber the whole header"""
        def f():
            import random
            return random.random()
        v = self.client.load_balanced_view()
        v.retries = 1
        ar = v.apply_async(f)
        r1 = ar.get(1)
        # give the Hub a chance to notice:
        self._wait_for_idle()
        ahr = self.client.resubmit(ar.msg_ids)
        ahr.get(1)
        time.sleep(0.5)
        records = self.client.db_query({'msg_id': {'$in': ar.msg_ids + ahr.msg_ids}}, keys='header')
        h1,h2 = [ r['header'] for r in records ]
        for key in set(h1.keys()).union(set(h2.keys())):
            if key in ('msg_id', 'date'):
                self.assertNotEqual(h1[key], h2[key])
            else:
                self.assertEqual(h1[key], h2[key])

    def test_resubmit_aborted(self):
        def f():
            import random
            return random.random()
        v = self.client.load_balanced_view()
        # restrict to one engine, so we can put a sleep
        # ahead of the task, so it will get aborted
        eid = self.client.ids[-1]
        v.targets = [eid]
        sleep = v.apply_async(time.sleep, 0.5)
        ar = v.apply_async(f)
        ar.abort()
        self.assertRaises(error.TaskAborted, ar.get)
        # Give the Hub a chance to get up to date:
        self._wait_for_idle()
        ahr = self.client.resubmit(ar.msg_ids)
        r2 = ahr.get(1)

    def test_resubmit_inflight(self):
        """resubmit of inflight task"""
        v = self.client.load_balanced_view()
        ar = v.apply_async(time.sleep,1)
        # give the message a chance to arrive
        time.sleep(0.2)
        ahr = self.client.resubmit(ar.msg_ids)
        ar.get(2)
        ahr.get(2)

    def test_resubmit_badkey(self):
        """ensure KeyError on resubmit of nonexistant task"""
        self.assertRaisesRemote(KeyError, self.client.resubmit, ['invalid'])

    def test_purge_hub_results(self):
        # ensure there are some tasks
        for i in range(5):
            self.client[:].apply_sync(lambda : 1)
        # Wait for the Hub to realise the result is done:
        # This prevents a race condition, where we
        # might purge a result the Hub still thinks is pending.
        self._wait_for_idle()
        rc2 = clientmod.Client(profile='iptest')
        hist = self.client.hub_history()
        ahr = rc2.get_result([hist[-1]])
        ahr.wait(10)
        self.client.purge_hub_results(hist[-1])
        newhist = self.client.hub_history()
        self.assertEqual(len(newhist)+1,len(hist))
        rc2.spin()
        rc2.close()

    def test_purge_local_results(self):
        # ensure there are some tasks
        res = []
        for i in range(5):
            res.append(self.client[:].apply_async(lambda : 1))
        self._wait_for_idle()
        self.client.wait(10) # wait for the results to come back
        before = len(self.client.results)
        self.assertEqual(len(self.client.metadata),before)
        self.client.purge_local_results(res[-1])
        self.assertEqual(len(self.client.results),before-len(res[-1]), msg="Not removed from results")
        self.assertEqual(len(self.client.metadata),before-len(res[-1]), msg="Not removed from metadata")
    
    def test_purge_local_results_outstanding(self):
        v = self.client[-1]
        ar = v.apply_async(lambda : 1)
        msg_id = ar.msg_ids[0]
        ar.owner = False
        ar.get()
        self._wait_for_idle()
        ar2 = v.apply_async(time.sleep, 1)
        self.assertIn(msg_id, self.client.results)
        self.assertIn(msg_id, self.client.metadata)
        self.client.purge_local_results(ar)
        self.assertNotIn(msg_id, self.client.results)
        self.assertNotIn(msg_id, self.client.metadata)
        with self.assertRaises(RuntimeError):
            self.client.purge_local_results(ar2)
        ar2.get()
        self.client.purge_local_results(ar2)
    
    def test_purge_all_local_results_outstanding(self):
        v = self.client[-1]
        ar = v.apply_async(time.sleep, 1)
        with self.assertRaises(RuntimeError):
            self.client.purge_local_results('all')
        ar.get()
        self.client.purge_local_results('all')
    
    def test_purge_all_hub_results(self):
        self.client.purge_hub_results('all')
        hist = self.client.hub_history()
        self.assertEqual(len(hist), 0)

    def test_purge_all_local_results(self):
        self.client.purge_local_results('all')
        self.assertEqual(len(self.client.results), 0, msg="Results not empty")
        self.assertEqual(len(self.client.metadata), 0, msg="metadata not empty")

    def test_purge_all_results(self):
        # ensure there are some tasks
        for i in range(5):
            self.client[:].apply_sync(lambda : 1)
        self.client.wait(10)
        self._wait_for_idle()
        self.client.purge_results('all')
        self.assertEqual(len(self.client.results), 0, msg="Results not empty")
        self.assertEqual(len(self.client.metadata), 0, msg="metadata not empty")
        hist = self.client.hub_history()
        self.assertEqual(len(hist), 0, msg="hub history not empty")
        
    def test_purge_everything(self):
        # ensure there are some tasks
        for i in range(5):
            self.client[:].apply_sync(lambda : 1)
        self.client.wait(10)
        self._wait_for_idle()
        self.client.purge_everything()
        # The client results
        self.assertEqual(len(self.client.results), 0, msg="Results not empty")
        self.assertEqual(len(self.client.metadata), 0, msg="metadata not empty")
        # The client "bookkeeping"
        self.assertEqual(len(self.client.session.digest_history), 0, msg="session digest not empty")
        self.assertEqual(len(self.client.history), 0, msg="client history not empty")
        # the hub results
        hist = self.client.hub_history()
        self.assertEqual(len(hist), 0, msg="hub history not empty")
        
    
    def test_spin_thread(self):
        self.client.spin_thread(0.01)
        ar = self.client[-1].apply_async(lambda : 1)
        md = self.client.metadata[ar.msg_ids[0]]
        # 3s timeout, 100ms poll
        for i in range(30):
            time.sleep(0.1)
            if md['received'] is not None:
                break
        self.assertIsInstance(md['received'], datetime)
    
    def test_stop_spin_thread(self):
        self.client.spin_thread(0.01)
        self.client.stop_spin_thread()
        ar = self.client[-1].apply_async(lambda : 1)
        md = self.client.metadata[ar.msg_ids[0]]
        # 500ms timeout, 100ms poll
        for i in range(5):
            time.sleep(0.1)
            self.assertIsNone(md['received'], None)
    
    def test_activate(self):
        ip = get_ipython()
        magics = ip.magics_manager.magics
        self.assertTrue('px' in magics['line'])
        self.assertTrue('px' in magics['cell'])
        v0 = self.client.activate(-1, '0')
        self.assertTrue('px0' in magics['line'])
        self.assertTrue('px0' in magics['cell'])
        self.assertEqual(v0.targets, self.client.ids[-1])
        v0 = self.client.activate('all', 'all')
        self.assertTrue('pxall' in magics['line'])
        self.assertTrue('pxall' in magics['cell'])
        self.assertEqual(v0.targets, 'all')
