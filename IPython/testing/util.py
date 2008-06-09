# encoding: utf-8
"""This file contains utility classes for performing tests with Deferreds.
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from twisted.trial import unittest
from twisted.internet import defer

class DeferredTestCase(unittest.TestCase):
    
    def assertDeferredEquals(self, deferred, expectedResult,
	                              chainDeferred=None):
        """Calls assertEquals on the result of the deferred and expectedResult.
        
        chainDeferred can be used to pass in previous Deferred objects that
        have tests being run on them.  This chaining of Deferred's in tests
        is needed to insure that all Deferred's are cleaned up at the end of
        a test.
        """
        
        if chainDeferred is None:
            chainDeferred = defer.succeed(None)
	       
        def gotResult(actualResult):
            self.assertEquals(actualResult, expectedResult)
        
        deferred.addCallback(gotResult)
                    
        return chainDeferred.addCallback(lambda _: deferred)
    
    def assertDeferredRaises(self, deferred, expectedException,
	                              chainDeferred=None):
        """Calls assertRaises on the Failure of the deferred and expectedException.
        
        chainDeferred can be used to pass in previous Deferred objects that
        have tests being run on them.  This chaining of Deferred's in tests
        is needed to insure that all Deferred's are cleaned up at the end of
        a test.
        """
        
        if chainDeferred is None:
            chainDeferred = defer.succeed(None)

        def gotFailure(f):
            #f.printTraceback()
            self.assertRaises(expectedException, f.raiseException)
            #return f
        
        deferred.addBoth(gotFailure)
            
        return chainDeferred.addCallback(lambda _: deferred)

