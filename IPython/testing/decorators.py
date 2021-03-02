# -*- coding: utf-8 -*-
"""Decorators for labeling test objects.

Decorators that merely return a modified version of the original function
object are straightforward.  Decorators that return a new function object need
to use nose.tools.make_decorator(original_function)(decorator) in returning the
decorator, in order to preserve metadata such as function name, setup and
teardown functions and so on - see nose.tools for more information.

This module provides a set of useful decorators meant to be ready to use in
your own tests.  See the bottom of the file for the ready-made ones, and if you
find yourself writing a new one that may be of generic use, add it here.

Included decorators:


Lightweight testing that remains unittest-compatible.

- An @as_unittest decorator can be used to tag any normal parameter-less
  function as a unittest TestCase.  Then, both nose and normal unittest will
  recognize it as such.  This will make it easier to migrate away from Nose if
  we ever need/want to while maintaining very lightweight tests.

NOTE: This file contains IPython-specific decorators. Using the machinery in
IPython.external.decorators, we import either numpy.testing.decorators if numpy is
available, OR use equivalent code in IPython.external._decorators, which
we've copied verbatim from numpy.

"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import shutil
import sys
import tempfile
import unittest
import warnings
from importlib import import_module

from decorator import decorator

# Expose the unittest-driven decorators
from .ipunittest import ipdoctest, ipdocstring

# Grab the numpy-specific decorators which we keep in a file that we
# occasionally update from upstream: decorators.py is a copy of
# numpy.testing.decorators, we expose all of it here.
import pytest

knownfailureif = pytest.mark.xfail

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

# Simple example of the basic idea
def as_unittest(func):
    """Decorator to make a simple function into a normal test via unittest."""
    class Tester(unittest.TestCase):
        def test(self):
            func()

    Tester.__name__ = func.__name__

    return Tester


# Utility functions
def make_label_dec(label, ds=None):
    """Factory function to create a decorator that applies one or more labels.

    Parameters
    ----------
      label : string or sequence
      One or more labels that will be applied by the decorator to the functions
    it decorates.  Labels are attributes of the decorated function with their
    value set to True.

      ds : string
      An optional docstring for the resulting decorator.  If not given, a
      default docstring is auto-generated.

    Returns
    -------
      A decorator.

    Examples
    --------

    A simple labeling decorator:

    >>> slow = make_label_dec('slow')
    >>> slow.__doc__
    "Labels a test as 'slow'."

    And one that uses multiple labels and a custom docstring:

    >>> rare = make_label_dec(['slow','hard'],
    ... "Mix labels 'slow' and 'hard' for rare tests.")
    >>> rare.__doc__
    "Mix labels 'slow' and 'hard' for rare tests."

    Now, let's test using this one:
    >>> @rare
    ... def f(): pass
    ...
    >>>
    >>> f.slow
    True
    >>> f.hard
    True
    """

    warnings.warn("The function `make_label_dec` is deprecated since IPython 4.0",
            DeprecationWarning, stacklevel=2)
    if isinstance(label, str):
        labels = [label]
    else:
        labels = label

    # Validate that the given label(s) are OK for use in setattr() by doing a
    # dry run on a dummy function.
    tmp = lambda : None
    for label in labels:
        setattr(tmp,label,True)

    # This is the actual decorator we'll return
    def decor(f):
        for label in labels:
            setattr(f,label,True)
        return f

    # Apply the user's docstring, or autogenerate a basic one
    if ds is None:
        ds = "Labels a test as %r." % label
    decor.__doc__ = ds

    return decor


# Inspired by numpy's skipif, but uses the full apply_wrapper utility to
# preserve function metadata better and allows the skip condition to be a
# callable.
skipif = unittest.skipIf
skip = unittest.skip
onlyif = unittest.skipIf

#-----------------------------------------------------------------------------
# Utility functions for decorators
def module_not_available(module):
    """Can module be imported?  Returns true if module does NOT import.

    This is used to make a decorator to skip tests that require module to be
    available, but delay the 'import numpy' to test execution time.
    """
    try:
        mod = import_module(module)
        mod_not_avail = False
    except ImportError:
        mod_not_avail = True

    return mod_not_avail


def decorated_dummy(dec, name):
    """Return a dummy function decorated with dec, with the given name.

    Examples
    --------
    import IPython.testing.decorators as dec
    setup = dec.decorated_dummy(dec.skip_if_no_x11, __name__)
    """
    warnings.warn("The function `decorated_dummy` is deprecated since IPython 4.0",
        DeprecationWarning, stacklevel=2)
    dummy = lambda: None
    dummy.__name__ = name
    return dec(dummy)

#-----------------------------------------------------------------------------
# Decorators for public use

# Decorators to skip certain tests on specific platforms.
skip_win32 = skipif(sys.platform == 'win32',
                    "This test does not run under Windows")
skip_linux = skipif(sys.platform.startswith('linux'),
                    "This test does not run under Linux")
skip_osx = skipif(sys.platform == 'darwin',"This test does not run under OS X")


# Decorators to skip tests if not on specific platforms.
skip_if_not_win32 = skipif(sys.platform != 'win32',
                           "This test only runs under Windows")
skip_if_not_linux = skipif(not sys.platform.startswith('linux'),
                           "This test only runs under Linux")
skip_if_not_osx = skipif(sys.platform != 'darwin',
                         "This test only runs under OSX")


_x11_skip_cond = (sys.platform not in ('darwin', 'win32') and
                  os.environ.get('DISPLAY', '') == '')
_x11_skip_msg = "Skipped under *nix when X11/XOrg not available"

skip_if_no_x11 = skipif(_x11_skip_cond, _x11_skip_msg)


# Decorators to skip certain tests on specific platform/python combinations
skip_win32_py38 = skipif(sys.version_info > (3,8) and os.name == 'nt',
                         "This test does not run on Windows with Python > 3.8")


# not a decorator itself, returns a dummy function to be used as setup
def skip_file_no_x11(name):
    warnings.warn("The function `skip_file_no_x11` is deprecated since IPython 4.0",
            DeprecationWarning, stacklevel=2)
    return decorated_dummy(skip_if_no_x11, name) if _x11_skip_cond else None

# Other skip decorators

# generic skip without module
skip_without = lambda mod: skipif(module_not_available(mod), "This test requires %s" % mod)

skipif_not_numpy = skip_without('numpy')

skipif_not_matplotlib = skip_without('matplotlib')

skipif_not_sympy = skip_without('sympy')

skip_known_failure = pytest.mark.xfail(True, reason='This test is known to fail')

# A null 'decorator', useful to make more readable code that needs to pick
# between different decorators based on OS or other conditions
null_deco = lambda f: f

# Some tests only run where we can use unicode paths. Note that we can't just
# check os.path.supports_unicode_filenames, which is always False on Linux.
try:
    f = tempfile.NamedTemporaryFile(prefix=u"tmp€")
except UnicodeEncodeError:
    unicode_paths = False
else:
    unicode_paths = True
    f.close()

onlyif_unicode_paths = onlyif(unicode_paths, ("This test is only applicable "
                                              "where we can use unicode in filenames."))


def onlyif_cmds_exist(*commands):
    """
    Decorator to skip test when at least one of `commands` is not found.
    """
    for cmd in commands:
        if not shutil.which(cmd):
            return skip("This test runs only if command '{0}' "
                        "is installed".format(cmd))
    return null_deco

def onlyif_any_cmd_exists(*commands):
    """
    Decorator to skip test unless at least one of `commands` is found.
    """
    warnings.warn("The function `onlyif_any_cmd_exists` is deprecated since IPython 4.0",
            DeprecationWarning, stacklevel=2)
    for cmd in commands:
        if shutil.which(cmd):
            return null_deco
    return skip("This test runs only if one of the commands {0} "
                "is installed".format(commands))
