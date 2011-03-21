import time
from tempfile import mktemp

import nose.tools as nt
import zmq

from IPython.zmq.parallel import client as clientmod
from IPython.zmq.parallel import error
from IPython.zmq.parallel.asyncresult import AsyncResult, AsyncHubResult
from IPython.zmq.parallel.view import LoadBalancedView, DirectView

from clienttest import ClusterTestCase, segfault, wait

class TestClient(ClusterTestCase):
    
    def test_ids(self):
        n = len(self.client.ids)
        self.add_engines(3)
        self.assertEquals(len(self.client.ids), n+3)
    
    def test_segfault_task(self):
        """test graceful handling of engine death (balanced)"""
        self.add_engines(1)
        ar = self.client.apply(segfault, block=False)
        self.assertRaisesRemote(error.EngineError, ar.get)
        eid = ar.engine_id
        while eid in self.client.ids:
            time.sleep(.01)
            self.client.spin()
    
    def test_segfault_mux(self):
        """test graceful handling of engine death (direct)"""
        self.add_engines(1)
        eid = self.client.ids[-1]
        ar = self.client[eid].apply_async(segfault)
        self.assertRaisesRemote(error.EngineError, ar.get)
        eid = ar.engine_id
        while eid in self.client.ids:
            time.sleep(.01)
            self.client.spin()
    
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
        nt.assert_raises(TypeError, lambda : self.client[None])
    
    def test_view_cache(self):
        """test that multiple view requests return the same object"""
        v = self.client[:2]
        v2 =self.client[:2]
        self.assertTrue(v is v2)
        v = self.client.view()
        v2 = self.client.view(balanced=True)
        self.assertTrue(v is v2)
    
    def test_targets(self):
        """test various valid targets arguments"""
        build = self.client._build_targets
        ids = self.client.ids
        idents,targets = build(None)
        self.assertEquals(ids, targets)
    
    def test_clear(self):
        """test clear behavior"""
        self.add_engines(2)
        self.client.block=True
        self.client.push(dict(a=5))
        self.client.pull('a')
        id0 = self.client.ids[-1]
        self.client.clear(targets=id0)
        self.client.pull('a', targets=self.client.ids[:-1])
        self.assertRaisesRemote(NameError, self.client.pull, 'a')
        self.client.clear()
        for i in self.client.ids:
            self.assertRaisesRemote(NameError, self.client.pull, 'a', targets=i)
            
    
    def test_push_pull(self):
        """test pushing and pulling"""
        data = dict(a=10, b=1.05, c=range(10), d={'e':(1,2),'f':'hi'})
        t = self.client.ids[-1]
        self.add_engines(2)
        push = self.client.push
        pull = self.client.pull
        self.client.block=True
        nengines = len(self.client)
        push({'data':data}, targets=t)
        d = pull('data', targets=t)
        self.assertEquals(d, data)
        push({'data':data})
        d = pull('data')
        self.assertEquals(d, nengines*[data])
        ar = push({'data':data}, block=False)
        self.assertTrue(isinstance(ar, AsyncResult))
        r = ar.get()
        ar = pull('data', block=False)
        self.assertTrue(isinstance(ar, AsyncResult))
        r = ar.get()
        self.assertEquals(r, nengines*[data])
        push(dict(a=10,b=20))
        r = pull(('a','b'))
        self.assertEquals(r, nengines*[[10,20]])
    
    def test_push_pull_function(self):
        "test pushing and pulling functions"
        def testf(x):
            return 2.0*x
        
        self.add_engines(4)
        t = self.client.ids[-1]
        self.client.block=True
        push = self.client.push
        pull = self.client.pull
        execute = self.client.execute
        push({'testf':testf}, targets=t)
        r = pull('testf', targets=t)
        self.assertEqual(r(1.0), testf(1.0))
        execute('r = testf(10)', targets=t)
        r = pull('r', targets=t)
        self.assertEquals(r, testf(10))
        ar = push({'testf':testf}, block=False)
        ar.get()
        ar = pull('testf', block=False)
        rlist = ar.get()
        for r in rlist:
            self.assertEqual(r(1.0), testf(1.0))
        execute("def g(x): return x*x", targets=t)
        r = pull(('testf','g'),targets=t)
        self.assertEquals((r[0](10),r[1](10)), (testf(10), 100))
    
    def test_push_function_globals(self):
        """test that pushed functions have access to globals"""
        def geta():
            return a
        self.add_engines(1)
        v = self.client[-1]
        v.block=True
        v['f'] = geta
        self.assertRaisesRemote(NameError, v.execute, 'b=f()')
        v.execute('a=5')
        v.execute('b=f()')
        self.assertEquals(v['b'], 5)
    
    def test_push_function_defaults(self):
        """test that pushed functions preserve default args"""
        def echo(a=10):
            return a
        self.add_engines(1)
        v = self.client[-1]
        v.block=True
        v['f'] = echo
        v.execute('b=f()')
        self.assertEquals(v['b'], 10)

    def test_get_result(self):
        """test getting results from the Hub."""
        c = clientmod.Client(profile='iptest')
        self.add_engines(1)
        ar = c.apply(wait, (1,), block=False, targets=t)
        # give the monitor time to notice the message
        time.sleep(.25)
        ahr = self.client.get_result(ar.msg_ids)
        self.assertTrue(isinstance(ahr, AsyncHubResult))
        self.assertEquals(ahr.get(), ar.get())
        ar2 = self.client.get_result(ar.msg_ids)
        self.assertFalse(isinstance(ar2, AsyncHubResult))
    
    def test_ids_list(self):
        """test client.ids"""
        self.add_engines(2)
        ids = self.client.ids
        self.assertEquals(ids, self.client._ids)
        self.assertFalse(ids is self.client._ids)
        ids.remove(ids[-1])
        self.assertNotEquals(ids, self.client._ids)
    
    def test_run_newline(self):
        """test that run appends newline to files"""
        tmpfile = mktemp()
        with open(tmpfile, 'w') as f:
            f.write("""def g():
                return 5
                """)
        v = self.client[-1]
        v.run(tmpfile, block=True)
        self.assertEquals(v.apply_sync(lambda : g()), 5)

    def test_apply_tracked(self):
        """test tracking for apply"""
        # self.add_engines(1)
        t = self.client.ids[-1]
        self.client.block=False
        def echo(n=1024*1024, **kwargs):
            return self.client.apply(lambda x: x, args=('x'*n,), targets=t, **kwargs)
        ar = echo(1)
        self.assertTrue(ar._tracker is None)
        self.assertTrue(ar.sent)
        ar = echo(track=True)
        self.assertTrue(isinstance(ar._tracker, zmq.MessageTracker))
        self.assertEquals(ar.sent, ar._tracker.done)
        ar._tracker.wait()
        self.assertTrue(ar.sent)
        
    def test_push_tracked(self):
        t = self.client.ids[-1]
        ns = dict(x='x'*1024*1024)
        ar = self.client.push(ns, targets=t, block=False)
        self.assertTrue(ar._tracker is None)
        self.assertTrue(ar.sent)
        
        ar = self.client.push(ns, targets=t, block=False, track=True)
        self.assertTrue(isinstance(ar._tracker, zmq.MessageTracker))
        self.assertEquals(ar.sent, ar._tracker.done)
        ar._tracker.wait()
        self.assertTrue(ar.sent)
        ar.get()
        
    def test_scatter_tracked(self):
        t = self.client.ids
        x='x'*1024*1024
        ar = self.client.scatter('x', x, targets=t, block=False)
        self.assertTrue(ar._tracker is None)
        self.assertTrue(ar.sent)
        
        ar = self.client.scatter('x', x, targets=t, block=False, track=True)
        self.assertTrue(isinstance(ar._tracker, zmq.MessageTracker))
        self.assertEquals(ar.sent, ar._tracker.done)
        ar._tracker.wait()
        self.assertTrue(ar.sent)
        ar.get()
    
    def test_remote_reference(self):
        v = self.client[-1]
        v['a'] = 123
        ra = clientmod.Reference('a')
        b = v.apply_sync(lambda x: x, ra)
        self.assertEquals(b, 123)


