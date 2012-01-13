"""Test suite for the irunner module.

Not the most elegant or fine-grained, but it does cover at least the bulk
functionality."""

# Global to make tests extra verbose and help debugging
VERBOSE = True

# stdlib imports
import StringIO
import sys
import unittest

# IPython imports
from IPython.lib import irunner
from IPython.utils.py3compat import doctest_refactor_print

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
        # banner.  clean it up for comparison, removing lines of whitespace
        output_l = [l for l in output.splitlines() if l and not l.isspace()]
        out_l = [l for l in out.splitlines() if l and not l.isspace()]
        mismatch  = 0
        if len(output_l) != len(out_l):
            message = ("Mismatch in number of lines\n\n"
                       "Expected:\n"
                       "~~~~~~~~~\n"
                       "%s\n\n"
                       "Got:\n"
                       "~~~~~~~~~\n"
                       "%s"
                       ) % ("\n".join(output_l), "\n".join(out_l))
            self.fail(message)
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
        source = doctest_refactor_print("""
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
    print i

print "that's all folks!"

exit
""")
        output = doctest_refactor_print("""\
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
   File "<ipython-input-8-6bd7313dd9a9>", line 1
     cos pi
          ^
SyntaxError: invalid syntax


In [9]: cos(pi)
Out[9]: -1.0


In [10]: for i in range(5):
   ....:     print i
   ....:
0
1
2
3
4

In [11]: print "that's all folks!"
that's all folks!


In [12]: exit
""")
        runner = irunner.IPythonRunner(out=self.out)
        self._test_runner(runner,source,output)

    def testPython(self):
        """Test the Python runner."""
        runner = irunner.PythonRunner(out=self.out)
        source = doctest_refactor_print("""
print 'hello, this is python'

# some more code
x=1;y=2
x+y**2

from math import *
cos(pi)

for i in range(5):
    print i

print "that's all folks!"
        """)
        output = doctest_refactor_print("""\
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
...     print i
...
0
1
2
3
4
>>> print "that's all folks!"
that's all folks!
""")
        self._test_runner(runner,source,output)
