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
import platform
import time
from tempfile import mktemp
from StringIO import StringIO

import zmq
from nose import SkipTest

from IPython.testing import decorators as dec
from IPython.testing.ipunittest import ParametricTestCase

from IPython import parallel  as pmod
from IPython.parallel import error
from IPython.parallel import AsyncResult, AsyncHubResult, AsyncMapResult
from IPython.parallel import DirectView
from IPython.parallel.util import interactive

from IPython.parallel.tests import add_engines

from .clienttest import ClusterTestCase, crash, wait, skip_without

def setup():
    add_engines(3, total=True)

class TestView(ClusterTestCase, ParametricTestCase):
    
    def setUp(self):
        # On Win XP, wait for resource cleanup, else parallel test group fails
        if platform.system() == "Windows" and platform.win32_ver()[0] == "XP":
            # 1 sec fails. 1.5 sec seems ok. Using 2 sec for margin of safety
            time.sleep(2)
        super(TestView, self).setUp()

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
    
    def test_scatter_gather_lazy(self):
        """scatter/gather with targets='all'"""
        view = self.client.direct_view(targets='all')
        x = range(64)
        view.scatter('x', x)
        gathered = view.gather('x', block=True)
        self.assertEquals(gathered, x)
        

    @dec.known_failure_py3
    @skip_without('numpy')
    def test_push_numpy_nocopy(self):
        import numpy
        view = self.client[:]
        a = numpy.arange(64)
        view['A'] = a
        @interactive
        def check_writeable(x):
            return x.flags.writeable
        
        for flag in view.apply_sync(check_writeable, pmod.Reference('A')):
            self.assertFalse(flag, "array is writeable, push shouldn't have pickled it")
        
        view.push(dict(B=a))
        for flag in view.apply_sync(check_writeable, pmod.Reference('B')):
            self.assertFalse(flag, "array is writeable, push shouldn't have pickled it")
    
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
    
    @skip_without('numpy')
    def test_push_pull_recarray(self):
        """push/pull recarrays"""
        import numpy
        from numpy.testing.utils import assert_array_equal
        
        view = self.client[-1]
        
        R = numpy.array([
            (1, 'hi', 0.),
            (2**30, 'there', 2.5),
            (-99999, 'world', -12345.6789),
        ], [('n', int), ('s', '|S10'), ('f', float)])
        
        view['RR'] = R
        R2 = view['RR']
        
        r_dtype, r_shape = view.apply_sync(interactive(lambda : (RR.dtype, RR.shape)))
        self.assertEquals(r_dtype, R.dtype)
        self.assertEquals(r_shape, R.shape)
        self.assertEquals(R2.dtype, R.dtype)
        self.assertEquals(R2.shape, R.shape)
        assert_array_equal(R2, R)
    
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
        ars = [ view.apply_async(time.sleep, 0.25) for i in range(10) ]
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
    
    def test_eval_reference(self):
        v = self.client[self.client.ids[0]]
        v['g'] = range(5)
        rg = pmod.Reference('g[0]')
        echo = lambda x:x
        self.assertEquals(v.apply_sync(echo, rg), 0)
    
    def test_reference_nameerror(self):
        v = self.client[self.client.ids[0]]
        r = pmod.Reference('elvis_has_left')
        echo = lambda x:x
        self.assertRaisesRemote(NameError, v.apply_sync, echo, r)

    def test_single_engine_map(self):
        e0 = self.client[self.client.ids[0]]
        r = range(5)
        check = [ -1*i for i in r ]
        result = e0.map_sync(lambda x: -1*x, r)
        self.assertEquals(result, check)
    
    def test_len(self):
        """len(view) makes sense"""
        e0 = self.client[self.client.ids[0]]
        yield self.assertEquals(len(e0), 1)
        v = self.client[:]
        yield self.assertEquals(len(v), len(self.client.ids))
        v = self.client.direct_view('all')
        yield self.assertEquals(len(v), len(self.client.ids))
        v = self.client[:2]
        yield self.assertEquals(len(v), 2)
        v = self.client[:1]
        yield self.assertEquals(len(v), 1)
        v = self.client.load_balanced_view()
        yield self.assertEquals(len(v), len(self.client.ids))
        # parametric tests seem to require manual closing?
        self.client.close()

    
    # begin execute tests
    
    def test_execute_reply(self):
        e0 = self.client[self.client.ids[0]]
        e0.block = True
        ar = e0.execute("5", silent=False)
        er = ar.get()
        self.assertEquals(str(er), "<ExecuteReply[%i]: 5>" % er.execution_count)
        self.assertEquals(er.pyout['data']['text/plain'], '5')

    def test_execute_reply_stdout(self):
        e0 = self.client[self.client.ids[0]]
        e0.block = True
        ar = e0.execute("print (5)", silent=False)
        er = ar.get()
        self.assertEquals(er.stdout.strip(), '5')
        
    def test_execute_pyout(self):
        """execute triggers pyout with silent=False"""
        view = self.client[:]
        ar = view.execute("5", silent=False, block=True)
        
        expected = [{'text/plain' : '5'}] * len(view)
        mimes = [ out['data'] for out in ar.pyout ]
        self.assertEquals(mimes, expected)
    
    def test_execute_silent(self):
        """execute does not trigger pyout with silent=True"""
        view = self.client[:]
        ar = view.execute("5", block=True)
        expected = [None] * len(view)
        self.assertEquals(ar.pyout, expected)
    
    def test_execute_magic(self):
        """execute accepts IPython commands"""
        view = self.client[:]
        view.execute("a = 5")
        ar = view.execute("%whos", block=True)
        # this will raise, if that failed
        ar.get(5)
        for stdout in ar.stdout:
            lines = stdout.splitlines()
            self.assertEquals(lines[0].split(), ['Variable', 'Type', 'Data/Info'])
            found = False
            for line in lines[2:]:
                split = line.split()
                if split == ['a', 'int', '5']:
                    found = True
                    break
            self.assertTrue(found, "whos output wrong: %s" % stdout)
    
    def test_execute_displaypub(self):
        """execute tracks display_pub output"""
        view = self.client[:]
        view.execute("from IPython.core.display import *")
        ar = view.execute("[ display(i) for i in range(5) ]", block=True)
        
        expected = [ {u'text/plain' : unicode(j)} for j in range(5) ]
        for outputs in ar.outputs:
            mimes = [ out['data'] for out in outputs ]
            self.assertEquals(mimes, expected)
    
    def test_apply_displaypub(self):
        """apply tracks display_pub output"""
        view = self.client[:]
        view.execute("from IPython.core.display import *")
        
        @interactive
        def publish():
            [ display(i) for i in range(5) ]
        
        ar = view.apply_async(publish)
        ar.get(5)
        expected = [ {u'text/plain' : unicode(j)} for j in range(5) ]
        for outputs in ar.outputs:
            mimes = [ out['data'] for out in outputs ]
            self.assertEquals(mimes, expected)
    
    def test_execute_raises(self):
        """exceptions in execute requests raise appropriately"""
        view = self.client[-1]
        ar = view.execute("1/0")
        self.assertRaisesRemote(ZeroDivisionError, ar.get, 2)
    
    @dec.skipif_not_matplotlib
    def test_magic_pylab(self):
        """%pylab works on engines"""
        view = self.client[-1]
        ar = view.execute("%pylab inline")
        # at least check if this raised:
        reply = ar.get(5)
        # include imports, in case user config
        ar = view.execute("plot(rand(100))", silent=False)
        reply = ar.get(5)
        self.assertEquals(len(reply.outputs), 1)
        output = reply.outputs[0]
        self.assertTrue("data" in output)
        data = output['data']
        self.assertTrue("image/png" in data)
        

