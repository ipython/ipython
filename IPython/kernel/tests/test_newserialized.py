# encoding: utf-8

"""This file contains unittests for the shell.py module."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

try:
    import zope.interface as zi
    from twisted.trial import unittest
    from IPython.testing.util import DeferredTestCase

    from IPython.kernel.newserialized import \
        ISerialized, \
        IUnSerialized, \
        Serialized, \
        UnSerialized, \
        SerializeIt, \
        UnSerializeIt
except ImportError:
    import nose
    raise nose.SkipTest("This test requires zope.interface, Twisted and Foolscap")

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

class SerializedTestCase(unittest.TestCase):

    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def testSerializedInterfaces(self):

        us = UnSerialized({'a':10, 'b':range(10)})
        s = ISerialized(us)
        uss = IUnSerialized(s)
        self.assert_(ISerialized.providedBy(s))
        self.assert_(IUnSerialized.providedBy(us))
        self.assert_(IUnSerialized.providedBy(uss))
        for m in list(ISerialized):
            self.assert_(hasattr(s, m))
        for m in list(IUnSerialized):
            self.assert_(hasattr(us, m))
        for m in list(IUnSerialized):
            self.assert_(hasattr(uss, m))

    def testPickleSerialized(self):
        obj = {'a':1.45345, 'b':'asdfsdf', 'c':10000L}
        original = UnSerialized(obj)
        originalSer = ISerialized(original)
        firstData = originalSer.getData()
        firstTD = originalSer.getTypeDescriptor()
        firstMD = originalSer.getMetadata()
        self.assert_(firstTD == 'pickle')
        self.assert_(firstMD == {})
        unSerialized = IUnSerialized(originalSer)
        secondObj = unSerialized.getObject()
        for k, v in secondObj.iteritems():
            self.assert_(obj[k] == v)
        secondSer = ISerialized(UnSerialized(secondObj))
        self.assert_(firstData == secondSer.getData())
        self.assert_(firstTD == secondSer.getTypeDescriptor() )
        self.assert_(firstMD == secondSer.getMetadata())
    
    def testNDArraySerialized(self):
        try:
            import numpy
        except ImportError:
            pass
        else:
            a = numpy.linspace(0.0, 1.0, 1000)
            unSer1 = UnSerialized(a)
            ser1 = ISerialized(unSer1)
            td = ser1.getTypeDescriptor()
            self.assert_(td == 'ndarray')
            md = ser1.getMetadata()
            self.assert_(md['shape'] == a.shape)
            self.assert_(md['dtype'] == a.dtype.str)
            buff = ser1.getData()
            self.assert_(buff == numpy.getbuffer(a))
            s = Serialized(buff, td, md)
            us = IUnSerialized(s)
            final = us.getObject()
            self.assert_(numpy.getbuffer(a) == numpy.getbuffer(final))
            self.assert_(a.dtype.str == final.dtype.str)
            self.assert_(a.shape == final.shape)
        
        
