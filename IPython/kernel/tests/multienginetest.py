# encoding: utf-8

""""""

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

from twisted.internet import defer

from IPython.kernel import engineservice as es
from IPython.kernel import multiengine as me
from IPython.kernel import newserialized
from IPython.testing import util
from IPython.testing.parametric import parametric, Parametric
from IPython.kernel import newserialized
from IPython.kernel.util import printer
from IPython.kernel.error import (InvalidEngineID,
    NoEnginesRegistered,
    CompositeError,
    InvalidDeferredID)
from IPython.kernel.tests.engineservicetest import validCommands, invalidCommands
from IPython.kernel.core.interpreter import Interpreter


#-------------------------------------------------------------------------------
# Base classes and utilities
#-------------------------------------------------------------------------------

class IMultiEngineBaseTestCase(object):
    """Basic utilities for working with multiengine tests.

    Some subclass should define:

    * self.multiengine
    * self.engines to keep track of engines for clean up"""

    def createShell(self):
        return Interpreter()

    def addEngine(self, n=1):
        for i in range(n):
            e = es.EngineService()
            e.startService()
            regDict = self.controller.register_engine(es.QueuedEngine(e), None)
            e.id = regDict['id']
            self.engines.append(e)


def testf(x):
    return 2.0*x


globala = 99


def testg(x):
    return  globala*x


def isdid(did):
    if not isinstance(did, str):
        return False
    if not len(did)==40:
        return False
    return True


def _raise_it(f):
    try:
        f.raiseException()
    except CompositeError, e:
        e.raise_exception()

#-------------------------------------------------------------------------------
# IMultiEngineTestCase
#-------------------------------------------------------------------------------

