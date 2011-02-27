import time

import nose.tools as nt

from IPython.zmq.parallel.asyncresult import AsyncResult
from IPython.zmq.parallel.view import LoadBalancedView, DirectView

from clienttest import ClusterTestCase, segfault

class TestClient(ClusterTestCase):
    
    def test_ids(self):
        self.assertEquals(len(self.client.ids), 1)
        self.add_engines(3)
        self.assertEquals(len(self.client.ids), 4)
    
    def test_segfault(self):
        self.add_engines(1)
        eid = self.client.ids[-1]
        self.client[eid].apply(segfault)
        while eid in self.client.ids:
            time.sleep(.01)
            self.client.spin()
    
    def test_view_indexing(self):
        self.add_engines(4)
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
        pass
    
    def test_clear(self):
        """test clear behavior"""
        # self.add_engines(4)
        # self.client.push()
    
    def test_push_pull(self):
        """test pushing and pulling"""
        data = dict(a=10, b=1.05, c=range(10), d={'e':(1,2),'f':'hi'})
        self.add_engines(4)
        push = self.client.push
        pull = self.client.pull
        self.client.block=True
        nengines = len(self.client)
        push({'data':data}, targets=0)
        d = pull('data', targets=0)
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
        self.client.block=True
        push = self.client.push
        pull = self.client.pull
        execute = self.client.execute
        push({'testf':testf}, targets=0)
        r = pull('testf', targets=0)
        self.assertEqual(r(1.0), testf(1.0))
        execute('r = testf(10)', targets=0)
        r = pull('r', targets=0)
        self.assertEquals(r, testf(10))
        ar = push({'testf':testf}, block=False)
        ar.get()
        ar = pull('testf', block=False)
        rlist = ar.get()
        for r in rlist:
            self.assertEqual(r(1.0), testf(1.0))
        execute("def g(x): return x*x", targets=0)
        r = pull(('testf','g'),targets=0)
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
    
        