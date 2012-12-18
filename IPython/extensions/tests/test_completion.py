# encoding: utf-8
"""Tests for completion.py annotation based hooks into the tab completer
system"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.extensions.completion import (tab_complete, globs_to,
    instance_of, literal)

from IPython.utils.tempdir import TemporaryDirectory
from IPython.testing.decorators import skipif

import nose.tools as nt
import sys, os

#-----------------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------------


def test_literal1():
    ip = get_ipython()
    @tab_complete(a=literal('aaaaaaaaaa'))
    def f(a):
        pass
    # py3k:
    # @tab_complete
    # def f(a : literal('aaaaaaaaaa')):
    #    pass
    ip.user_ns['f'] = f
    yield lambda : nt.assert_equal(ip.complete(None, "f(")[1],
        ["'aaaaaaaaaa'"])
        
    yield lambda : nt.assert_equal(ip.complete(None, "f('a")[1],
        ['aaaaaaaaaa'])


def test_default_instance():
    ip = get_ipython()
    @tab_complete(a=int)
    def f(a):
        pass
    # py3k:
    # @tab_complete
    # def f(a : int):
    #    pass
    ip.user_ns['f'] = f
    ip.user_ns['longint1'] = 1
    ip.user_ns['longint2'] = 1
    nt.assert_equal(ip.complete(None, "f(l")[1], ['longint1', 'longint2'])


def test_literal2():
    ip = get_ipython()
    # easy tab completion on two literal strings
    @tab_complete(arg1=literal('completion1', 'completion2'))
    def f(arg1 , arg2):
        pass
    # py3k:
    # @tab_complete
    # def f(arg1 : literal('completion1', 'completion2'), arg2):
    #    pass
    ip.user_ns['f'] = f
    yield lambda : nt.assert_equal(ip.complete(None, "f('complet")[1],
            ['completion1', 'completion2'])
    
    # this is slightly harder because under normal circumstances the
    # complex builtin would match, but in this case it should be excluded
    yield lambda : nt.assert_equal(ip.complete(None, "f('comple")[1],
        ['completion1', 'completion2'])


def test_glob1():
    ip = get_ipython()
    @tab_complete(x=globs_to('*.txt'))
    def f(x):
        pass
    # py3k:
    # @tab_complete
    # def f(x : globs_to('*.txt')):
    #    pass
    ip.user_ns['f'] = f
    
    with TemporaryDirectory() as tmpdir:
        names = [os.path.join(tmpdir, e) for e in ['a.txt', 'b.jpg', 'c.txt']]
        for n in names:
            open(n, 'w').close()
        
        # Check simple completion
        c = ip.complete(None, 'f(%s/' % tmpdir)[1]
        nt.assert_equal(c, ["%s/a.txt" % tmpdir, "%s/c.txt" % tmpdir])

def test_method():
    ip = get_ipython()
    class F(object):
        @tab_complete(arg1=literal('bar_baz_qux'))
        def foo(self, arg1):
            pass
    # py3k:
    # class F:
    #     @tab_complete
    #     def foo(self, arg1 : literal('bar_baz_qux')):
    #         pass
    ip.user_ns['f'] = F()
    
    nt.assert_equal(ip.complete(None, 'f.foo(')[1],
        ["'bar_baz_qux'"])


def test_constructor():
    ip = get_ipython()
    class F(object):
        @tab_complete(arg1=literal('bar_baz_qux'))
        def __init__(self, arg1):
            pass
    # py3k:
    # class F:
    #     @tab_complete
    #     def __init__(self, arg1 : literal('bar_baz_qux')):
    #         pass
    ip.user_ns['F'] = F
    nt.assert_equal(ip.complete(None, 'F(')[1], ["'bar_baz_qux'"])


def test_return():
    ip = get_ipython()
    @tab_complete(**{'return': str})
    def f(x):
        return x
    ip.user_ns['f'] = f
    nt.assert_equal(ip.complete(None, 'f().e')[1],
        [".encode", ".endswith", ".expandtabs"])
