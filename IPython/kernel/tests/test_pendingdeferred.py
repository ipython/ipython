#!/usr/bin/env python
# encoding: utf-8

"""Tests for pendingdeferred.py"""

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
    from twisted.internet import defer
    from twisted.python import failure

    from IPython.testing.util import DeferredTestCase
    import IPython.kernel.pendingdeferred as pd
    from IPython.kernel import error
    from IPython.kernel.util import printer
except ImportError:
    import nose
    raise nose.SkipTest("This test requires zope.interface, Twisted and Foolscap")
    
class Foo(object):

    def bar(self, bahz):
        return defer.succeed('blahblah: %s' % bahz)

class TwoPhaseFoo(pd.PendingDeferredManager):

    def __init__(self, foo):
        self.foo = foo
        pd.PendingDeferredManager.__init__(self)

    @pd.two_phase
    def bar(self, bahz):
        return self.foo.bar(bahz)

class PendingDeferredManagerTest(DeferredTestCase):

    def setUp(self):
        self.pdm = pd.PendingDeferredManager()
    
    def tearDown(self):
        pass

    def testBasic(self):
        dDict = {}
        # Create 10 deferreds and save them
        for i in range(10):
            d = defer.Deferred()
            did = self.pdm.save_pending_deferred(d)
            dDict[did] = d
        # Make sure they are begin saved
        for k in dDict.keys():
            self.assert_(self.pdm.quick_has_id(k))
        # Get the pending deferred (block=True), then callback with 'foo' and compare
        for did in dDict.keys()[0:5]:
            d = self.pdm.get_pending_deferred(did,block=True)
            dDict[did].callback('foo')
            d.addCallback(lambda r: self.assert_(r=='foo'))
        # Get the pending deferreds with (block=False) and make sure ResultNotCompleted is raised
        for did in dDict.keys()[5:10]:
            d = self.pdm.get_pending_deferred(did,block=False)
            d.addErrback(lambda f: self.assertRaises(error.ResultNotCompleted, f.raiseException))
        # Now callback the last 5, get them and compare.
        for did in dDict.keys()[5:10]:
            dDict[did].callback('foo')
            d = self.pdm.get_pending_deferred(did,block=False)
            d.addCallback(lambda r: self.assert_(r=='foo'))

    def test_save_then_delete(self):
        d = defer.Deferred()
        did = self.pdm.save_pending_deferred(d)
        self.assert_(self.pdm.quick_has_id(did))
        self.pdm.delete_pending_deferred(did)
        self.assert_(not self.pdm.quick_has_id(did))

    def test_save_get_delete(self):
        d = defer.Deferred()
        did = self.pdm.save_pending_deferred(d)
        d2 = self.pdm.get_pending_deferred(did,True)
        d2.addErrback(lambda f: self.assertRaises(error.AbortedPendingDeferredError, f.raiseException))
        self.pdm.delete_pending_deferred(did)
        return d2

    def test_double_get(self):
        d = defer.Deferred()
        did = self.pdm.save_pending_deferred(d)
        d2 = self.pdm.get_pending_deferred(did,True)
        d3 = self.pdm.get_pending_deferred(did,True)
        d3.addErrback(lambda f: self.assertRaises(error.InvalidDeferredID, f.raiseException))

    def test_get_after_callback(self):
        d = defer.Deferred()
        did = self.pdm.save_pending_deferred(d)
        d.callback('foo')
        d2 = self.pdm.get_pending_deferred(did,True)
        d2.addCallback(lambda r: self.assertEquals(r,'foo'))
        self.assert_(not self.pdm.quick_has_id(did))

    def test_get_before_callback(self):
        d = defer.Deferred()
        did = self.pdm.save_pending_deferred(d)
        d2 = self.pdm.get_pending_deferred(did,True)
        d.callback('foo')
        d2.addCallback(lambda r: self.assertEquals(r,'foo'))
        self.assert_(not self.pdm.quick_has_id(did))
        d = defer.Deferred()
        did = self.pdm.save_pending_deferred(d)
        d2 = self.pdm.get_pending_deferred(did,True)
        d2.addCallback(lambda r: self.assertEquals(r,'foo'))
        d.callback('foo')
        self.assert_(not self.pdm.quick_has_id(did))

    def test_get_after_errback(self):
        class MyError(Exception):
            pass
        d = defer.Deferred()
        did = self.pdm.save_pending_deferred(d)
        d.errback(failure.Failure(MyError('foo')))
        d2 = self.pdm.get_pending_deferred(did,True)
        d2.addErrback(lambda f: self.assertRaises(MyError, f.raiseException))
        self.assert_(not self.pdm.quick_has_id(did))

    def test_get_before_errback(self):
        class MyError(Exception):
            pass
        d = defer.Deferred()
        did = self.pdm.save_pending_deferred(d)
        d2 = self.pdm.get_pending_deferred(did,True)
        d.errback(failure.Failure(MyError('foo')))
        d2.addErrback(lambda f: self.assertRaises(MyError, f.raiseException))
        self.assert_(not self.pdm.quick_has_id(did))
        d = defer.Deferred()
        did = self.pdm.save_pending_deferred(d)
        d2 = self.pdm.get_pending_deferred(did,True)
        d2.addErrback(lambda f: self.assertRaises(MyError, f.raiseException))
        d.errback(failure.Failure(MyError('foo')))
        self.assert_(not self.pdm.quick_has_id(did))
    
    def test_noresult_noblock(self):
        d = defer.Deferred()
        did = self.pdm.save_pending_deferred(d)
        d2 = self.pdm.get_pending_deferred(did,False)
        d2.addErrback(lambda f: self.assertRaises(error.ResultNotCompleted, f.raiseException))

    def test_with_callbacks(self):
        d = defer.Deferred()
        d.addCallback(lambda r: r+' foo')
        d.addCallback(lambda r: r+' bar')
        did = self.pdm.save_pending_deferred(d)
        d2 = self.pdm.get_pending_deferred(did,True)
        d.callback('bam')
        d2.addCallback(lambda r: self.assertEquals(r,'bam foo bar'))

    def test_with_errbacks(self):
        class MyError(Exception):
            pass
        d = defer.Deferred()
        d.addCallback(lambda r: 'foo')
        d.addErrback(lambda f: 'caught error')
        did = self.pdm.save_pending_deferred(d)
        d2 = self.pdm.get_pending_deferred(did,True)
        d.errback(failure.Failure(MyError('bam')))
        d2.addErrback(lambda f: self.assertRaises(MyError, f.raiseException))

    def test_nested_deferreds(self):
        d = defer.Deferred()
        d2 = defer.Deferred()
        d.addCallback(lambda r: d2)
        did = self.pdm.save_pending_deferred(d)
        d.callback('foo')
        d3 = self.pdm.get_pending_deferred(did,False)
        d3.addErrback(lambda f: self.assertRaises(error.ResultNotCompleted, f.raiseException))
        d2.callback('bar')
        d3 = self.pdm.get_pending_deferred(did,False)
        d3.addCallback(lambda r: self.assertEquals(r,'bar'))

