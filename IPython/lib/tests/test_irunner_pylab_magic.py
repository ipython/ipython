"""Test suite for pylab_import_all magic
Modified from the irunner module but using regex.
"""

# Global to make tests extra verbose and help debugging
VERBOSE = True

# stdlib imports
import StringIO
import sys
import unittest
import re

# IPython imports
from IPython.lib import irunner
from IPython.testing import decorators

def pylab_not_importable():
    """Test if importing pylab fails. (For example, when having no display)"""
    try:
        import pylab
        return False
    except:
        return True

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
            if not re.match(ol1,ol2):
                mismatch += 1
                if VERBOSE:
                    print '<<< line %s does not match:' % n
                    print repr(ol1)
                    print repr(ol2)
                    print '>>>'
        self.assert_(mismatch==0,'Number of mismatched lines: %s' %
                     mismatch)

    @decorators.skipif_not_matplotlib
    @decorators.skipif(pylab_not_importable, "Likely a run without X.")
    def test_pylab_import_all_enabled(self):
        "Verify that plot is available when pylab_import_all = True"
        source = """
from IPython.config.application import Application
app = Application.instance()
app.pylab_import_all = True
pylab
ip=get_ipython()
'plot' in ip.user_ns
        """
        output = """
In \[1\]: from IPython\.config\.application import Application
In \[2\]: app = Application\.instance\(\)
In \[3\]: app\.pylab_import_all = True
In \[4\]: pylab
^Welcome to pylab, a matplotlib-based Python environment
For more information, type 'help\(pylab\)'\.
In \[5\]: ip=get_ipython\(\)
In \[6\]: \'plot\' in ip\.user_ns
Out\[6\]: True
"""
        runner = irunner.IPythonRunner(out=self.out)
        self._test_runner(runner,source,output)

    @decorators.skipif_not_matplotlib
    @decorators.skipif(pylab_not_importable, "Likely a run without X.")
    def test_pylab_import_all_disabled(self):
        "Verify that plot is not available when pylab_import_all = False"
        source = """
from IPython.config.application import Application
app = Application.instance()
app.pylab_import_all = False
pylab
ip=get_ipython()
'plot' in ip.user_ns
        """
        output = """
In \[1\]: from IPython\.config\.application import Application
In \[2\]: app = Application\.instance\(\)
In \[3\]: app\.pylab_import_all = False
In \[4\]: pylab
^Welcome to pylab, a matplotlib-based Python environment
For more information, type 'help\(pylab\)'\.
In \[5\]: ip=get_ipython\(\)
In \[6\]: \'plot\' in ip\.user_ns
Out\[6\]: False
"""
        runner = irunner.IPythonRunner(out=self.out)
        self._test_runner(runner,source,output)
