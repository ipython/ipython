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

import unittest
from IPython.kernel.core import shell

resultKeys = ('commandIndex', 'stdin', 'stdout', 'stderr')

class BasicShellTest(unittest.TestCase):

    def setUp(self):
        self.s = shell.InteractiveShell()
        
    def testExecute(self):
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]
        for c in commands:
            result = self.s.execute(c[1])
            self.assertEquals(result, dict(zip(resultKeys,c)))
            
    def testPutGet(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        for o in objs:
            self.s.put("key",o)
            value = self.s.get("key")
            self.assertEquals(value,o)
        self.assertRaises(TypeError, self.s.put,10)
        self.assertRaises(TypeError, self.s.get,10)
        self.s.reset()
        self.assertRaises(NameError, self.s.get, 'a')
        
    def testUpdate(self):
        d = {"a": 10, "b": 34.3434, "c": "hi there"}
        self.s.update(d)
        for k in d.keys():
            value = self.s.get(k)
            self.assertEquals(value, d[k])
        self.assertRaises(TypeError, self.s.update, [1,2,2])
        
    def testCommand(self):
        self.assertRaises(IndexError,self.s.getCommand)
        self.s.execute("a = 5")
        self.assertEquals(self.s.getCommand(), dict(zip(resultKeys, (0,"a = 5","",""))))
        self.assertEquals(self.s.getCommand(0), dict(zip(resultKeys, (0,"a = 5","",""))))
        self.s.reset()
        self.assertEquals(self.s.getLastCommandIndex(),-1)
        self.assertRaises(IndexError,self.s.getCommand)
        
        