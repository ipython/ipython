#!/usr/bin/env python
"""Testing script for the tools.utils module.
"""

# Module imports
from IPython.testing import tcommon
from IPython.testing.tcommon import *

# If you have standalone doctests in a separate file, set their names in the
# dt_files variable (as a single string  or a list thereof).  The mkPath call
# forms an absolute path based on the current file, it is not needed if you
# provide the full pahts.
dt_files = fullPath(__file__,['tst_tools_utils_doctest.txt',
                              'tst_tools_utils_doctest2.txt'])

# If you have any modules whose docstrings should be scanned for embedded tests
# as examples accorging to standard doctest practice, set them here (as a
# single string or a list thereof):
dt_modules = 'IPython.tools.utils'

##########################################################################
### Regular unittest test classes go here

## class utilsTestCase(unittest.TestCase):
##     def test_foo(self):
##         pass
        
##########################################################################
### Main
# This ensures that the code will run either standalone as a script, or that it
# can be picked up by Twisted's `trial` test wrapper to run all the tests.
if tcommon.pexpect is not None:
    if __name__ == '__main__':
        unittest.main(testLoader=IPDocTestLoader(dt_files,dt_modules))
    else:
        testSuite = lambda : makeTestSuite(__name__,dt_files,dt_modules)
