"""test serialization tools"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import pickle
from collections import namedtuple

import nose.tools as nt

# from unittest import TestCaes
from IPython.kernel.zmq.serialize import serialize_object, deserialize_object
from IPython.testing import decorators as dec
from IPython.utils.pickleutil import CannedArray, CannedClass
from IPython.utils.py3compat import iteritems
from IPython.parallel import interactive

#-------------------------------------------------------------------------------
# Globals and Utilities
#-------------------------------------------------------------------------------

def roundtrip(obj):
    """roundtrip an object through serialization"""
    bufs = serialize_object(obj)
    obj2, remainder = deserialize_object(bufs)
    nt.assert_equals(remainder, [])
    return obj2

class C(object):
    """dummy class for """
    
    def __init__(self, **kwargs):
        for key,value in iteritems(kwargs):
            setattr(self, key, value)

SHAPES = ((100,), (1024,10), (10,8,6,5), (), (0,))
DTYPES = ('uint8', 'float64', 'int32', [('g', 'float32')], '|S10')

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

def new_array(shape, dtype):
    import numpy
    return numpy.random.random(shape).astype(dtype)

def test_roundtrip_simple():
    for obj in [
        'hello',
        dict(a='b', b=10),
        [1,2,'hi'],
        (b'123', 'hello'),
    ]:
        obj2 = roundtrip(obj)
        nt.assert_equal(obj, obj2)

def test_roundtrip_nested():
    for obj in [
        dict(a=range(5), b={1:b'hello'}),
        [range(5),[range(3),(1,[b'whoda'])]],
    ]:
        obj2 = roundtrip(obj)
        nt.assert_equal(obj, obj2)

def test_roundtrip_buffered():
    for obj in [
        dict(a=b"x"*1025),
        b"hello"*500,
        [b"hello"*501, 1,2,3]
    ]:
        bufs = serialize_object(obj)
        nt.assert_equal(len(bufs), 2)
        obj2, remainder = deserialize_object(bufs)
        nt.assert_equal(remainder, [])
        nt.assert_equal(obj, obj2)

@dec.skip_without('numpy')
def test_numpy():
    import numpy
    from numpy.testing.utils import assert_array_equal
    for shape in SHAPES:
        for dtype in DTYPES:
            A = new_array(shape, dtype=dtype)
            bufs = serialize_object(A)
            B, r = deserialize_object(bufs)
            nt.assert_equal(r, [])
            nt.assert_equal(A.shape, B.shape)
            nt.assert_equal(A.dtype, B.dtype)
            assert_array_equal(A,B)

@dec.skip_without('numpy')
def test_recarray():
    import numpy
    from numpy.testing.utils import assert_array_equal
    for shape in SHAPES:
        for dtype in [
            [('f', float), ('s', '|S10')],
            [('n', int), ('s', '|S1'), ('u', 'uint32')],
        ]:
            A = new_array(shape, dtype=dtype)
            
            bufs = serialize_object(A)
            B, r = deserialize_object(bufs)
            nt.assert_equal(r, [])
            nt.assert_equal(A.shape, B.shape)
            nt.assert_equal(A.dtype, B.dtype)
            assert_array_equal(A,B)

@dec.skip_without('numpy')
def test_numpy_in_seq():
    import numpy
    from numpy.testing.utils import assert_array_equal
    for shape in SHAPES:
        for dtype in DTYPES:
            A = new_array(shape, dtype=dtype)
            bufs = serialize_object((A,1,2,b'hello'))
            canned = pickle.loads(bufs[0])
            nt.assert_is_instance(canned[0], CannedArray)
            tup, r = deserialize_object(bufs)
            B = tup[0]
            nt.assert_equal(r, [])
            nt.assert_equal(A.shape, B.shape)
            nt.assert_equal(A.dtype, B.dtype)
            assert_array_equal(A,B)

@dec.skip_without('numpy')
def test_numpy_in_dict():
    import numpy
    from numpy.testing.utils import assert_array_equal
    for shape in SHAPES:
        for dtype in DTYPES:
            A = new_array(shape, dtype=dtype)
            bufs = serialize_object(dict(a=A,b=1,c=range(20)))
            canned = pickle.loads(bufs[0])
            nt.assert_is_instance(canned['a'], CannedArray)
            d, r = deserialize_object(bufs)
            B = d['a']
            nt.assert_equal(r, [])
            nt.assert_equal(A.shape, B.shape)
            nt.assert_equal(A.dtype, B.dtype)
            assert_array_equal(A,B)

def test_class():
    @interactive
    class C(object):
        a=5
    bufs = serialize_object(dict(C=C))
    canned = pickle.loads(bufs[0])
    nt.assert_is_instance(canned['C'], CannedClass)
    d, r = deserialize_object(bufs)
    C2 = d['C']
    nt.assert_equal(C2.a, C.a)

def test_class_oldstyle():
    @interactive
    class C:
        a=5
    
    bufs = serialize_object(dict(C=C))
    canned = pickle.loads(bufs[0])
    nt.assert_is_instance(canned['C'], CannedClass)
    d, r = deserialize_object(bufs)
    C2 = d['C']
    nt.assert_equal(C2.a, C.a)

def test_tuple():
    tup = (lambda x:x, 1)
    bufs = serialize_object(tup)
    canned = pickle.loads(bufs[0])
    nt.assert_is_instance(canned, tuple)
    t2, r = deserialize_object(bufs)
    nt.assert_equal(t2[0](t2[1]), tup[0](tup[1]))

point = namedtuple('point', 'x y')

def test_namedtuple():
    p = point(1,2)
    bufs = serialize_object(p)
    canned = pickle.loads(bufs[0])
    nt.assert_is_instance(canned, point)
    p2, r = deserialize_object(bufs, globals())
    nt.assert_equal(p2.x, p.x)
    nt.assert_equal(p2.y, p.y)

def test_list():
    lis = [lambda x:x, 1]
    bufs = serialize_object(lis)
    canned = pickle.loads(bufs[0])
    nt.assert_is_instance(canned, list)
    l2, r = deserialize_object(bufs)
    nt.assert_equal(l2[0](l2[1]), lis[0](lis[1]))

def test_class_inheritance():
    @interactive
    class C(object):
        a=5

    @interactive
    class D(C):
        b=10
    
    bufs = serialize_object(dict(D=D))
    canned = pickle.loads(bufs[0])
    nt.assert_is_instance(canned['D'], CannedClass)
    d, r = deserialize_object(bufs)
    D2 = d['D']
    nt.assert_equal(D2.a, D.a)
    nt.assert_equal(D2.b, D.b)
