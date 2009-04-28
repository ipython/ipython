# encoding: utf-8
"""
Testing related decorators for use with twisted.trial.

The decorators in this files are designed to follow the same API as those
in the decorators module (in this same directory).  But they can be used
with twisted.trial
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import sys

from IPython.testing.decorators import make_label_dec

#-----------------------------------------------------------------------------
# Testing decorators
#-----------------------------------------------------------------------------


def skipif(skip_condition, msg=None):
    """Create a decorator that marks a test function for skipping.

    The is a decorator factory that returns a decorator that will 
    conditionally skip a test based on the value of skip_condition.  The
    skip_condition argument can either be a boolean or a callable that returns
    a boolean.

    Parameters
    ----------
    skip_condition : boolean or callable
        If this evaluates to True, the test is skipped.
    msg : str
        The message to print if the test is skipped.

    Returns
    -------
    decorator : function
        The decorator function that can be applied to the test function.
    """

    def skip_decorator(f):

        # Allow for both boolean or callable skip conditions.
        if callable(skip_condition):
            skip_val = lambda : skip_condition()
        else:
            skip_val = lambda : skip_condition

        if msg is None:
            out = 'Test skipped due to test condition.'
        else: 
            out = msg
        final_msg = "Skipping test: %s. %s" % (f.__name__,out)

        if skip_val():
            f.skip = final_msg

        return f
    return skip_decorator


def skip(msg=None):
    """Create a decorator that marks a test function for skipping.

    This is a decorator factory that returns a decorator that will cause
    tests to be skipped.

    Parameters
    ----------
    msg : str
        Optional message to be added.

    Returns
    -------
    decorator : function
        Decorator, which, when applied to a function, sets the skip
        attribute of the function causing `twisted.trial` to skip it.
    """

    return skipif(True,msg)


def numpy_not_available():
    """Can numpy be imported?  Returns true if numpy does NOT import.

    This is used to make a decorator to skip tests that require numpy to be
    available, but delay the 'import numpy' to test execution time.
    """
    try:
        import numpy
        np_not_avail = False
    except ImportError:
        np_not_avail = True

    return np_not_avail

#-----------------------------------------------------------------------------
# Decorators for public use
#-----------------------------------------------------------------------------

# Decorators to skip certain tests on specific platforms.
skip_win32 = skipif(sys.platform == 'win32',
                    "This test does not run under Windows")
skip_linux = skipif(sys.platform == 'linux2',
                    "This test does not run under Linux")
skip_osx = skipif(sys.platform == 'darwin',"This test does not run under OS X")

# Decorators to skip tests if not on specific platforms.
skip_if_not_win32 = skipif(sys.platform != 'win32',
                           "This test only runs under Windows")
skip_if_not_linux = skipif(sys.platform != 'linux2',
                           "This test only runs under Linux")
skip_if_not_osx = skipif(sys.platform != 'darwin',
                         "This test only runs under OSX")

# Other skip decorators
skipif_not_numpy = skipif(numpy_not_available,"This test requires numpy")

skipknownfailure = skip('This test is known to fail')


