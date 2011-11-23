# encoding: utf-8
"""
A utility for handling the reloading of doctest.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def dhook_wrap(func,*a,**k):
    """Wrap a function call in a sys.displayhook controller.

    Returns a wrapper around func which calls func, with all its arguments and
    keywords unmodified, using the default sys.displayhook.  Since IPython
    modifies sys.displayhook, it breaks the behavior of certain systems that
    rely on the default behavior, notably doctest.
    """

    def f(*a,**k):

        dhook_s = sys.displayhook
        sys.displayhook = sys.__displayhook__
        try:
            out = func(*a,**k)
        finally:
            sys.displayhook = dhook_s

        return out

    f.__doc__ = func.__doc__
    return f


def doctest_reload():
    """Properly reload doctest to reuse it interactively.

    This routine:

      - imports doctest but does NOT reload it (see below).

      - resets its global 'master' attribute to None, so that multiple uses of
      the module interactively don't produce cumulative reports.

      - Monkeypatches its core test runner method to protect it from IPython's
      modified displayhook.  Doctest expects the default displayhook behavior
      deep down, so our modification breaks it completely.  For this reason, a
      hard monkeypatch seems like a reasonable solution rather than asking
      users to manually use a different doctest runner when under IPython.

    Notes
    -----

    This function *used to* reload doctest, but this has been disabled because
    reloading doctest unconditionally can cause massive breakage of other
    doctest-dependent modules already in memory, such as those for IPython's
    own testing system.  The name wasn't changed to avoid breaking people's
    code, but the reload call isn't actually made anymore."""

    import doctest
    doctest.master = None
    doctest.DocTestRunner.run = dhook_wrap(doctest.DocTestRunner.run)

