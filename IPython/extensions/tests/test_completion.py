"""
tab completion api

@tab_completion
def f(x : int, y : dict) -> int:
    pass
"""
from IPython.extensions.completion import (tab_complete, globs_to,
    instance_of, literal)

from IPython.utils.tempdir import TemporaryDirectory
from IPython.testing.decorators import skipif
import nose.tools as nt
import sys, os


# @skipif(sys.version_info.major == 2)
# def test_decorator():
#     # test that two ways of annotating give the same result
#     for ann in [tab_glob('.txt'), tab_instance(int, set), tab_literal(1,2)]:
#         @tab_completion
#         def f1(arg1 : ann, arg2):
#             pass
#         @tab_completion(arg1=ann)
#         def f2(arg1, arg2):
#             pass
#     
#         yield lambda : nt.assert_equal(f1.__tab_completions__, f2.__tab_completions__)
# 
# 
# 
#     # test that the (unfortunate) python 2 style sytax for annotating the return
#     # value puts the data in the same place as the py3k syntax
#     for ann in [tab_glob('.txt'), tab_instance(int, set), tab_literal(1,2)]:
#         @tab_completion
#         def f1(arg1, arg2) -> ann:
#             pass
#         
#         @tab_completion_return(ann)
#         def f2(arg1, arg2):
#             pass
#             
#         yield lambda : nt.assert_equal(f1.__tab_completions__, f2.__tab_completions__)


def test_literal1():
    ip = get_ipython()
    @tab_complete(a=literal('aaaaaaaaaa'))
    def f(a):
        pass
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
    ip.user_ns['f'] = F()
    
    nt.assert_equal(ip.complete(None, 'f.foo(')[1],
        ["'bar_baz_qux'"])


def test_constructor():
    ip = get_ipython()
    class F(object):
        @tab_complete(arg1=literal('bar_baz_qux'))
        def __init__(self, arg1):
            pass
    ip.user_ns['F'] = F
    nt.assert_equal(ip.complete(None, 'F(')[1], ["'bar_baz_qux'"])