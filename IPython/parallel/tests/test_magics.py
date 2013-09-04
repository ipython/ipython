# -*- coding: utf-8 -*-
"""Test Parallel magics

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

import re
import time


from IPython.testing import decorators as dec
from IPython.utils.io import capture_output

from IPython import parallel  as pmod
from IPython.parallel import AsyncResult

from IPython.parallel.tests import add_engines

from .clienttest import ClusterTestCase, generate_output

def setup():
    add_engines(3, total=True)

class TestParallelMagics(ClusterTestCase):
    
    def test_px_blocking(self):
        ip = get_ipython()
        v = self.client[-1:]
        v.activate()
        v.block=True

        ip.magic('px a=5')
        self.assertEqual(v['a'], [5])
        ip.magic('px a=10')
        self.assertEqual(v['a'], [10])
        # just 'print a' works ~99% of the time, but this ensures that
        # the stdout message has arrived when the result is finished:
        with capture_output() as io:
            ip.magic(
                'px import sys,time;print(a);sys.stdout.flush();time.sleep(0.2)'
            )
        self.assertIn('[stdout:', io.stdout)
        self.assertNotIn('\n\n', io.stdout)
        assert io.stdout.rstrip().endswith('10')
        self.assertRaisesRemote(ZeroDivisionError, ip.magic, 'px 1/0')
    
    def _check_generated_stderr(self, stderr, n):
        expected = [
            r'\[stderr:\d+\]',
            '^stderr$',
            '^stderr2$',
        ] * n
        
        self.assertNotIn('\n\n', stderr)
        lines = stderr.splitlines()
        self.assertEqual(len(lines), len(expected), stderr)
        for line,expect in zip(lines, expected):
            if isinstance(expect, str):
                expect = [expect]
            for ex in expect:
                assert re.search(ex, line) is not None, "Expected %r in %r" % (ex, line)
        
    def test_cellpx_block_args(self):
        """%%px --[no]block flags work"""
        ip = get_ipython()
        v = self.client[-1:]
        v.activate()
        v.block=False
        
        for block in (True, False):
            v.block = block
            ip.magic("pxconfig --verbose")
            with capture_output(display=False) as io:
                ip.run_cell_magic("px", "", "1")
            if block:
                assert io.stdout.startswith("Parallel"), io.stdout
            else:
                assert io.stdout.startswith("Async"), io.stdout
            
            with capture_output(display=False) as io:
                ip.run_cell_magic("px", "--block", "1")
            assert io.stdout.startswith("Parallel"), io.stdout

            with capture_output(display=False) as io:
                ip.run_cell_magic("px", "--noblock", "1")
            assert io.stdout.startswith("Async"), io.stdout
    
    def test_cellpx_groupby_engine(self):
        """%%px --group-outputs=engine"""
        ip = get_ipython()
        v = self.client[:]
        v.block = True
        v.activate()
        
        v['generate_output'] = generate_output
        
        with capture_output(display=False) as io:
            ip.run_cell_magic('px', '--group-outputs=engine', 'generate_output()')
        
        self.assertNotIn('\n\n', io.stdout)
        lines = io.stdout.splitlines()
        expected = [
            r'\[stdout:\d+\]',
            'stdout',
            'stdout2',
            r'\[output:\d+\]',
            r'IPython\.core\.display\.HTML',
            r'IPython\.core\.display\.Math',
            r'Out\[\d+:\d+\]:.*IPython\.core\.display\.Math',
            ] * len(v)
        
        self.assertEqual(len(lines), len(expected), io.stdout)
        for line,expect in zip(lines, expected):
            if isinstance(expect, str):
                expect = [expect]
            for ex in expect:
                assert re.search(ex, line) is not None, "Expected %r in %r" % (ex, line)
        
        self._check_generated_stderr(io.stderr, len(v))


    def test_cellpx_groupby_order(self):
        """%%px --group-outputs=order"""
        ip = get_ipython()
        v = self.client[:]
        v.block = True
        v.activate()
        
        v['generate_output'] = generate_output
        
        with capture_output(display=False) as io:
            ip.run_cell_magic('px', '--group-outputs=order', 'generate_output()')
        
        self.assertNotIn('\n\n', io.stdout)
        lines = io.stdout.splitlines()
        expected = []
        expected.extend([
            r'\[stdout:\d+\]',
            'stdout',
            'stdout2',
        ] * len(v))
        expected.extend([
            r'\[output:\d+\]',
            'IPython.core.display.HTML',
        ] * len(v))
        expected.extend([
            r'\[output:\d+\]',
            'IPython.core.display.Math',
        ] * len(v))
        expected.extend([
            r'Out\[\d+:\d+\]:.*IPython\.core\.display\.Math'
        ] * len(v))
        
        self.assertEqual(len(lines), len(expected), io.stdout)
        for line,expect in zip(lines, expected):
            if isinstance(expect, str):
                expect = [expect]
            for ex in expect:
                assert re.search(ex, line) is not None, "Expected %r in %r" % (ex, line)
        
        self._check_generated_stderr(io.stderr, len(v))

    def test_cellpx_groupby_type(self):
        """%%px --group-outputs=type"""
        ip = get_ipython()
        v = self.client[:]
        v.block = True
        v.activate()
        
        v['generate_output'] = generate_output
        
        with capture_output(display=False) as io:
            ip.run_cell_magic('px', '--group-outputs=type', 'generate_output()')
        
        self.assertNotIn('\n\n', io.stdout)
        lines = io.stdout.splitlines()
        
        expected = []
        expected.extend([
            r'\[stdout:\d+\]',
            'stdout',
            'stdout2',
        ] * len(v))
        expected.extend([
            r'\[output:\d+\]',
            r'IPython\.core\.display\.HTML',
            r'IPython\.core\.display\.Math',
        ] * len(v))
        expected.extend([
            (r'Out\[\d+:\d+\]', r'IPython\.core\.display\.Math')
        ] * len(v))
        
        self.assertEqual(len(lines), len(expected), io.stdout)
        for line,expect in zip(lines, expected):
            if isinstance(expect, str):
                expect = [expect]
            for ex in expect:
                assert re.search(ex, line) is not None, "Expected %r in %r" % (ex, line)
        
        self._check_generated_stderr(io.stderr, len(v))


    def test_px_nonblocking(self):
        ip = get_ipython()
        v = self.client[-1:]
        v.activate()
        v.block=False

        ip.magic('px a=5')
        self.assertEqual(v['a'], [5])
        ip.magic('px a=10')
        self.assertEqual(v['a'], [10])
        ip.magic('pxconfig --verbose')
        with capture_output() as io:
            ar = ip.magic('px print (a)')
        self.assertIsInstance(ar, AsyncResult)
        self.assertIn('Async', io.stdout)
        self.assertNotIn('[stdout:', io.stdout)
        self.assertNotIn('\n\n', io.stdout)
        
        ar = ip.magic('px 1/0')
        self.assertRaisesRemote(ZeroDivisionError, ar.get)
    
    def test_autopx_blocking(self):
        ip = get_ipython()
        v = self.client[-1]
        v.activate()
        v.block=True

        with capture_output(display=False) as io:
            ip.magic('autopx')
            ip.run_cell('\n'.join(('a=5','b=12345','c=0')))
            ip.run_cell('b*=2')
            ip.run_cell('print (b)')
            ip.run_cell('b')
            ip.run_cell("b/c")
            ip.magic('autopx')
        
        output = io.stdout
        
        assert output.startswith('%autopx enabled'), output
        assert output.rstrip().endswith('%autopx disabled'), output
        self.assertIn('ZeroDivisionError', output)
        self.assertIn('\nOut[', output)
        self.assertIn(': 24690', output)
        ar = v.get_result(-1)
        self.assertEqual(v['a'], 5)
        self.assertEqual(v['b'], 24690)
        self.assertRaisesRemote(ZeroDivisionError, ar.get)

    def test_autopx_nonblocking(self):
        ip = get_ipython()
        v = self.client[-1]
        v.activate()
        v.block=False

        with capture_output() as io:
            ip.magic('autopx')
            ip.run_cell('\n'.join(('a=5','b=10','c=0')))
            ip.run_cell('print (b)')
            ip.run_cell('import time; time.sleep(0.1)')
            ip.run_cell("b/c")
            ip.run_cell('b*=2')
            ip.magic('autopx')
        
        output = io.stdout.rstrip()
        
        assert output.startswith('%autopx enabled'), output
        assert output.endswith('%autopx disabled'), output
        self.assertNotIn('ZeroDivisionError', output)
        ar = v.get_result(-2)
        self.assertRaisesRemote(ZeroDivisionError, ar.get)
        # prevent TaskAborted on pulls, due to ZeroDivisionError
        time.sleep(0.5)
        self.assertEqual(v['a'], 5)
        # b*=2 will not fire, due to abort
        self.assertEqual(v['b'], 10)
    
    def test_result(self):
        ip = get_ipython()
        v = self.client[-1]
        v.activate()
        data = dict(a=111,b=222)
        v.push(data, block=True)

        for name in ('a', 'b'):
            ip.magic('px ' + name)
            with capture_output(display=False) as io:
                ip.magic('pxresult')
            self.assertIn(str(data[name]), io.stdout)
        
    @dec.skipif_not_matplotlib
    def test_px_pylab(self):
        """%pylab works on engines"""
        ip = get_ipython()
        v = self.client[-1]
        v.block = True
        v.activate()
        
        with capture_output() as io:
            ip.magic("px %pylab inline")
        
        self.assertIn("Populating the interactive namespace from numpy and matplotlib", io.stdout)
        
        with capture_output(display=False) as io:
            ip.magic("px plot(rand(100))")
        self.assertIn('Out[', io.stdout)
        self.assertIn('matplotlib.lines', io.stdout)
    
    def test_pxconfig(self):
        ip = get_ipython()
        rc = self.client
        v = rc.activate(-1, '_tst')
        self.assertEqual(v.targets, rc.ids[-1])
        ip.magic("%pxconfig_tst -t :")
        self.assertEqual(v.targets, rc.ids)
        ip.magic("%pxconfig_tst -t ::2")
        self.assertEqual(v.targets, rc.ids[::2])
        ip.magic("%pxconfig_tst -t 1::2")
        self.assertEqual(v.targets, rc.ids[1::2])
        ip.magic("%pxconfig_tst -t 1")
        self.assertEqual(v.targets, 1)
        ip.magic("%pxconfig_tst --block")
        self.assertEqual(v.block, True)
        ip.magic("%pxconfig_tst --noblock")
        self.assertEqual(v.block, False)
    
    def test_cellpx_targets(self):
        """%%px --targets doesn't change defaults"""
        ip = get_ipython()
        rc = self.client
        view = rc.activate(rc.ids)
        self.assertEqual(view.targets, rc.ids)
        ip.magic('pxconfig --verbose')
        for cell in ("pass", "1/0"):
            with capture_output(display=False) as io:
                try:
                    ip.run_cell_magic("px", "--targets all", cell)
                except pmod.RemoteError:
                    pass
            self.assertIn('engine(s): all', io.stdout)
            self.assertEqual(view.targets, rc.ids)


    def test_cellpx_block(self):
        """%%px --block doesn't change default"""
        ip = get_ipython()
        rc = self.client
        view = rc.activate(rc.ids)
        view.block = False
        self.assertEqual(view.targets, rc.ids)
        ip.magic('pxconfig --verbose')
        for cell in ("pass", "1/0"):
            with capture_output(display=False) as io:
                try:
                    ip.run_cell_magic("px", "--block", cell)
                except pmod.RemoteError:
                    pass
            self.assertNotIn('Async', io.stdout)
            self.assertEqual(view.block, False)


