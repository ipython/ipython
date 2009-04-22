# -*- coding: utf-8 -*-
"""IPython Test Suite Runner.

This module provides a main entry point to a user script to test IPython itself
from the command line.  The main() routine can be used in a similar manner to
the ``nosetests`` script, and it takes similar arguments, but if no arguments
are given it defaults to testing all of IPython.  This should be preferred to
using plain ``nosetests`` because a number of nose plugins necessary to test
IPython correctly are automatically configured by this code.
"""

#-----------------------------------------------------------------------------
# Module imports
#-----------------------------------------------------------------------------

# stdlib
import sys
import warnings

# third-party
import nose.plugins.builtin
from nose.core import TestProgram

# Our own imports
from IPython.testing.plugin.ipdoctest import IPythonDoctest

#-----------------------------------------------------------------------------
# Constants and globals
#-----------------------------------------------------------------------------

# For the IPythonDoctest plugin, we need to exclude certain patterns that cause
# testing problems.  We should strive to minimize the number of skipped
# modules, since this means untested code.  As the testing machinery
# solidifies, this list should eventually become empty.
EXCLUDE = ['IPython/external/',
           'IPython/platutils_win32',
           'IPython/frontend/cocoa',
           'IPython/frontend/process/winprocess.py',
           'IPython_doctest_plugin',
           'IPython/Gnuplot',
           'IPython/Extensions/ipy_',
           'IPython/Extensions/clearcmd',
           'IPython/Extensions/PhysicalQIn',
           'IPython/Extensions/scitedirector',
           'IPython/Extensions/numeric_formats',
           'IPython/testing/attic',
           ]

#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------

def main():
    """Run the IPython test suite.
    """

    warnings.filterwarnings('ignore', 
        'This will be removed soon.  Use IPython.testing.util instead')

    argv = sys.argv + [ 
                        # Loading ipdoctest causes problems with Twisted.
                        # I am removing this as a temporary fix to get the 
                        # test suite back into working shape.  Our nose
                        # plugin needs to be gone through with a fine
                        # toothed comb to find what is causing the problem.
                        # '--with-ipdoctest',
                        '--ipdoctest-tests','--ipdoctest-extension=txt',
                        '--detailed-errors',
                       
                        # We add --exe because of setuptools' imbecility (it
                        # blindly does chmod +x on ALL files).  Nose does the
                        # right thing and it tries to avoid executables,
                        # setuptools unfortunately forces our hand here.  This
                        # has been discussed on the distutils list and the
                        # setuptools devs refuse to fix this problem!
                        '--exe',
                        ]

    # Detect if any tests were required by explicitly calling an IPython
    # submodule or giving a specific path
    has_tests = False
    for arg in sys.argv:
        if 'IPython' in arg or arg.endswith('.py') or \
           (':' in arg and  '.py' in arg):
            has_tests = True
            break
        
    # If nothing was specifically requested, test full IPython
    if not has_tests:
        argv.append('IPython')

    # Construct list of plugins, omitting the existing doctest plugin, which
    # ours replaces (and extends).
    plugins = [IPythonDoctest(EXCLUDE)]
    for p in nose.plugins.builtin.plugins:
        plug = p()
        if plug.name == 'doctest':
            continue

        #print '*** adding plugin:',plug.name  # dbg
        plugins.append(plug)

    TestProgram(argv=argv,plugins=plugins)
