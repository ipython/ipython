"""test serialization with newserialized"""

from unittest import TestCase

import nose.tools as nt

from IPython.testing.parametric import parametric
from IPython.utils import newserialized as ns
from IPython.utils.pickleutil import can, uncan, CannedObject, CannedFunction
from IPython.zmq.parallel.tests.clienttest import skip_without


class CanningTestCase(TestCase):
    def test_canning(self):
        d = dict(a=5,b=6)
        cd = can(d)
        nt.assert_true(isinstance(cd, dict))

    def test_canned_function(self):
        f = lambda : 7
        cf = can(f)
        nt.assert_true(isinstance(cf, CannedFunction))
    
    @parametric
    def test_can_roundtrip(cls):
        objs = [
            dict(),
            set(),
            list(),
            ['a',1,['a',1],u'e'],
        ]
        return map(cls.run_roundtrip, objs)
    
    @classmethod
    def run_roundtrip(cls, obj):
        o = uncan(can(obj))
        nt.assert_equals(obj, o)
    
    def test_serialized_interfaces(self):

        us = {'a':10, 'b':range(10)}
        s = ns.serialize(us)
        uus = ns.unserialize(s)
        nt.assert_true(isinstance(s, ns.SerializeIt))
        nt.assert_equals(uus, us)

    def test_pickle_serialized(self):
        obj = {'a':1.45345, 'b':'asdfsdf', 'c':10000L}
        original = ns.UnSerialized(obj)
        originalSer = ns.SerializeIt(original)
        firstData = originalSer.getData()
        firstTD = originalSer.getTypeDescriptor()
        firstMD = originalSer.getMetadata()
        nt.assert_equals(firstTD, 'pickle')
        nt.assert_equals(firstMD, {})
        unSerialized = ns.UnSerializeIt(originalSer)
        secondObj = unSerialized.getObject()
        for k, v in secondObj.iteritems():
            nt.assert_equals(obj[k], v)
        secondSer = ns.SerializeIt(ns.UnSerialized(secondObj))
        nt.assert_equals(firstData, secondSer.getData())
        nt.assert_equals(firstTD, secondSer.getTypeDescriptor() )
        nt.assert_equals(firstMD, secondSer.getMetadata())
    
    @skip_without('numpy')
    def test_ndarray_serialized(self):
        import numpy
        a = numpy.linspace(0.0, 1.0, 1000)
        unSer1 = ns.UnSerialized(a)
        ser1 = ns.SerializeIt(unSer1)
        td = ser1.getTypeDescriptor()
        nt.assert_equals(td, 'ndarray')
        md = ser1.getMetadata()
        nt.assert_equals(md['shape'], a.shape)
        nt.assert_equals(md['dtype'], a.dtype.str)
        buff = ser1.getData()
        nt.assert_equals(buff, numpy.getbuffer(a))
        s = ns.Serialized(buff, td, md)
        final = ns.unserialize(s)
        nt.assert_equals(numpy.getbuffer(a), numpy.getbuffer(final))
        nt.assert_true((a==final).all())
        nt.assert_equals(a.dtype.str, final.dtype.str)
        nt.assert_equals(a.shape, final.shape)
        # test non-copying:
        a[2] = 1e9
        nt.assert_true((a==final).all())
        
        
        