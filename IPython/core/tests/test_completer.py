"""Tests for the IPython tab-completion machinery.
"""
#-----------------------------------------------------------------------------
# Module imports
#-----------------------------------------------------------------------------

# stdlib
import sys

# third party
import nose.tools as nt

# our own packages
from IPython.core import completer

#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------
def test_protect_filename():
    pairs = [ ('abc','abc'),
              (' abc',r'\ abc'),
              ('a bc',r'a\ bc'),
              ('a  bc',r'a\ \ bc'),
              ('  bc',r'\ \ bc'),
              ]
    # On posix, we also protect parens
    if sys.platform != 'win32':
        pairs.extend( [('a(bc',r'a\(bc'),
                       ('a)bc',r'a\)bc'),
                       ('a( )bc',r'a\(\ \)bc'),
                       ] )
    # run the actual tests
    for s1, s2 in pairs:
        s1p = completer.protect_filename(s1)
        nt.assert_equals(s1p, s2)
