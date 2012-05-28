# -*- coding: utf-8 -*-
"""Tests for the Cython magics extension."""

import os
import nose.tools as nt


code = """def f(x):
    return 2*x
"""

try:
    import Cython
except:
    __test__ = False

def setup():
    ip = get_ipython()
    ip.extension_manager.load_extension('cythonmagic')

def test_cython_inline():
    ip = get_ipython()
    ip.ex('a=10; b=20')
    result = ip.run_cell_magic('cython_inline','','return a+b')
    nt.assert_equals(result, 30)

def test_cython_pyximport():
    module_name = '_test_cython_pyximport'
    ip = get_ipython()
    ip.run_cell_magic('cython_pyximport', module_name, code)
    ip.ex('g = f(10)')
    nt.assert_equals(ip.user_ns['g'], 20.0)
    try:
        os.remove(module_name+'.pyx')
    except OSError:
        pass

def test_cython():
    ip = get_ipython()
    ip.run_cell_magic('cython', '', code)
    ip.ex('g = f(10)')
    nt.assert_equals(ip.user_ns['g'], 20.0)        



