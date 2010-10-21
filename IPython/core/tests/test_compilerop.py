"""Tests for the compilerop module.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010 The IPython Development Team.
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib imports
import linecache

# Third-party imports
import nose.tools as nt

# Our own imports
from IPython.core import compilerop

#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------

def test_code_name():
    code = 'x=1'
    name = compilerop.code_name(code)
    nt.assert_true(name.startswith('<ipython-input-0'))


def test_code_name2():
    code = 'x=1'
    name = compilerop.code_name(code, 9)
    nt.assert_true(name.startswith('<ipython-input-9'))


def test_compiler():
    """Test the compiler correctly compiles and caches inputs
    """
    cp = compilerop.CachingCompiler()
    ncache = len(linecache.cache)
    cp('x=1', 'single')
    nt.assert_true(len(linecache.cache) > ncache)


def test_compiler_check_cache():
    """Test the compiler properly manages the cache.
    """
    # Rather simple-minded tests that just exercise the API
    cp = compilerop.CachingCompiler()
    cp('x=1', 'single', 99)
    # Ensure now that after clearing the cache, our entries survive
    cp.check_cache()
    for k in linecache.cache:
        if k.startswith('<ipython-input-99'):
            break
    else:
        raise AssertionError('Entry for input-99 missing from linecache')
