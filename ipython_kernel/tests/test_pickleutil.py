
import pickle

import nose.tools as nt
from IPython.utils import codeutil
from IPython.utils.pickleutil import can, uncan

def interactive(f):
    f.__module__ = '__main__'
    return f

def dumps(obj):
    return pickle.dumps(can(obj))

def loads(obj):
    return uncan(pickle.loads(obj))

def test_no_closure():
    @interactive
    def foo():
        a = 5
        return a
    
    pfoo = dumps(foo)
    bar = loads(pfoo)
    nt.assert_equal(foo(), bar())

def test_generator_closure():
    # this only creates a closure on Python 3
    @interactive
    def foo():
        i = 'i'
        r = [ i for j in (1,2) ]
        return r
    
    pfoo = dumps(foo)
    bar = loads(pfoo)
    nt.assert_equal(foo(), bar())

def test_nested_closure():
    @interactive
    def foo():
        i = 'i'
        def g():
            return i
        return g()
    
    pfoo = dumps(foo)
    bar = loads(pfoo)
    nt.assert_equal(foo(), bar())

def test_closure():
    i = 'i'
    @interactive
    def foo():
        return i
    
    pfoo = dumps(foo)
    bar = loads(pfoo)
    nt.assert_equal(foo(), bar())

    