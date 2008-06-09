#!/usr/bin/env python
# encoding: utf-8

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

import time

from IPython.kernel import task, engineservice as es
from IPython.kernel.util import printer
from IPython.kernel import error

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

def _raise_it(f):
    try:
        f.raiseException()
    except CompositeError, e:
        e.raise_exception() 

class TaskTestBase(object):
    
    def addEngine(self, n=1):
        for i in range(n):
            e = es.EngineService()
            e.startService()
            regDict = self.controller.register_engine(es.QueuedEngine(e), None)
            e.id = regDict['id']
            self.engines.append(e)


class ITaskControllerTestCase(TaskTestBase):
        
    def testTaskIDs(self):
        self.addEngine(1)
        d = self.tc.run(task.Task('a=5'))
        d.addCallback(lambda r: self.assertEquals(r, 0))
        d.addCallback(lambda r: self.tc.run(task.Task('a=5')))
        d.addCallback(lambda r: self.assertEquals(r, 1))
        d.addCallback(lambda r: self.tc.run(task.Task('a=5')))
        d.addCallback(lambda r: self.assertEquals(r, 2))
        d.addCallback(lambda r: self.tc.run(task.Task('a=5')))
        d.addCallback(lambda r: self.assertEquals(r, 3))
        return d
    
    def testAbort(self):
        """Cannot do a proper abort test, because blocking execution prevents
        abort from being called before task completes"""
        self.addEngine(1)
        t = task.Task('a=5')
        d = self.tc.abort(0)
        d.addErrback(lambda f: self.assertRaises(IndexError, f.raiseException))
        d.addCallback(lambda _:self.tc.run(t))
        d.addCallback(self.tc.abort)
        d.addErrback(lambda f: self.assertRaises(IndexError, f.raiseException))
        return d
    
    def testAbortType(self):
        self.addEngine(1)
        d = self.tc.abort('asdfadsf')
        d.addErrback(lambda f: self.assertRaises(TypeError, f.raiseException))
        return d
    
    def testClears(self):
        self.addEngine(1)
        t = task.Task('a=1', clear_before=True, pull='b', clear_after=True)
        d = self.multiengine.execute('b=1', targets=0)
        d.addCallback(lambda _: self.tc.run(t))
        d.addCallback(lambda tid: self.tc.get_task_result(tid,block=True))
        d.addCallback(lambda tr: tr.failure)
        d.addErrback(lambda f: self.assertRaises(NameError, f.raiseException))
        d.addCallback(lambda _:self.multiengine.pull('a', targets=0))
        d.addErrback(lambda f: self.assertRaises(NameError, _raise_it, f))
        return d
    
    def testSimpleRetries(self):
        self.addEngine(1)
        t = task.Task("i += 1\nassert i == 16", pull='i',retries=10)
        t2 = task.Task("i += 1\nassert i == 16", pull='i',retries=10)
        d = self.multiengine.execute('i=0', targets=0)
        d.addCallback(lambda r: self.tc.run(t))
        d.addCallback(self.tc.get_task_result, block=True)
        d.addCallback(lambda tr: tr.ns.i)
        d.addErrback(lambda f: self.assertRaises(AssertionError, f.raiseException))
        
        d.addCallback(lambda r: self.tc.run(t2))
        d.addCallback(self.tc.get_task_result, block=True)
        d.addCallback(lambda tr: tr.ns.i)
        d.addCallback(lambda r: self.assertEquals(r, 16))
        return d
    
    def testRecoveryTasks(self):
        self.addEngine(1)
        t = task.Task("i=16", pull='i')
        t2 = task.Task("raise Exception", recovery_task=t, retries = 2)
        
        d = self.tc.run(t2)
        d.addCallback(self.tc.get_task_result, block=True)
        d.addCallback(lambda tr: tr.ns.i)
        d.addCallback(lambda r: self.assertEquals(r, 16))
        return d
    
    # def testInfiniteRecoveryLoop(self):
    #     self.addEngine(1)
    #     t = task.Task("raise Exception", retries = 5)
    #     t2 = task.Task("assert True", retries = 2, recovery_task = t)
    #     t.recovery_task = t2
    #     
    #     d = self.tc.run(t)
    #     d.addCallback(self.tc.get_task_result, block=True)
    #     d.addCallback(lambda tr: tr.ns.i)
    #     d.addBoth(printer)
    #     d.addErrback(lambda f: self.assertRaises(AssertionError, f.raiseException))
    #     return d
    # 
    def testSetupNS(self):
        self.addEngine(1)
        d = self.multiengine.execute('a=0', targets=0)
        ns = dict(a=1, b=0)
        t = task.Task("", push=ns, pull=['a','b'])
        d.addCallback(lambda r: self.tc.run(t))
        d.addCallback(self.tc.get_task_result, block=True)
        d.addCallback(lambda tr: {'a':tr.ns.a, 'b':tr['b']})
        d.addCallback(lambda r: self.assertEquals(r, ns))
        return d
    
    def testTaskResults(self):
        self.addEngine(1)
        t1 = task.Task('a=5', pull='a')
        d = self.tc.run(t1)
        d.addCallback(self.tc.get_task_result, block=True)
        d.addCallback(lambda tr: (tr.ns.a,tr['a'],tr.failure, tr.raiseException()))
        d.addCallback(lambda r: self.assertEquals(r, (5,5,None,None)))  
        
        t2 = task.Task('7=5')
        d.addCallback(lambda r: self.tc.run(t2))
        d.addCallback(self.tc.get_task_result, block=True)
        d.addCallback(lambda tr: tr.ns)
        d.addErrback(lambda f: self.assertRaises(SyntaxError, f.raiseException))
        
        t3 = task.Task('', pull='b')
        d.addCallback(lambda r: self.tc.run(t3))
        d.addCallback(self.tc.get_task_result, block=True)
        d.addCallback(lambda tr: tr.ns)
        d.addErrback(lambda f: self.assertRaises(NameError, f.raiseException))
        return d
