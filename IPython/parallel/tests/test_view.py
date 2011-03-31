"""test View objects"""
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

from IPython import parallel  as pmod
from IPython.parallel import error
from IPython.parallel.asyncresult import AsyncResult, AsyncHubResult, AsyncMapResult
from IPython.parallel.view import LoadBalancedView, DirectView
from IPython.parallel.util import interactive

from IPython.parallel.tests import add_engines

from .clienttest import ClusterTestCase, segfault, wait, skip_without

def setup():
    add_engines(3)

class TestView(ClusterTestCase):
    
    def test_segfault_task(self):
        """test graceful handling of engine death (balanced)"""
        # self.add_engines(1)
        ar = self.client[-1].apply_async(segfault)
        self.assertRaisesRemote(error.EngineError, ar.get)
        eid = ar.engine_id
        while eid in self.client.ids:
            time.sleep(.01)
            self.client.spin()
    
    def test_segfault_mux(self):
        """test graceful handling of engine death (direct)"""
        # self.add_engines(1)
        eid = self.client.ids[-1]
        ar = self.client[eid].apply_async(segfault)
        self.assertRaisesRemote(error.EngineError, ar.get)
        eid = ar.engine_id
        while eid in self.client.ids:
            time.sleep(.01)
            self.client.spin()
    
    def test_push_pull(self):
        """test pushing and pulling"""
        data = dict(a=10, b=1.05, c=range(10), d={'e':(1,2),'f':'hi'})
        t = self.client.ids[-1]
        v = self.client[t]
        push = v.push
        pull = v.pull
        v.block=True
        nengines = len(self.client)
        push({'data':data})
        d = pull('data')
        self.assertEquals(d, data)
        self.client[:].push({'data':data})
        d = self.client[:].pull('data', block=True)
        self.assertEquals(d, nengines*[data])
        ar = push({'data':data}, block=False)
        self.assertTrue(isinstance(ar, AsyncResult))
        r = ar.get()
        ar = self.client[:].pull('data', block=False)
        self.assertTrue(isinstance(ar, AsyncResult))
        r = ar.get()
        self.assertEquals(r, nengines*[data])
        self.client[:].push(dict(a=10,b=20))
        r = self.client[:].pull(('a','b'))
        self.assertEquals(r, nengines*[[10,20]])
    
    def test_push_pull_function(self):
        "test pushing and pulling functions"
        def testf(x):
            return 2.0*x
        
        t = self.client.ids[-1]
        self.client[t].block=True
        push = self.client[t].push
        pull = self.client[t].pull
        execute = self.client[t].execute
        push({'testf':testf})
        r = pull('testf')
        self.assertEqual(r(1.0), testf(1.0))
        execute('r = testf(10)')
        r = pull('r')
        self.assertEquals(r, testf(10))
        ar = self.client[:].push({'testf':testf}, block=False)
        ar.get()
        ar = self.client[:].pull('testf', block=False)
        rlist = ar.get()
        for r in rlist:
            self.assertEqual(r(1.0), testf(1.0))
        execute("def g(x): return x*x")
        r = pull(('testf','g'))
        self.assertEquals((r[0](10),r[1](10)), (testf(10), 100))
    
    def test_push_function_globals(self):
        """test that pushed functions have access to globals"""
        @interactive
        def geta():
            return a
        # self.add_engines(1)
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
        v = self.client[-1]
        v.block=True
        v['f'] = echo
        v.execute('b=f()')
        self.assertEquals(v['b'], 10)

    def test_get_result(self):
        """test getting results from the Hub."""
        c = pmod.Client(profile='iptest')
        # self.add_engines(1)
        t = c.ids[-1]
        v = c[t]
        v2 = self.client[t]
        ar = v.apply_async(wait, 1)
        # give the monitor time to notice the message
        time.sleep(.25)
        ahr = v2.get_result(ar.msg_ids)
        self.assertTrue(isinstance(ahr, AsyncHubResult))
        self.assertEquals(ahr.get(), ar.get())
        ar2 = v2.get_result(ar.msg_ids)
        self.assertFalse(isinstance(ar2, AsyncHubResult))
        c.spin()
        c.close()
    
    def test_run_newline(self):
        """test that run appends newline to files"""
        tmpfile = mktemp()
        with open(tmpfile, 'w') as f:
            f.write("""def g():
                return 5
                """)
        v = self.client[-1]
        v.run(tmpfile, block=True)
        self.assertEquals(v.apply_sync(lambda f: f(), pmod.Reference('g')), 5)

    def test_apply_tracked(self):
        """test tracking for apply"""
        # self.add_engines(1)
        t = self.client.ids[-1]
        v = self.client[t]
        v.block=False
        def echo(n=1024*1024, **kwargs):
            with v.temp_flags(**kwargs):
                return v.apply(lambda x: x, 'x'*n)
        ar = echo(1, track=False)
        self.assertTrue(isinstance(ar._tracker, zmq.MessageTracker))
        self.assertTrue(ar.sent)
        ar = echo(track=True)
        self.assertTrue(isinstance(ar._tracker, zmq.MessageTracker))
        self.assertEquals(ar.sent, ar._tracker.done)
        ar._tracker.wait()
        self.assertTrue(ar.sent)
        
    def test_push_tracked(self):
        t = self.client.ids[-1]
        ns = dict(x='x'*1024*1024)
        v = self.client[t]
        ar = v.push(ns, block=False, track=False)
        self.assertTrue(isinstance(ar._tracker, zmq.MessageTracker))
        self.assertTrue(ar.sent)
        
        ar = v.push(ns, block=False, track=True)
        self.assertTrue(isinstance(ar._tracker, zmq.MessageTracker))
        self.assertEquals(ar.sent, ar._tracker.done)
        ar._tracker.wait()
        self.assertTrue(ar.sent)
        ar.get()
        
    def test_scatter_tracked(self):
        t = self.client.ids
        x='x'*1024*1024
        ar = self.client[t].scatter('x', x, block=False, track=False)
        self.assertTrue(isinstance(ar._tracker, zmq.MessageTracker))
        self.assertTrue(ar.sent)
        
        ar = self.client[t].scatter('x', x, block=False, track=True)
        self.assertTrue(isinstance(ar._tracker, zmq.MessageTracker))
        self.assertEquals(ar.sent, ar._tracker.done)
        ar._tracker.wait()
        self.assertTrue(ar.sent)
        ar.get()
    
    def test_remote_reference(self):
        v = self.client[-1]
        v['a'] = 123
        ra = pmod.Reference('a')
        b = v.apply_sync(lambda x: x, ra)
        self.assertEquals(b, 123)


    def test_scatter_gather(self):
        view = self.client[:]
        seq1 = range(16)
        view.scatter('a', seq1)
        seq2 = view.gather('a', block=True)
        self.assertEquals(seq2, seq1)
        self.assertRaisesRemote(NameError, view.gather, 'asdf', block=True)
    
    @skip_without('numpy')
    def test_scatter_gather_numpy(self):
        import numpy
        from numpy.testing.utils import assert_array_equal, assert_array_almost_equal
        view = self.client[:]
        a = numpy.arange(64)
        view.scatter('a', a)
        b = view.gather('a', block=True)
        assert_array_equal(b, a)
    
    def test_map(self):
        view = self.client[:]
        def f(x):
            return x**2
        data = range(16)
        r = view.map_sync(f, data)
        self.assertEquals(r, map(f, data))
    
    def test_scatterGatherNonblocking(self):
        data = range(16)
        view = self.client[:]
        view.scatter('a', data, block=False)
        ar = view.gather('a', block=False)
        self.assertEquals(ar.get(), data)
    
    @skip_without('numpy')
    def test_scatter_gather_numpy_nonblocking(self):
        import numpy
        from numpy.testing.utils import assert_array_equal, assert_array_almost_equal
        a = numpy.arange(64)
        view = self.client[:]
        ar = view.scatter('a', a, block=False)
        self.assertTrue(isinstance(ar, AsyncResult))
        amr = view.gather('a', block=False)
        self.assertTrue(isinstance(amr, AsyncMapResult))
        assert_array_equal(amr.get(), a)

    def test_execute(self):
        view = self.client[:]
        # self.client.debug=True
        execute = view.execute
        ar = execute('c=30', block=False)
        self.assertTrue(isinstance(ar, AsyncResult))
        ar = execute('d=[0,1,2]', block=False)
        self.client.wait(ar, 1)
        self.assertEquals(len(ar.get()), len(self.client))
        for c in view['c']:
            self.assertEquals(c, 30)
    
    def test_abort(self):
        view = self.client[-1]
        ar = view.execute('import time; time.sleep(0.25)', block=False)
        ar2 = view.apply_async(lambda : 2)
        ar3 = view.apply_async(lambda : 3)
        view.abort(ar2)
        view.abort(ar3.msg_ids)
        self.assertRaises(error.TaskAborted, ar2.get)
        self.assertRaises(error.TaskAborted, ar3.get)
        
    def test_temp_flags(self):
        view = self.client[-1]
        view.block=True
        with view.temp_flags(block=False):
            self.assertFalse(view.block)
        self.assertTrue(view.block)
    
    def test_importer(self):
        view = self.client[-1]
        view.clear(block=True)
        with view.importer:
            import re
        
        @interactive
        def findall(pat, s):
            # this globals() step isn't necessary in real code
            # only to prevent a closure in the test
            return globals()['re'].findall(pat, s)
        
        self.assertEquals(view.apply_sync(findall, '\w+', 'hello world'), 'hello world'.split())
    
