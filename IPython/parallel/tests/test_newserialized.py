"""test serialization with newserialized

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

from unittest import TestCase

from IPython.testing.decorators import parametric
from IPython.utils import newserialized as ns
from IPython.utils.pickleutil import can, uncan, CannedObject, CannedFunction
from IPython.parallel.tests.clienttest import skip_without

if sys.version_info[0] >= 3:
    buffer = memoryview

class CanningTestCase(TestCase):
    def test_canning(self):
        d = dict(a=5,b=6)
        cd = can(d)
        self.assertTrue(isinstance(cd, dict))

    def test_canned_function(self):
        f = lambda : 7
        cf = can(f)
        self.assertTrue(isinstance(cf, CannedFunction))
    
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
    def run_roundtrip(self, obj):
        o = uncan(can(obj))
        assert o == obj, "failed assertion: %r == %r"%(o,obj)
    
    def test_serialized_interfaces(self):

        us = {'a':10, 'b':range(10)}
        s = ns.serialize(us)
        uus = ns.unserialize(s)
        self.assertTrue(isinstance(s, ns.SerializeIt))
        self.assertEquals(uus, us)

    def test_pickle_serialized(self):
        obj = {'a':1.45345, 'b':'asdfsdf', 'c':10000L}
        original = ns.UnSerialized(obj)
        originalSer = ns.SerializeIt(original)
        firstData = originalSer.getData()
        firstTD = originalSer.getTypeDescriptor()
        firstMD = originalSer.getMetadata()
        self.assertEquals(firstTD, 'pickle')
        self.assertEquals(firstMD, {})
        unSerialized = ns.UnSerializeIt(originalSer)
        secondObj = unSerialized.getObject()
        for k, v in secondObj.iteritems():
            self.assertEquals(obj[k], v)
        secondSer = ns.SerializeIt(ns.UnSerialized(secondObj))
        self.assertEquals(firstData, secondSer.getData())
        self.assertEquals(firstTD, secondSer.getTypeDescriptor() )
        self.assertEquals(firstMD, secondSer.getMetadata())
    
    @skip_without('numpy')
    def test_ndarray_serialized(self):
        import numpy
        a = numpy.linspace(0.0, 1.0, 1000)
        unSer1 = ns.UnSerialized(a)
        ser1 = ns.SerializeIt(unSer1)
        td = ser1.getTypeDescriptor()
        self.assertEquals(td, 'ndarray')
        md = ser1.getMetadata()
        self.assertEquals(md['shape'], a.shape)
        self.assertEquals(md['dtype'], a.dtype.str)
        buff = ser1.getData()
        self.assertEquals(buff, buffer(a))
        s = ns.Serialized(buff, td, md)
        final = ns.unserialize(s)
        self.assertEquals(buffer(a), buffer(final))
        self.assertTrue((a==final).all())
        self.assertEquals(a.dtype.str, final.dtype.str)
        self.assertEquals(a.shape, final.shape)
        # test non-copying:
        a[2] = 1e9
        self.assertTrue((a==final).all())
    
    def test_uncan_function_globals(self):
        """test that uncanning a module function restores it into its module"""
        from re import search
        cf = can(search)
        csearch = uncan(cf)
        self.assertEqual(csearch.__module__, search.__module__)
        self.assertNotEqual(csearch('asd', 'asdf'), None)
        csearch = uncan(cf, dict(a=5))
        self.assertEqual(csearch.__module__, search.__module__)
        self.assertNotEqual(csearch('asd', 'asdf'), None)
        
        