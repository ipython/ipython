# -*- coding: utf-8 -*-
"""test View objects

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

import sys
import time
from tempfile import mktemp
from StringIO import StringIO

import zmq
from nose import SkipTest

from IPython.testing import decorators as dec

from IPython import parallel  as pmod
from IPython.parallel import error
from IPython.parallel import AsyncResult, AsyncHubResult, AsyncMapResult
from IPython.parallel import DirectView
from IPython.parallel.util import interactive

from IPython.parallel.tests import add_engines

from .clienttest import ClusterTestCase, crash, wait, skip_without

def setup():
    add_engines(3)

class TestView(ClusterTestCase):
    
    def test_z_crash_mux(self):
        """test graceful handling of engine death (direct)"""
        raise SkipTest("crash tests disabled, due to undesirable crash reports")
        # self.add_engines(1)
        eid = self.client.ids[-1]
        ar = self.client[eid].apply_async(crash)
        self.assertRaisesRemote(error.EngineError, ar.get, 10)
        eid = ar.engine_id
        tic = time.time()
        while eid in self.client.ids and time.time()-tic < 5:
            time.sleep(.01)
            self.client.spin()
        self.assertFalse(eid in self.client.ids, "Engine should have died")
    
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
        r = self.client[:].pull(('a','b'), block=True)
        self.assertEquals(r, nengines*[[10,20]])
    
    def test_push_pull_function(self):
        "test pushing and pulling functions"
        def testf(x):
            return 2.0*x
        
        t = self.client.ids[-1]
        v = self.client[t]
        v.block=True
        push = v.push
        pull = v.pull
        execute = v.execute
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
        ar._tracker.wait()
        self.assertEquals(ar.sent, ar._tracker.done)
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
    
    @skip_without('numpy')
    def test_apply_numpy(self):
        """view.apply(f, ndarray)"""
        import numpy
        from numpy.testing.utils import assert_array_equal, assert_array_almost_equal
        
        A = numpy.random.random((100,100))
        view = self.client[-1]
        for dt in [ 'int32', 'uint8', 'float32', 'float64' ]:
            B = A.astype(dt)
            C = view.apply_sync(lambda x:x, B)
            assert_array_equal(B,C)
    
    def test_map(self):
        view = self.client[:]
        def f(x):
            return x**2
        data = range(16)
        r = view.map_sync(f, data)
        self.assertEquals(r, map(f, data))
    
    def test_map_iterable(self):
        """test map on iterables (direct)"""
        view = self.client[:]
        # 101 is prime, so it won't be evenly distributed
        arr = range(101)
        # ensure it will be an iterator, even in Python 3
        it = iter(arr)
        r = view.map_sync(lambda x:x, arr)
        self.assertEquals(r, list(arr))
    
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
        ar = view.execute('import time; time.sleep(1)', block=False)
        ar2 = view.apply_async(lambda : 2)
        ar3 = view.apply_async(lambda : 3)
        view.abort(ar2)
        view.abort(ar3.msg_ids)
        self.assertRaises(error.TaskAborted, ar2.get)
        self.assertRaises(error.TaskAborted, ar3.get)
    
    def test_abort_all(self):
        """view.abort() aborts all outstanding tasks"""
        view = self.client[-1]
        ars = [ view.apply_async(time.sleep, 1) for i in range(10) ]
        view.abort()
        view.wait(timeout=5)
        for ar in ars[5:]:
            self.assertRaises(error.TaskAborted, ar.get)
    
    def test_temp_flags(self):
        view = self.client[-1]
        view.block=True
        with view.temp_flags(block=False):
            self.assertFalse(view.block)
        self.assertTrue(view.block)
    
    @dec.known_failure_py3
    def test_importer(self):
        view = self.client[-1]
        view.clear(block=True)
        with view.importer:
            import re
        
        @interactive
        def findall(pat, s):
            # this globals() step isn't necessary in real code
            # only to prevent a closure in the test
            re = globals()['re']
            return re.findall(pat, s)
        
        self.assertEquals(view.apply_sync(findall, '\w+', 'hello world'), 'hello world'.split())
    
    # parallel magic tests
    
    def test_magic_px_blocking(self):
        ip = get_ipython()
        v = self.client[-1]
        v.activate()
        v.block=True

        ip.magic_px('a=5')
        self.assertEquals(v['a'], 5)
        ip.magic_px('a=10')
        self.assertEquals(v['a'], 10)
        sio = StringIO()
        savestdout = sys.stdout
        sys.stdout = sio
        # just 'print a' worst ~99% of the time, but this ensures that
        # the stdout message has arrived when the result is finished:
        ip.magic_px('import sys,time;print (a); sys.stdout.flush();time.sleep(0.2)')
        sys.stdout = savestdout
        buf = sio.getvalue()
        self.assertTrue('[stdout:' in buf, buf)
        self.assertTrue(buf.rstrip().endswith('10'))
        self.assertRaisesRemote(ZeroDivisionError, ip.magic_px, '1/0')

    def test_magic_px_nonblocking(self):
        ip = get_ipython()
        v = self.client[-1]
        v.activate()
        v.block=False

        ip.magic_px('a=5')
        self.assertEquals(v['a'], 5)
        ip.magic_px('a=10')
        self.assertEquals(v['a'], 10)
        sio = StringIO()
        savestdout = sys.stdout
        sys.stdout = sio
        ip.magic_px('print a')
        sys.stdout = savestdout
        buf = sio.getvalue()
        self.assertFalse('[stdout:%i]'%v.targets in buf)
        ip.magic_px('1/0')
        ar = v.get_result(-1)
        self.assertRaisesRemote(ZeroDivisionError, ar.get)
    
    def test_magic_autopx_blocking(self):
        ip = get_ipython()
        v = self.client[-1]
        v.activate()
        v.block=True

        sio = StringIO()
        savestdout = sys.stdout
        sys.stdout = sio
        ip.magic_autopx()
        ip.run_cell('\n'.join(('a=5','b=10','c=0')))
        ip.run_cell('print b')
        ip.run_cell("b/c")
        ip.run_code(compile('b*=2', '', 'single'))
        ip.magic_autopx()
        sys.stdout = savestdout
        output = sio.getvalue().strip()
        self.assertTrue(output.startswith('%autopx enabled'))
        self.assertTrue(output.endswith('%autopx disabled'))
        self.assertTrue('RemoteError: ZeroDivisionError' in output)
        ar = v.get_result(-2)
        self.assertEquals(v['a'], 5)
        self.assertEquals(v['b'], 20)
        self.assertRaisesRemote(ZeroDivisionError, ar.get)

    def test_magic_autopx_nonblocking(self):
        ip = get_ipython()
        v = self.client[-1]
        v.activate()
        v.block=False

        sio = StringIO()
        savestdout = sys.stdout
        sys.stdout = sio
        ip.magic_autopx()
        ip.run_cell('\n'.join(('a=5','b=10','c=0')))
        ip.run_cell('print b')
        ip.run_cell("b/c")
        ip.run_code(compile('b*=2', '', 'single'))
        ip.magic_autopx()
        sys.stdout = savestdout
        output = sio.getvalue().strip()
        self.assertTrue(output.startswith('%autopx enabled'))
        self.assertTrue(output.endswith('%autopx disabled'))
        self.assertFalse('ZeroDivisionError' in output)
        ar = v.get_result(-2)
        self.assertEquals(v['a'], 5)
        self.assertEquals(v['b'], 20)
        self.assertRaisesRemote(ZeroDivisionError, ar.get)
    
    def test_magic_result(self):
        ip = get_ipython()
        v = self.client[-1]
        v.activate()
        v['a'] = 111
        ra = v['a']
        
        ar = ip.magic_result()
        self.assertEquals(ar.msg_ids, [v.history[-1]])
        self.assertEquals(ar.get(), 111)
        ar = ip.magic_result('-2')
        self.assertEquals(ar.msg_ids, [v.history[-2]])
    
    def test_unicode_execute(self):
        """test executing unicode strings"""
        v = self.client[-1]
        v.block=True
        if sys.version_info[0] >= 3:
            code="a='é'"
        else:
            code=u"a=u'é'"
        v.execute(code)
        self.assertEquals(v['a'], u'é')
        
    def test_unicode_apply_result(self):
        """test unicode apply results"""
        v = self.client[-1]
        r = v.apply_sync(lambda : u'é')
        self.assertEquals(r, u'é')
    
    def test_unicode_apply_arg(self):
        """test passing unicode arguments to apply"""
        v = self.client[-1]
        
        @interactive
        def check_unicode(a, check):
            assert isinstance(a, unicode), "%r is not unicode"%a
            assert isinstance(check, bytes), "%r is not bytes"%check
            assert a.encode('utf8') == check, "%s != %s"%(a,check)
        
        for s in [ u'é', u'ßø®∫',u'asdf' ]:
            try:
                v.apply_sync(check_unicode, s, s.encode('utf8'))
            except error.RemoteError as e:
                if e.ename == 'AssertionError':
                    self.fail(e.evalue)
                else:
                    raise e
    
    def test_map_reference(self):
        """view.map(<Reference>, *seqs) should work"""
        v = self.client[:]
        v.scatter('n', self.client.ids, flatten=True)
        v.execute("f = lambda x,y: x*y")
        rf = pmod.Reference('f')
        nlist = list(range(10))
        mlist = nlist[::-1]
        expected = [ m*n for m,n in zip(mlist, nlist) ]
        result = v.map_sync(rf, mlist, nlist)
        self.assertEquals(result, expected)

    def test_apply_reference(self):
        """view.apply(<Reference>, *args) should work"""
        v = self.client[:]
        v.scatter('n', self.client.ids, flatten=True)
        v.execute("f = lambda x: n*x")
        rf = pmod.Reference('f')
        result = v.apply_sync(rf, 5)
        expected = [ 5*id for id in self.client.ids ]
        self.assertEquals(result, expected)

