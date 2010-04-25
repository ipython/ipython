"""Tests for input manipulation machinery."""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import nose.tools as nt

from IPython.testing import tools as tt, decorators as dec

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------
ip = get_ipython()

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

    for raw, correct in pairs:
        yield nt.assert_equals(ip.prefilter(raw), correct)


@dec.parametric
def test_autocall_binops():
    """See https://bugs.launchpad.net/ipython/+bug/315706"""
    ip.magic('autocall 2')
    f = lambda x: x
    ip.user_ns['f'] = f
    try:
        yield nt.assert_equals(ip.prefilter('f 1'),'f(1)')
        for t in ['f +1', 'f -1']:
            yield nt.assert_equals(ip.prefilter(t), t)
    finally:
        ip.magic('autocall 0')
        del ip.user_ns['f']
        
