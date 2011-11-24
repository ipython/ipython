"""Implementation of the parametric test support for Python 3.x.

Thanks for the py3 version to Robert Collins, from the Testing in Python
mailing list.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2009-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import unittest
from unittest import TestSuite

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------


def isgenerator(func):
    return hasattr(func,'_generator')


class IterCallableSuite(TestSuite):
   def __init__(self, iterator, adapter):
       self._iter = iterator
       self._adapter = adapter
   def __iter__(self):
       yield self._adapter(self._iter.__next__)

class ParametricTestCase(unittest.TestCase):
   """Write parametric tests in normal unittest testcase form.

   Limitations: the last iteration misses printing out a newline when
   running in verbose mode.
   """

   def run(self, result=None):
       testMethod = getattr(self, self._testMethodName)
       # For normal tests, we just call the base class and return that
       if isgenerator(testMethod):
           def adapter(next_test):
               ftc = unittest.FunctionTestCase(next_test,
                                               self.setUp,
                                               self.tearDown)
               self._nose_case = ftc   # Nose 1.0 rejects the test without this
               return ftc

           return IterCallableSuite(testMethod(),adapter).run(result)
       else:
           return super(ParametricTestCase, self).run(result)


def parametric(func):
   """Decorator to make a simple function into a normal test via
unittest."""
   # Hack, until I figure out how to write isgenerator() for python3!!
   func._generator = True

   class Tester(ParametricTestCase):
       test = staticmethod(func)

   Tester.__name__ = func.__name__

   return Tester
