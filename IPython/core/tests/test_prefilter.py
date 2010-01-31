"""Tests for input manipulation machinery."""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import nose.tools as nt

from IPython.testing import tools as tt, decorators as dec

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------
@dec.parametric
def test_prefilter():
    """Test user input conversions"""

    # pairs of (raw, expected correct) input
    pairs = [ ('2+2','2+2'),
              ('>>> 2+2','2+2'),
              ('>>> # This is a comment\n'
               '... 2+2',
               '# This is a comment\n'
               '2+2'),
              # Some IPython input
              ('In [1]: 1', '1'),
              ('In [2]: for i in range(5):\n'
               '   ...:     print i,',
               'for i in range(5):\n'
               '    print i,'),
             ]

    ip = get_ipython()
    for raw, correct in pairs:
        yield nt.assert_equals(ip.prefilter(raw), correct)
