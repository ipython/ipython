"""test serialization tools"""

#-------------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import pickle

import nose.tools as nt

# from unittest import TestCaes
from IPython.kernel.zmq.serialize import serialize_object, unserialize_object
from IPython.testing import decorators as dec
from IPython.utils.pickleutil import CannedArray, CannedClass
from IPython.parallel import interactive

#-------------------------------------------------------------------------------
# Globals and Utilities
#-------------------------------------------------------------------------------

def roundtrip(obj):
    """roundtrip an object through serialization"""
    bufs = serialize_object(obj)
    obj2, remainder = unserialize_object(bufs)
    nt.assert_equals(remainder, [])
    return obj2

class C(object):
    """dummy class for """
    
    def __init__(self, **kwargs):
        for key,value in kwargs.iteritems():
            setattr(self, key, value)

SHAPES = ((100,), (1024,10), (10,8,6,5), (), (0,))
DTYPES = ('uint8', 'float64', 'int32', [('g', 'float32')], '|S10')
#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

@dec.parametric
def test_roundtrip_simple():
    for obj in [
        'hello',
        dict(a='b', b=10),
        [1,2,'hi'],
        (b'123', 'hello'),
    ]:
        obj2 = roundtrip(obj)
        yield nt.assert_equals(obj, obj2)

@dec.parametric
def test_roundtrip_nested():
    for obj in [
        dict(a=range(5), b={1:b'hello'}),
        [range(5),[range(3),(1,[b'whoda'])]],
    ]:
        obj2 = roundtrip(obj)
        yield nt.assert_equals(obj, obj2)

@dec.parametric
def test_roundtrip_buffered():
    for obj in [
        dict(a=b"x"*1025),
        b"hello"*500,
        [b"hello"*501, 1,2,3]
    ]:
        bufs = serialize_object(obj)
        yield nt.assert_equals(len(bufs), 2)
        obj2, remainder = unserialize_object(bufs)
        yield nt.assert_equals(remainder, [])
        yield nt.assert_equals(obj, obj2)

def _scrub_nan(A):
    """scrub nans out of empty arrays
    
    since nan != nan
    """
    import numpy
    if A.dtype.fields and A.shape:
        for field in A.dtype.fields.keys():
            try:
                A[field][numpy.isnan(A[field])] = 0
            except (TypeError, NotImplementedError):
                # e.g. str dtype
                pass

@dec.parametric
@dec.skip_without('numpy')
def test_numpy():
    import numpy
    from numpy.testing.utils import assert_array_equal
    for shape in SHAPES:
        for dtype in DTYPES:
            A = numpy.empty(shape, dtype=dtype)
            _scrub_nan(A)
            bufs = serialize_object(A)
            B, r = unserialize_object(bufs)
            yield nt.assert_equals(r, [])
            yield nt.assert_equals(A.shape, B.shape)
            yield nt.assert_equals(A.dtype, B.dtype)
            yield assert_array_equal(A,B)

@dec.parametric
@dec.skip_without('numpy')
def test_recarray():
    import numpy
    from numpy.testing.utils import assert_array_equal
    for shape in SHAPES:
        for dtype in [
            [('f', float), ('s', '|S10')],
            [('n', int), ('s', '|S1'), ('u', 'uint32')],
        ]:
            A = numpy.empty(shape, dtype=dtype)
            _scrub_nan(A)
            
            bufs = serialize_object(A)
            B, r = unserialize_object(bufs)
            yield nt.assert_equals(r, [])
            yield nt.assert_equals(A.shape, B.shape)
            yield nt.assert_equals(A.dtype, B.dtype)
            yield assert_array_equal(A,B)

@dec.parametric
@dec.skip_without('numpy')
def test_numpy_in_seq():
    import numpy
    from numpy.testing.utils import assert_array_equal
    for shape in SHAPES:
        for dtype in DTYPES:
            A = numpy.empty(shape, dtype=dtype)
            _scrub_nan(A)
            bufs = serialize_object((A,1,2,b'hello'))
            canned = pickle.loads(bufs[0])
            yield nt.assert_true(canned[0], CannedArray)
            tup, r = unserialize_object(bufs)
            B = tup[0]
            yield nt.assert_equals(r, [])
            yield nt.assert_equals(A.shape, B.shape)
            yield nt.assert_equals(A.dtype, B.dtype)
            yield assert_array_equal(A,B)

@dec.parametric
@dec.skip_without('numpy')
def test_numpy_in_dict():
    import numpy
    from numpy.testing.utils import assert_array_equal
    for shape in SHAPES:
        for dtype in DTYPES:
            A = numpy.empty(shape, dtype=dtype)
            _scrub_nan(A)
            bufs = serialize_object(dict(a=A,b=1,c=range(20)))
            canned = pickle.loads(bufs[0])
            yield nt.assert_true(canned['a'], CannedArray)
            d, r = unserialize_object(bufs)
            B = d['a']
            yield nt.assert_equals(r, [])
            yield nt.assert_equals(A.shape, B.shape)
            yield nt.assert_equals(A.dtype, B.dtype)
            yield assert_array_equal(A,B)

@dec.parametric
def test_class():
    @interactive
    class C(object):
        a=5
    bufs = serialize_object(dict(C=C))
    canned = pickle.loads(bufs[0])
    yield nt.assert_true(canned['C'], CannedClass)
    d, r = unserialize_object(bufs)
    C2 = d['C']
    yield nt.assert_equal(C2.a, C.a)

@dec.parametric
def test_class_oldstyle():
    @interactive
    class C:
        a=5
    
    bufs = serialize_object(dict(C=C))
    canned = pickle.loads(bufs[0])
    yield nt.assert_true(canned['C'], CannedClass)
    d, r = unserialize_object(bufs)
    C2 = d['C']
    yield nt.assert_equal(C2.a, C.a)

@dec.parametric
def test_class_inheritance():
    @interactive
    class C(object):
        a=5

    @interactive
    class D(C):
        b=10
    
    bufs = serialize_object(dict(D=D))
    canned = pickle.loads(bufs[0])
    yield nt.assert_true(canned['D'], CannedClass)
    d, r = unserialize_object(bufs)
    D2 = d['D']
    yield nt.assert_equal(D2.a, D.a)
    yield nt.assert_equal(D2.b, D.b)
