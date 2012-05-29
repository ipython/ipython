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

import sys
import time

import zmq
from nose import SkipTest

from IPython.testing import decorators as dec
from IPython.testing.ipunittest import ParametricTestCase

from IPython import parallel  as pmod
from IPython.parallel import error
from IPython.parallel import AsyncResult
from IPython.parallel.util import interactive

from IPython.parallel.tests import add_engines

from .clienttest import ClusterTestCase, capture_output, generate_output

def setup():
    add_engines(3, total=True)

class TestParallelMagics(ClusterTestCase, ParametricTestCase):
    
    def test_px_blocking(self):
        ip = get_ipython()
        v = self.client[-1:]
        v.activate()
        v.block=True

        ip.magic('px a=5')
        self.assertEquals(v['a'], [5])
        ip.magic('px a=10')
        self.assertEquals(v['a'], [10])
        # just 'print a' works ~99% of the time, but this ensures that
        # the stdout message has arrived when the result is finished:
        with capture_output() as io:
            ip.magic(
                'px import sys,time;print(a);sys.stdout.flush();time.sleep(0.2)'
            )
        out = io.stdout
        self.assertTrue('[stdout:' in out, out)
        self.assertTrue(out.rstrip().endswith('10'))
        self.assertRaisesRemote(ZeroDivisionError, ip.magic, 'px 1/0')
    
    def test_cellpx_block_args(self):
        """%%px --[no]block flags work"""
        ip = get_ipython()
        v = self.client[-1:]
        v.activate()
        v.block=False
        
        for block in (True, False):
            v.block = block
            
            with capture_output() as io:
                ip.run_cell_magic("px", "", "1")
            if block:
                self.assertTrue(io.stdout.startswith("Parallel"), io.stdout)
            else:
                self.assertTrue(io.stdout.startswith("Async"), io.stdout)
            
            with capture_output() as io:
                ip.run_cell_magic("px", "--block", "1")
            self.assertTrue(io.stdout.startswith("Parallel"), io.stdout)

            with capture_output() as io:
                ip.run_cell_magic("px", "--noblock", "1")
            self.assertTrue(io.stdout.startswith("Async"), io.stdout)
    
    def test_cellpx_groupby_engine(self):
        """%%px --group-outputs=engine"""
        ip = get_ipython()
        v = self.client[:]
        v.block = True
        v.activate()
        
        v['generate_output'] = generate_output
        
        with capture_output() as io:
            ip.run_cell_magic('px', '--group-outputs=engine', 'generate_output()')
        
        lines = io.stdout.strip().splitlines()[1:]
        expected = [
            ('[stdout:', '] stdout'),
            'stdout2',
            'IPython.core.display.HTML',
            'IPython.core.display.Math',
            ('] Out[', 'IPython.core.display.Math')
            ] * len(v)
        
        self.assertEquals(len(lines), len(expected), io.stdout)
        for line,expect in zip(lines, expected):
            if isinstance(expect, str):
                expect = [expect]
            for ex in expect:
                self.assertTrue(ex in line, "Expected %r in %r" % (ex, line))
        
        expected = [
            ('[stderr:', '] stderr'),
            'stderr2',
        ] * len(v)
        
        lines = io.stderr.strip().splitlines()
        self.assertEquals(len(lines), len(expected), io.stderr)
        for line,expect in zip(lines, expected):
            if isinstance(expect, str):
                expect = [expect]
            for ex in expect:
                self.assertTrue(ex in line, "Expected %r in %r" % (ex, line))


    def test_cellpx_groupby_order(self):
        """%%px --group-outputs=order"""
        ip = get_ipython()
        v = self.client[:]
        v.block = True
        v.activate()
        
        v['generate_output'] = generate_output
        
        with capture_output() as io:
            ip.run_cell_magic('px', '--group-outputs=order', 'generate_output()')
        
        lines = io.stdout.strip().splitlines()[1:]
        expected = []
        expected.extend([
            ('[stdout:', '] stdout'),
            'stdout2',
        ] * len(v))
        expected.extend([
            'IPython.core.display.HTML',
        ] * len(v))
        expected.extend([
            'IPython.core.display.Math',
        ] * len(v))
        expected.extend([
            ('] Out[', 'IPython.core.display.Math')
        ] * len(v))
        
        self.assertEquals(len(lines), len(expected), io.stdout)
        for line,expect in zip(lines, expected):
            if isinstance(expect, str):
                expect = [expect]
            for ex in expect:
                self.assertTrue(ex in line, "Expected %r in %r" % (ex, line))
        
        expected = [
            ('[stderr:', '] stderr'),
            'stderr2',
        ] * len(v)
        
        lines = io.stderr.strip().splitlines()
        self.assertEquals(len(lines), len(expected), io.stderr)
        for line,expect in zip(lines, expected):
            if isinstance(expect, str):
                expect = [expect]
            for ex in expect:
                self.assertTrue(ex in line, "Expected %r in %r" % (ex, line))

    def test_cellpx_groupby_atype(self):
        """%%px --group-outputs=type"""
        ip = get_ipython()
        v = self.client[:]
        v.block = True
        v.activate()
        
        v['generate_output'] = generate_output
        
        with capture_output() as io:
            ip.run_cell_magic('px', '--group-outputs=type', 'generate_output()')
        
        lines = io.stdout.strip().splitlines()[1:]
        
        expected = []
        expected.extend([
            ('[stdout:', '] stdout'),
            'stdout2',
        ] * len(v))
        expected.extend([
            'IPython.core.display.HTML',
            'IPython.core.display.Math',
        ] * len(v))
        expected.extend([
            ('] Out[', 'IPython.core.display.Math')
        ] * len(v))
        
        self.assertEquals(len(lines), len(expected), io.stdout)
        for line,expect in zip(lines, expected):
            if isinstance(expect, str):
                expect = [expect]
            for ex in expect:
                self.assertTrue(ex in line, "Expected %r in %r" % (ex, line))
        
        expected = [
            ('[stderr:', '] stderr'),
            'stderr2',
        ] * len(v)
        
        lines = io.stderr.strip().splitlines()
        self.assertEquals(len(lines), len(expected), io.stderr)
        for line,expect in zip(lines, expected):
            if isinstance(expect, str):
                expect = [expect]
            for ex in expect:
                self.assertTrue(ex in line, "Expected %r in %r" % (ex, line))


    def test_px_nonblocking(self):
        ip = get_ipython()
        v = self.client[-1:]
        v.activate()
        v.block=False

        ip.magic('px a=5')
        self.assertEquals(v['a'], [5])
        ip.magic('px a=10')
        self.assertEquals(v['a'], [10])
        with capture_output() as io:
            ip.magic('px print a')
        self.assertFalse('[stdout:' in io.stdout)
        ar = ip.magic('px 1/0')
        self.assertRaisesRemote(ZeroDivisionError, ar.get)
    
    def test_autopx_blocking(self):
        ip = get_ipython()
        v = self.client[-1]
        v.activate()
        v.block=True

        with capture_output() as io:
            ip.magic('autopx')
            ip.run_cell('\n'.join(('a=5','b=12345','c=0')))
            ip.run_cell('b*=2')
            ip.run_cell('print (b)')
            ip.run_cell('b')
            ip.run_cell("b/c")
            ip.magic('autopx')
        
        output = io.stdout.strip()
        
        self.assertTrue(output.startswith('%autopx enabled'), output)
        self.assertTrue(output.endswith('%autopx disabled'), output)
        self.assertTrue('RemoteError: ZeroDivisionError' in output, output)
        self.assertTrue('] Out[' in output, output)
        self.assertTrue(': 24690' in output, output)
        ar = v.get_result(-1)
        self.assertEquals(v['a'], 5)
        self.assertEquals(v['b'], 24690)
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
        
        output = io.stdout.strip()
        
        self.assertTrue(output.startswith('%autopx enabled'))
        self.assertTrue(output.endswith('%autopx disabled'))
        self.assertFalse('ZeroDivisionError' in output)
        ar = v.get_result(-2)
        self.assertRaisesRemote(ZeroDivisionError, ar.get)
        # prevent TaskAborted on pulls, due to ZeroDivisionError
        time.sleep(0.5)
        self.assertEquals(v['a'], 5)
        # b*=2 will not fire, due to abort
        self.assertEquals(v['b'], 10)
    
    def test_result(self):
        ip = get_ipython()
        v = self.client[-1]
        v.activate()
        data = dict(a=111,b=222)
        v.push(data, block=True)

        ip.magic('px a')
        ip.magic('px b')
        for idx, name in [
                    ('', 'b'),
                    ('-1', 'b'),
                    ('2', 'b'),
                    ('1', 'a'),
                    ('-2', 'a'),
                ]:
            with capture_output() as io:
                ip.magic('result ' + idx)
            output = io.stdout.strip()
            msg = "expected %s output to include %s, but got: %s" % \
                ('%result '+idx, str(data[name]), output)
            self.assertTrue(str(data[name]) in output, msg)
        
    @dec.skipif_not_matplotlib
    def test_px_pylab(self):
        """%pylab works on engines"""
        ip = get_ipython()
        v = self.client[-1]
        v.block = True
        v.activate()
        
        with capture_output() as io:
            ip.magic("px %pylab inline")
        
        self.assertTrue("Welcome to pylab" in io.stdout, io.stdout)
        self.assertTrue("backend_inline" in io.stdout, io.stdout)
        
        with capture_output() as io:
            ip.magic("px plot(rand(100))")
        
        self.assertTrue('] Out[' in io.stdout, io.stdout)
        self.assertTrue('matplotlib.lines' in io.stdout, io.stdout)
        

