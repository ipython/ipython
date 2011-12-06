"""Tests for kernel utility functions

Authors
-------
* MinRK
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2011, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Stdlib imports
from unittest import TestCase

# Third-party imports
import nose.tools as nt

# Our own imports
from IPython.testing import decorators as dec
from IPython.lib import kernel

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

@dec.parametric
def test_swallow_argv():
    tests = [
        # expected  , argv       , aliases, flags
        (['-a', '5'], ['-a', '5'], None, None),
        (['5'], ['-a', '5'], None, ['a']),
        ([], ['-a', '5'], ['a'], None),
        ([], ['-a', '5'], ['a'], ['a']),
        ([], ['--foo'], None, ['foo']),
        (['--foo'], ['--foo'], ['foobar'], []),
        ([], ['--foo', '5'], ['foo'], []),
        ([], ['--foo=5'], ['foo'], []),
        (['--foo=5'], ['--foo=5'], [], ['foo']),
        (['5'], ['--foo', '5'], [], ['foo']),
        (['bar'], ['--foo', '5', 'bar'], ['foo'], ['foo']),
        (['bar'], ['--foo=5', 'bar'], ['foo'], ['foo']),
        (['5','bar'], ['--foo', '5', 'bar'], None, ['foo']),
        (['bar'], ['--foo', '5', 'bar'], ['foo'], None),
        (['bar'], ['--foo=5', 'bar'], ['foo'], None),
    ]
    for expected, argv, aliases, flags in tests:
        stripped = kernel.swallow_argv(argv, aliases=aliases, flags=flags)
        message = '\n'.join(['',
            "argv: %r" % argv,
            "aliases: %r" % aliases,
            "flags : %r" % flags,
            "expected : %r" % expected,
            "returned : %r" % stripped,
        ])
        yield nt.assert_equal(expected, stripped, message)

