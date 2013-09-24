# -*- coding: utf-8 -*-
"""Tests for the Cython magics extension."""

import os
import nose.tools as nt

from IPython.testing import decorators as dec
from IPython.utils import py3compat

code = py3compat.str_to_unicode("""def f(x):
    return 2*x
""")

try:
    import Cython
except:
    __test__ = False

ip = get_ipython()


def setup():
    ip.extension_manager.load_extension('cythonmagic')


def test_cython_inline():
    ip.ex('a=10; b=20')
    result = ip.run_cell_magic('cython_inline','','return a+b')
    nt.assert_equal(result, 30)


@dec.skip_win32
def test_cython_pyximport():
    module_name = '_test_cython_pyximport'
    ip.run_cell_magic('cython_pyximport', module_name, code)
    ip.ex('g = f(10)')
    nt.assert_equal(ip.user_ns['g'], 20.0)
    ip.run_cell_magic('cython_pyximport', module_name, code)
    ip.ex('h = f(-10)')
    nt.assert_equal(ip.user_ns['h'], -20.0)
    try:
        os.remove(module_name+'.pyx')
    except OSError:
        pass


def test_cython():
    ip.run_cell_magic('cython', '', code)
    ip.ex('g = f(10)')
    nt.assert_equal(ip.user_ns['g'], 20.0)


def test_cython_name():
    # The Cython module named 'mymodule' defines the function f.
    ip.run_cell_magic('cython', '--name=mymodule', code)
    # This module can now be imported in the interactive namespace.
    ip.ex('import mymodule; g = mymodule.f(10)')
    nt.assert_equal(ip.user_ns['g'], 20.0)


@dec.skip_win32
def test_extlibs():
    code = py3compat.str_to_unicode("""
from libc.math cimport sin
x = sin(0.0)
    """)
    ip.user_ns['x'] = 1
    ip.run_cell_magic('cython', '-l m', code)
    nt.assert_equal(ip.user_ns['x'], 0)
    
