"""DEPRECATED - use IPython.testing.util instead.

Utilities for testing code.
"""

#############################################################################

# This was old testing code we never really used in IPython.  The pieces of
# testing machinery from snakeoil that were good have already been merged into
# the nose plugin, so this can be taken away soon.  Leave a warning for now,
# we'll remove it in a later release (around 0.10 or so).

from warnings import warn
warn('This will be removed soon.  Use IPython.testing.util instead',
     DeprecationWarning)

#############################################################################

# Required modules and packages

# Standard Python lib
import os
import sys

# From this project
from IPython.tools import utils

# path to our own installation, so we can find source files under this.
TEST_PATH = os.path.dirname(os.path.abspath(__file__))

# Global flag, used by vprint
VERBOSE = '-v' in sys.argv or '--verbose' in sys.argv

##########################################################################
# Code begins

# Some utility functions
def vprint(*args):
    """Print-like function which relies on a global VERBOSE flag."""
    if not VERBOSE:
        return

    write = sys.stdout.write
    for item in args:
        write(str(item))
    write('\n')
    sys.stdout.flush()

def test_path(path):
    """Return a path as a subdir of the test package.

    This finds the correct path of the test package on disk, and prepends it
    to the input path."""

    return os.path.join(TEST_PATH,path)

def fullPath(startPath,files):
    """Make full paths for all the listed files, based on startPath.

    Only the base part of startPath is kept, since this routine is typically
    used with a script's __file__ variable as startPath.  The base of startPath
    is then prepended to all the listed files, forming the output list.

    :Parameters:
      startPath : string
        Initial path to use as the base for the results.  This path is split
      using os.path.split() and only its first component is kept.

      files : string or list
        One or more files.

    :Examples:

    >>> fullPath('/foo/bar.py',['a.txt','b.txt'])
    ['/foo/a.txt', '/foo/b.txt']

    >>> fullPath('/foo',['a.txt','b.txt'])
    ['/a.txt', '/b.txt']

    If a single file is given, the output is still a list:
    >>> fullPath('/foo','a.txt')
    ['/a.txt']
    """

    files = utils.list_strings(files)
    base = os.path.split(startPath)[0]
    return [ os.path.join(base,f) for f in files ]