class IMultiEngineTestCase(IMultiEngineBaseTestCase):
    """A test for any object that implements IEngineMultiplexer.

    self.multiengine must be defined and implement IEngineMultiplexer.
    """

    def testIMultiEngineInterface(self):
        """Does self.engine claim to implement IEngineCore?"""
        self.assert_(me.IEngineMultiplexer.providedBy(self.multiengine))
        self.assert_(me.IMultiEngine.providedBy(self.multiengine))

    def testIEngineMultiplexerInterfaceMethods(self):
        """Does self.engine have the methods and attributes in IEngineCore."""
        for m in list(me.IEngineMultiplexer):
            self.assert_(hasattr(self.multiengine, m))

    def testIEngineMultiplexerDeferreds(self):
        self.addEngine(1)
        d= self.multiengine.execute('a=5', targets=0)
        d.addCallback(lambda _: self.multiengine.push(dict(a=5),targets=0))
        d.addCallback(lambda _: self.multiengine.push(dict(a=5, b='asdf', c=[1,2,3]),targets=0))
        d.addCallback(lambda _: self.multiengine.pull(('a','b','c'),targets=0))
        d.addCallback(lambda _: self.multiengine.get_result(targets=0))
        d.addCallback(lambda _: self.multiengine.reset(targets=0))
        d.addCallback(lambda _: self.multiengine.keys(targets=0))
        d.addCallback(lambda _: self.multiengine.push_serialized(dict(a=newserialized.serialize(10)),targets=0))
        d.addCallback(lambda _: self.multiengine.pull_serialized('a',targets=0))
        d.addCallback(lambda _: self.multiengine.clear_queue(targets=0))
        d.addCallback(lambda _: self.multiengine.queue_status(targets=0))
        return d

    def testInvalidEngineID(self):
         self.addEngine(1)
         badID = 100
         d = self.multiengine.execute('a=5', targets=badID)
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.push(dict(a=5), targets=badID))
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.pull('a', targets=badID))
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.reset(targets=badID))
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.keys(targets=badID))
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.push_serialized(dict(a=newserialized.serialize(10)), targets=badID))
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.pull_serialized('a', targets=badID))
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.queue_status(targets=badID))
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         return d

    def testNoEnginesRegistered(self):
        badID = 'all'
        d= self.multiengine.execute('a=5', targets=badID)
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.push(dict(a=5), targets=badID))
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.pull('a', targets=badID))
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.get_result(targets=badID))
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.reset(targets=badID))
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.keys(targets=badID))
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.push_serialized(dict(a=newserialized.serialize(10)), targets=badID))
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.pull_serialized('a', targets=badID))
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.queue_status(targets=badID))
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        return d

    def runExecuteAll(self, d, cmd, shell):
        actual = shell.execute(cmd)
        d.addCallback(lambda _: self.multiengine.execute(cmd))
        def compare(result):
            for r in result:
                actual['id'] = r['id']
                self.assertEquals(r, actual)
        d.addCallback(compare)

    def testExecuteAll(self):
        self.addEngine(4)
        d= defer.Deferred()
        shell = Interpreter()
        for cmd in validCommands:
                self.runExecuteAll(d, cmd, shell)
        d.callback(None)
        return d

    # The following two methods show how to do parametrized
    # tests.  This is really slick!  Same is used above.
    def runExecuteFailures(self, cmd, exc):
        self.addEngine(4)
        d= self.multiengine.execute(cmd)
        d.addErrback(lambda f: self.assertRaises(exc, _raise_it, f))
        return d

    @parametric
    def testExecuteFailuresMultiEng(cls):
        return [(cls.runExecuteFailures,cmd,exc) for
                cmd,exc in invalidCommands]

    def testPushPull(self):
        self.addEngine(1)
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d= self.multiengine.push(dict(key=objs[0]), targets=0)
        d.addCallback(lambda _: self.multiengine.pull('key', targets=0))
        d.addCallback(lambda r: self.assertEquals(r, [objs[0]]))
        d.addCallback(lambda _: self.multiengine.push(dict(key=objs[1]), targets=0))
        d.addCallback(lambda _: self.multiengine.pull('key', targets=0))
        d.addCallback(lambda r: self.assertEquals(r, [objs[1]]))
        d.addCallback(lambda _: self.multiengine.push(dict(key=objs[2]), targets=0))
        d.addCallback(lambda _: self.multiengine.pull('key', targets=0))
        d.addCallback(lambda r: self.assertEquals(r, [objs[2]]))
        d.addCallback(lambda _: self.multiengine.push(dict(key=objs[3]), targets=0))
        d.addCallback(lambda _: self.multiengine.pull('key', targets=0))
        d.addCallback(lambda r: self.assertEquals(r, [objs[3]]))
        d.addCallback(lambda _: self.multiengine.reset(targets=0))
        d.addCallback(lambda _: self.multiengine.pull('a', targets=0))
        d.addErrback(lambda f: self.assertRaises(NameError, _raise_it, f))
        d.addCallback(lambda _: self.multiengine.push(dict(a=10,b=20)))
        d.addCallback(lambda _: self.multiengine.pull(('a','b')))
        d.addCallback(lambda r: self.assertEquals(r, [[10,20]]))
        return d

    def testPushPullAll(self):
        self.addEngine(4)
        d= self.multiengine.push(dict(a=10))
        d.addCallback(lambda _: self.multiengine.pull('a'))
        d.addCallback(lambda r: self.assert_(r==[10,10,10,10]))
        d.addCallback(lambda _: self.multiengine.push(dict(a=10, b=20)))
        d.addCallback(lambda _: self.multiengine.pull(('a','b')))
        d.addCallback(lambda r: self.assert_(r==4*[[10,20]]))
        d.addCallback(lambda _: self.multiengine.push(dict(a=10, b=20), targets=0))
        d.addCallback(lambda _: self.multiengine.pull(('a','b'), targets=0))
        d.addCallback(lambda r: self.assert_(r==[[10,20]]))
        d.addCallback(lambda _: self.multiengine.push(dict(a=None, b=None), targets=0))
        d.addCallback(lambda _: self.multiengine.pull(('a','b'), targets=0))
        d.addCallback(lambda r: self.assert_(r==[[None,None]]))
        return d

    def testPushPullSerialized(self):
        self.addEngine(1)
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d= self.multiengine.push_serialized(dict(key=newserialized.serialize(objs[0])), targets=0)
        d.addCallback(lambda _: self.multiengine.pull_serialized('key', targets=0))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, objs[0]))
        d.addCallback(lambda _: self.multiengine.push_serialized(dict(key=newserialized.serialize(objs[1])), targets=0))
        d.addCallback(lambda _: self.multiengine.pull_serialized('key', targets=0))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, objs[1]))
        d.addCallback(lambda _: self.multiengine.push_serialized(dict(key=newserialized.serialize(objs[2])), targets=0))
        d.addCallback(lambda _: self.multiengine.pull_serialized('key', targets=0))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, objs[2]))
        d.addCallback(lambda _: self.multiengine.push_serialized(dict(key=newserialized.serialize(objs[3])), targets=0))
        d.addCallback(lambda _: self.multiengine.pull_serialized('key', targets=0))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, objs[3]))
        d.addCallback(lambda _: self.multiengine.push(dict(a=10,b=range(5)), targets=0))
        d.addCallback(lambda _: self.multiengine.pull_serialized(('a','b'), targets=0))
        d.addCallback(lambda serial: [newserialized.IUnSerialized(s).getObject() for s in serial[0]])
        d.addCallback(lambda r: self.assertEquals(r, [10, range(5)]))
        d.addCallback(lambda _: self.multiengine.reset(targets=0))
        d.addCallback(lambda _: self.multiengine.pull_serialized('a', targets=0))
        d.addErrback(lambda f: self.assertRaises(NameError, _raise_it, f))
        return d

        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d= defer.succeed(None)
        for o in objs:
            self.multiengine.push_serialized(0, key=newserialized.serialize(o))
            value = self.multiengine.pull_serialized(0, 'key')
            value.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
            d = self.assertDeferredEquals(value,o,d)
        return d

    def runGetResultAll(self, d, cmd, shell):
        actual = shell.execute(cmd)
        d.addCallback(lambda _: self.multiengine.execute(cmd))
        d.addCallback(lambda _: self.multiengine.get_result())
        def compare(result):
            for r in result:
                actual['id'] = r['id']
                self.assertEquals(r, actual)
        d.addCallback(compare)

    def testGetResultAll(self):
        self.addEngine(4)
        d= defer.Deferred()
        shell = Interpreter()
        for cmd in validCommands:
                self.runGetResultAll(d, cmd, shell)
        d.callback(None)
        return d

    def testGetResultDefault(self):
        self.addEngine(1)
        target = 0
        cmd = 'a=5'
        shell = self.createShell()
        shellResult = shell.execute(cmd)
        def popit(dikt, key):
            dikt.pop(key)
            return dikt
        d= self.multiengine.execute(cmd, targets=target)
        d.addCallback(lambda _: self.multiengine.get_result(targets=target))
        d.addCallback(lambda r: self.assertEquals(shellResult, popit(r[0],'id')))
        return d

    def testGetResultFailure(self):
        self.addEngine(1)
        d= self.multiengine.get_result(None, targets=0)
        d.addErrback(lambda f: self.assertRaises(IndexError, _raise_it, f))
        d.addCallback(lambda _: self.multiengine.get_result(10, targets=0))
        d.addErrback(lambda f: self.assertRaises(IndexError, _raise_it, f))
        return d

    def testPushFunction(self):
        self.addEngine(1)
        d= self.multiengine.push_function(dict(f=testf), targets=0)
        d.addCallback(lambda _: self.multiengine.execute('result = f(10)', targets=0))
        d.addCallback(lambda _: self.multiengine.pull('result', targets=0))
        d.addCallback(lambda r: self.assertEquals(r[0], testf(10)))
        d.addCallback(lambda _: self.multiengine.push(dict(globala=globala), targets=0))
        d.addCallback(lambda _: self.multiengine.push_function(dict(g=testg), targets=0))
        d.addCallback(lambda _: self.multiengine.execute('result = g(10)', targets=0))
        d.addCallback(lambda _: self.multiengine.pull('result', targets=0))
        d.addCallback(lambda r: self.assertEquals(r[0], testg(10)))
        return d

    def testPullFunction(self):
        self.addEngine(1)
        d= self.multiengine.push(dict(a=globala), targets=0)
        d.addCallback(lambda _: self.multiengine.push_function(dict(f=testf), targets=0))
        d.addCallback(lambda _: self.multiengine.pull_function('f', targets=0))
        d.addCallback(lambda r: self.assertEquals(r[0](10), testf(10)))
        d.addCallback(lambda _: self.multiengine.execute("def g(x): return x*x", targets=0))
        d.addCallback(lambda _: self.multiengine.pull_function(('f','g'),targets=0))
        d.addCallback(lambda r: self.assertEquals((r[0][0](10),r[0][1](10)), (testf(10), 100)))
        return d

    def testPushFunctionAll(self):
        self.addEngine(4)
        d= self.multiengine.push_function(dict(f=testf))
        d.addCallback(lambda _: self.multiengine.execute('result = f(10)'))
        d.addCallback(lambda _: self.multiengine.pull('result'))
        d.addCallback(lambda r: self.assertEquals(r, 4*[testf(10)]))
        d.addCallback(lambda _: self.multiengine.push(dict(globala=globala)))
        d.addCallback(lambda _: self.multiengine.push_function(dict(testg=testg)))
        d.addCallback(lambda _: self.multiengine.execute('result = testg(10)'))
        d.addCallback(lambda _: self.multiengine.pull('result'))
        d.addCallback(lambda r: self.assertEquals(r, 4*[testg(10)]))
        return d

    def testPullFunctionAll(self):
        self.addEngine(4)
        d= self.multiengine.push_function(dict(f=testf))
        d.addCallback(lambda _: self.multiengine.pull_function('f'))
        d.addCallback(lambda r: self.assertEquals([func(10) for func in r], 4*[testf(10)]))
        return d

    def testGetIDs(self):
        self.addEngine(1)
        d= self.multiengine.get_ids()
        d.addCallback(lambda r: self.assertEquals(r, [0]))
        d.addCallback(lambda _: self.addEngine(3))
        d.addCallback(lambda _: self.multiengine.get_ids())
        d.addCallback(lambda r: self.assertEquals(r, [0,1,2,3]))
        return d

    def testClearQueue(self):
        self.addEngine(4)
        d= self.multiengine.clear_queue()
        d.addCallback(lambda r: self.assertEquals(r,4*[None]))
        return d

    def testQueueStatus(self):
        self.addEngine(4)
        d= self.multiengine.queue_status(targets=0)
        d.addCallback(lambda r: self.assert_(isinstance(r[0],tuple)))
        return d

    def testGetSetProperties(self):
        self.addEngine(4)
        dikt = dict(a=5, b='asdf', c=True, d=None, e=range(5))
        d= self.multiengine.set_properties(dikt)
        d.addCallback(lambda r: self.multiengine.get_properties())
        d.addCallback(lambda r: self.assertEquals(r, 4*[dikt]))
        d.addCallback(lambda r: self.multiengine.get_properties(('c',)))
        d.addCallback(lambda r: self.assertEquals(r, 4*[{'c': dikt['c']}]))
        d.addCallback(lambda r: self.multiengine.set_properties(dict(c=False)))
        d.addCallback(lambda r: self.multiengine.get_properties(('c', 'd')))
        d.addCallback(lambda r: self.assertEquals(r, 4*[dict(c=False, d=None)]))
        return d

    def testClearProperties(self):
        self.addEngine(4)
        dikt = dict(a=5, b='asdf', c=True, d=None, e=range(5))
        d= self.multiengine.set_properties(dikt)
        d.addCallback(lambda r: self.multiengine.clear_properties())
        d.addCallback(lambda r: self.multiengine.get_properties())
        d.addCallback(lambda r: self.assertEquals(r, 4*[{}]))
        return d

    def testDelHasProperties(self):
        self.addEngine(4)
        dikt = dict(a=5, b='asdf', c=True, d=None, e=range(5))
        d= self.multiengine.set_properties(dikt)
        d.addCallback(lambda r: self.multiengine.del_properties(('b','e')))
        d.addCallback(lambda r: self.multiengine.has_properties(('a','b','c','d','e')))
        d.addCallback(lambda r: self.assertEquals(r, 4*[[True, False, True, True, False]]))
        return d

