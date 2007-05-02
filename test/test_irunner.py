#!/usr/bin/env python
"""Test suite for the irunner module.

Not the most elegant or fine-grained, but it does cover at least the bulk
functionality."""

# Global to make tests extra verbose and help debugging
VERBOSE = True

# stdlib imports
import cStringIO as StringIO
import sys
import unittest

# IPython imports
from IPython import irunner

# Testing code begins
class RunnerTestCase(unittest.TestCase):

    def setUp(self):
        self.out = StringIO.StringIO()
        #self.out = sys.stdout

    def _test_runner(self,runner,source,output):
        """Test that a given runner's input/output match."""
        
        runner.run_source(source)
        out = self.out.getvalue()
        #out = ''
        # this output contains nasty \r\n lineends, and the initial ipython
        # banner.  clean it up for comparison
        output_l = output.split()
        out_l = out.split()
        mismatch  = 0
        #if len(output_l) != len(out_l):
        #    self.fail('mismatch in number of lines')
        for n in range(len(output_l)):
            # Do a line-by-line comparison
            ol1 = output_l[n].strip()
            ol2 = out_l[n].strip()
            if ol1 != ol2:
                mismatch += 1
                if VERBOSE:
                    print '<<< line %s does not match:' % n
                    print repr(ol1)
                    print repr(ol2)
                    print '>>>'
        self.assert_(mismatch==0,'Number of mismatched lines: %s' %
                     mismatch)

    def testIPython(self):
        """Test the IPython runner."""
        source = """
print 'hello, this is python'

# some more code
x=1;y=2
x+y**2

# An example of autocall functionality
from math import *
autocall 1
cos pi
autocall 0
cos pi
cos(pi)

for i in range(5):
    print i,

print "that's all folks!"

%Exit
"""
        output = """\
In [1]: print 'hello, this is python'
hello, this is python


# some more code
In [2]: x=1;y=2

In [3]: x+y**2
Out[3]: 5


# An example of autocall functionality
In [4]: from math import *

In [5]: autocall 1
Automatic calling is: Smart

In [6]: cos pi
------> cos(pi)
Out[6]: -1.0

In [7]: autocall 0
Automatic calling is: OFF

In [8]: cos pi
------------------------------------------------------------
   File "<ipython console>", line 1
     cos pi
          ^
<type 'exceptions.SyntaxError'>: invalid syntax


In [9]: cos(pi)
Out[9]: -1.0


In [10]: for i in range(5):
   ....:     print i,
   ....:
0 1 2 3 4

In [11]: print "that's all folks!"
that's all folks!


In [12]: %Exit
"""
        runner = irunner.IPythonRunner(out=self.out)
        self._test_runner(runner,source,output)

    def testPython(self):
        """Test the Python runner."""
        runner = irunner.PythonRunner(out=self.out)
        source = """
print 'hello, this is python'

# some more code
x=1;y=2
x+y**2

from math import *
cos(pi)

for i in range(5):
    print i,

print "that's all folks!"
        """
        output = """\
>>> print 'hello, this is python'
hello, this is python

# some more code
>>> x=1;y=2
>>> x+y**2
5

>>> from math import *
>>> cos(pi)
-1.0

>>> for i in range(5):
...     print i,
...
0 1 2 3 4
>>> print "that's all folks!"
that's all folks!
"""
        self._test_runner(runner,source,output)
        
if __name__ == '__main__':
    unittest.main()