Parametric(IMultiEngineTestCase)

#-------------------------------------------------------------------------------
# ISynchronousMultiEngineTestCase
#-------------------------------------------------------------------------------

class ISynchronousMultiEngineTestCase(IMultiEngineBaseTestCase):

    def testISynchronousMultiEngineInterface(self):
        """Does self.engine claim to implement IEngineCore?"""
        self.assert_(me.ISynchronousEngineMultiplexer.providedBy(self.multiengine))
        self.assert_(me.ISynchronousMultiEngine.providedBy(self.multiengine))

    def testExecute(self):
        self.addEngine(4)
        execute = self.multiengine.execute
        d= execute('a=5', targets=0, block=True)
        d.addCallback(lambda r: self.assert_(len(r)==1))
        d.addCallback(lambda _: execute('b=10'))
        d.addCallback(lambda r: self.assert_(len(r)==4))
        d.addCallback(lambda _: execute('c=30', block=False))
        d.addCallback(lambda did: self.assert_(isdid(did)))
        d.addCallback(lambda _: execute('d=[0,1,2]', block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assert_(len(r)==4))
        return d

    def testPushPull(self):
        data = dict(a=10, b=1.05, c=range(10), d={'e':(1,2),'f':'hi'})
        self.addEngine(4)
        push = self.multiengine.push
        pull = self.multiengine.pull
        d= push({'data':data}, targets=0)
        d.addCallback(lambda r: pull('data', targets=0))
        d.addCallback(lambda r: self.assertEqual(r,[data]))
        d.addCallback(lambda _: push({'data':data}))
        d.addCallback(lambda r: pull('data'))
        d.addCallback(lambda r: self.assertEqual(r,4*[data]))
        d.addCallback(lambda _: push({'data':data}, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda _: pull('data', block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assertEqual(r,4*[data]))
        d.addCallback(lambda _: push(dict(a=10,b=20)))
        d.addCallback(lambda _: pull(('a','b')))
        d.addCallback(lambda r: self.assertEquals(r, 4*[[10,20]]))
        return d

    def testPushPullFunction(self):
        self.addEngine(4)
        pushf = self.multiengine.push_function
        pullf = self.multiengine.pull_function
        push = self.multiengine.push
        pull = self.multiengine.pull
        execute = self.multiengine.execute
        d= pushf({'testf':testf}, targets=0)
        d.addCallback(lambda r: pullf('testf', targets=0))
        d.addCallback(lambda r: self.assertEqual(r[0](1.0), testf(1.0)))
        d.addCallback(lambda _: execute('r = testf(10)', targets=0))
        d.addCallback(lambda _: pull('r', targets=0))
        d.addCallback(lambda r: self.assertEquals(r[0], testf(10)))
        d.addCallback(lambda _: pushf({'testf':testf}, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda _: pullf('testf', block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assertEqual(r[0](1.0), testf(1.0)))
        d.addCallback(lambda _: execute("def g(x): return x*x", targets=0))
        d.addCallback(lambda _: pullf(('testf','g'),targets=0))
        d.addCallback(lambda r: self.assertEquals((r[0][0](10),r[0][1](10)), (testf(10), 100)))
        return d

    def testGetResult(self):
        shell = Interpreter()
        result1 = shell.execute('a=10')
        result1['id'] = 0
        result2 = shell.execute('b=20')
        result2['id'] = 0
        execute= self.multiengine.execute
        get_result = self.multiengine.get_result
        self.addEngine(1)
        d= execute('a=10')
        d.addCallback(lambda _: get_result())
        d.addCallback(lambda r: self.assertEquals(r[0], result1))
        d.addCallback(lambda _: execute('b=20'))
        d.addCallback(lambda _: get_result(1))
        d.addCallback(lambda r: self.assertEquals(r[0], result1))
        d.addCallback(lambda _: get_result(2, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assertEquals(r[0], result2))
        return d

    def testResetAndKeys(self):
        self.addEngine(1)

        #Blocking mode
        d= self.multiengine.push(dict(a=10, b=20, c=range(10)), targets=0)
        d.addCallback(lambda _: self.multiengine.keys(targets=0))
        def keys_found(keys):
            self.assert_('a' in keys[0])
            self.assert_('b' in keys[0])
            self.assert_('b' in keys[0])
        d.addCallback(keys_found)
        d.addCallback(lambda _: self.multiengine.reset(targets=0))
        d.addCallback(lambda _: self.multiengine.keys(targets=0))
        def keys_not_found(keys):
            self.assert_('a' not in keys[0])
            self.assert_('b' not in keys[0])
            self.assert_('b' not in keys[0])
        d.addCallback(keys_not_found)

        #Non-blocking mode
        d.addCallback(lambda _: self.multiengine.push(dict(a=10, b=20, c=range(10)), targets=0))
        d.addCallback(lambda _: self.multiengine.keys(targets=0, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        def keys_found(keys):
            self.assert_('a' in keys[0])
            self.assert_('b' in keys[0])
            self.assert_('b' in keys[0])
        d.addCallback(keys_found)
        d.addCallback(lambda _: self.multiengine.reset(targets=0, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda _: self.multiengine.keys(targets=0, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        def keys_not_found(keys):
            self.assert_('a' not in keys[0])
            self.assert_('b' not in keys[0])
            self.assert_('b' not in keys[0])
        d.addCallback(keys_not_found)

        return d

    def testPushPullSerialized(self):
        self.addEngine(1)
        dikt = dict(a=10,b='hi there',c=1.2345,d={'p':(1,2)})
        sdikt = {}
        for k,v in dikt.iteritems():
            sdikt[k] = newserialized.serialize(v)
        d= self.multiengine.push_serialized(dict(a=sdikt['a']), targets=0)
        d.addCallback(lambda _: self.multiengine.pull('a',targets=0))
        d.addCallback(lambda r: self.assertEquals(r[0], dikt['a']))
        d.addCallback(lambda _: self.multiengine.pull_serialized('a', targets=0))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, dikt['a']))
        d.addCallback(lambda _: self.multiengine.push_serialized(sdikt, targets=0))
        d.addCallback(lambda _: self.multiengine.pull_serialized(sdikt.keys(), targets=0))
        d.addCallback(lambda serial: [newserialized.IUnSerialized(s).getObject() for s in serial[0]])
        d.addCallback(lambda r: self.assertEquals(r, dikt.values()))
        d.addCallback(lambda _: self.multiengine.reset(targets=0))
        d.addCallback(lambda _: self.multiengine.pull_serialized('a', targets=0))
        d.addErrback(lambda f: self.assertRaises(NameError, _raise_it, f))

        #Non-blocking mode
        d.addCallback(lambda r: self.multiengine.push_serialized(dict(a=sdikt['a']), targets=0, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda _: self.multiengine.pull('a',targets=0))
        d.addCallback(lambda r: self.assertEquals(r[0], dikt['a']))
        d.addCallback(lambda _: self.multiengine.pull_serialized('a', targets=0, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, dikt['a']))
        d.addCallback(lambda _: self.multiengine.push_serialized(sdikt, targets=0, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda _: self.multiengine.pull_serialized(sdikt.keys(), targets=0, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda serial: [newserialized.IUnSerialized(s).getObject() for s in serial[0]])
        d.addCallback(lambda r: self.assertEquals(r, dikt.values()))
        d.addCallback(lambda _: self.multiengine.reset(targets=0))
        d.addCallback(lambda _: self.multiengine.pull_serialized('a', targets=0, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addErrback(lambda f: self.assertRaises(NameError, _raise_it, f))
        return d

    def testClearQueue(self):
        self.addEngine(4)
        d= self.multiengine.clear_queue()
        d.addCallback(lambda r: self.multiengine.clear_queue(block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assertEquals(r,4*[None]))
        return d

    def testQueueStatus(self):
        self.addEngine(4)
        d= self.multiengine.queue_status(targets=0)
        d.addCallback(lambda r: self.assert_(isinstance(r[0],tuple)))
        d.addCallback(lambda r: self.multiengine.queue_status(targets=0, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assert_(isinstance(r[0],tuple)))
        return d

    def testGetIDs(self):
        self.addEngine(1)
        d= self.multiengine.get_ids()
        d.addCallback(lambda r: self.assertEquals(r, [0]))
        d.addCallback(lambda _: self.addEngine(3))
        d.addCallback(lambda _: self.multiengine.get_ids())
        d.addCallback(lambda r: self.assertEquals(r, [0,1,2,3]))
        return d

    def testGetSetProperties(self):
        self.addEngine(4)
        dikt = dict(a=5, b='asdf', c=True, d=None, e=range(5))
        d= self.multiengine.set_properties(dikt)
        d.addCallback(lambda r: self.multiengine.get_properties())
        d.addCallback(lambda r: self.assertEquals(r, 4*[dikt]))
        d.addCallback(lambda r: self.multiengine.get_properties(('c',)))
        d.addCallback(lambda r: self.assertEquals(r, 4*[{'c': dikt['c']}]))
        d.addCallback(lambda r: self.multiengine.set_properties(dict(c=False)))
        d.addCallback(lambda r: self.multiengine.get_properties(('c', 'd')))
        d.addCallback(lambda r: self.assertEquals(r, 4*[dict(c=False, d=None)]))

        #Non-blocking
        d.addCallback(lambda r: self.multiengine.set_properties(dikt, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.multiengine.get_properties(block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assertEquals(r, 4*[dikt]))
        d.addCallback(lambda r: self.multiengine.get_properties(('c',), block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assertEquals(r, 4*[{'c': dikt['c']}]))
        d.addCallback(lambda r: self.multiengine.set_properties(dict(c=False), block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.multiengine.get_properties(('c', 'd'), block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assertEquals(r, 4*[dict(c=False, d=None)]))
        return d

    def testClearProperties(self):
        self.addEngine(4)
        dikt = dict(a=5, b='asdf', c=True, d=None, e=range(5))
        d= self.multiengine.set_properties(dikt)
        d.addCallback(lambda r: self.multiengine.clear_properties())
        d.addCallback(lambda r: self.multiengine.get_properties())
        d.addCallback(lambda r: self.assertEquals(r, 4*[{}]))

        #Non-blocking
        d.addCallback(lambda r: self.multiengine.set_properties(dikt, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.multiengine.clear_properties(block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.multiengine.get_properties(block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assertEquals(r, 4*[{}]))
        return d

    def testDelHasProperties(self):
        self.addEngine(4)
        dikt = dict(a=5, b='asdf', c=True, d=None, e=range(5))
        d= self.multiengine.set_properties(dikt)
        d.addCallback(lambda r: self.multiengine.del_properties(('b','e')))
        d.addCallback(lambda r: self.multiengine.has_properties(('a','b','c','d','e')))
        d.addCallback(lambda r: self.assertEquals(r, 4*[[True, False, True, True, False]]))

        #Non-blocking
        d.addCallback(lambda r: self.multiengine.set_properties(dikt, block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.multiengine.del_properties(('b','e'), block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.multiengine.has_properties(('a','b','c','d','e'), block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assertEquals(r, 4*[[True, False, True, True, False]]))
        return d

    def test_clear_pending_deferreds(self):
        self.addEngine(4)
        did_list = []
        d= self.multiengine.execute('a=10',block=False)
        d.addCallback(lambda did: did_list.append(did))
        d.addCallback(lambda _: self.multiengine.push(dict(b=10),block=False))
        d.addCallback(lambda did: did_list.append(did))
        d.addCallback(lambda _: self.multiengine.pull(('a','b'),block=False))
        d.addCallback(lambda did: did_list.append(did))
        d.addCallback(lambda _: self.multiengine.clear_pending_deferreds())
        d.addCallback(lambda _: self.multiengine.get_pending_deferred(did_list[0],True))
        d.addErrback(lambda f: self.assertRaises(InvalidDeferredID, f.raiseException))
        d.addCallback(lambda _: self.multiengine.get_pending_deferred(did_list[1],True))
        d.addErrback(lambda f: self.assertRaises(InvalidDeferredID, f.raiseException))
        d.addCallback(lambda _: self.multiengine.get_pending_deferred(did_list[2],True))
        d.addErrback(lambda f: self.assertRaises(InvalidDeferredID, f.raiseException))
        return d

#-------------------------------------------------------------------------------
# Coordinator test cases
#-------------------------------------------------------------------------------

class IMultiEngineCoordinatorTestCase(object):

    def testScatterGather(self):
        self.addEngine(4)
        d= self.multiengine.scatter('a', range(16))
        d.addCallback(lambda r: self.multiengine.gather('a'))
        d.addCallback(lambda r: self.assertEquals(r, range(16)))
        d.addCallback(lambda _: self.multiengine.gather('asdf'))
        d.addErrback(lambda f: self.assertRaises(NameError, _raise_it, f))
        return d

    def testScatterGatherNumpy(self):
        try:
            import numpy
            from numpy.testing.utils import assert_array_equal, assert_array_almost_equal
        except:
            return
        else:
            self.addEngine(4)
            a = numpy.arange(16)
            d = self.multiengine.scatter('a', a)
            d.addCallback(lambda r: self.multiengine.gather('a'))
            d.addCallback(lambda r: assert_array_equal(r, a))
            return d

    def testMap(self):
        self.addEngine(4)
        def f(x):
            return x**2
        data = range(16)
        d= self.multiengine.map(f, data)
        d.addCallback(lambda r: self.assertEquals(r,[f(x) for x in data]))
        return d


class ISynchronousMultiEngineCoordinatorTestCase(IMultiEngineCoordinatorTestCase):

    def testScatterGatherNonblocking(self):
        self.addEngine(4)
        d= self.multiengine.scatter('a', range(16), block=False)
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.multiengine.gather('a', block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assertEquals(r, range(16)))
        return d
    
    def testScatterGatherNumpyNonblocking(self):
        try:
            import numpy
            from numpy.testing.utils import assert_array_equal, assert_array_almost_equal
        except:
            return
        else:
            self.addEngine(4)
            a = numpy.arange(16)
            d = self.multiengine.scatter('a', a, block=False)
            d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
            d.addCallback(lambda r: self.multiengine.gather('a', block=False))
            d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
            d.addCallback(lambda r: assert_array_equal(r, a))
            return d
    
    def test_clear_pending_deferreds(self):
        self.addEngine(4)
        did_list = []
        d= self.multiengine.scatter('a',range(16),block=False)
        d.addCallback(lambda did: did_list.append(did))
        d.addCallback(lambda _: self.multiengine.gather('a',block=False))
        d.addCallback(lambda did: did_list.append(did))
        d.addCallback(lambda _: self.multiengine.map(lambda x: x, range(16),block=False))
        d.addCallback(lambda did: did_list.append(did))
        d.addCallback(lambda _: self.multiengine.clear_pending_deferreds())
        d.addCallback(lambda _: self.multiengine.get_pending_deferred(did_list[0],True))
        d.addErrback(lambda f: self.assertRaises(InvalidDeferredID, f.raiseException))
        d.addCallback(lambda _: self.multiengine.get_pending_deferred(did_list[1],True))
        d.addErrback(lambda f: self.assertRaises(InvalidDeferredID, f.raiseException))
        d.addCallback(lambda _: self.multiengine.get_pending_deferred(did_list[2],True))
        d.addErrback(lambda f: self.assertRaises(InvalidDeferredID, f.raiseException))
        return d

#-------------------------------------------------------------------------------
# Extras test cases
#-------------------------------------------------------------------------------

class IMultiEngineExtrasTestCase(object):

    def testZipPull(self):
        self.addEngine(4)
        d= self.multiengine.push(dict(a=10,b=20))
        d.addCallback(lambda r: self.multiengine.zip_pull(('a','b')))
        d.addCallback(lambda r: self.assert_(r, [4*[10],4*[20]]))
        return d

    def testRun(self):
        self.addEngine(4)
        import tempfile
        fname = tempfile.mktemp('foo.py')
        f= open(fname, 'w')
        f.write('a = 10\nb=30')
        f.close()
        d= self.multiengine.run(fname)
        d.addCallback(lambda r: self.multiengine.pull(('a','b')))
        d.addCallback(lambda r: self.assertEquals(r, 4*[[10,30]]))
        return d


class ISynchronousMultiEngineExtrasTestCase(IMultiEngineExtrasTestCase):

    def testZipPullNonblocking(self):
        self.addEngine(4)
        d= self.multiengine.push(dict(a=10,b=20))
        d.addCallback(lambda r: self.multiengine.zip_pull(('a','b'), block=False))
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.assert_(r, [4*[10],4*[20]]))
        return d

    def testRunNonblocking(self):
        self.addEngine(4)
        import tempfile
        fname = tempfile.mktemp('foo.py')
        f= open(fname, 'w')
        f.write('a = 10\nb=30')
        f.close()
        d= self.multiengine.run(fname, block=False)
        d.addCallback(lambda did: self.multiengine.get_pending_deferred(did, True))
        d.addCallback(lambda r: self.multiengine.pull(('a','b')))
        d.addCallback(lambda r: self.assertEquals(r, 4*[[10,30]]))
        return d


#-------------------------------------------------------------------------------
# IFullSynchronousMultiEngineTestCase
#-------------------------------------------------------------------------------

class IFullSynchronousMultiEngineTestCase(ISynchronousMultiEngineTestCase,
    ISynchronousMultiEngineCoordinatorTestCase,
    ISynchronousMultiEngineExtrasTestCase):
    pass
