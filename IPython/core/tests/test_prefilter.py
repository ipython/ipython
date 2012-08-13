"""Tests for input manipulation machinery."""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import nose.tools as nt

from IPython.core.prefilter import AutocallChecker
from IPython.testing import tools as tt, decorators as dec
from IPython.testing.globalipapp import get_ipython

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------
ip = get_ipython()

@dec.parametric
def test_prefilter():
    """Test user input conversions"""

    # pairs of (raw, expected correct) input
    pairs = [ ('2+2','2+2'),
             ]

    for raw, correct in pairs:
        yield nt.assert_equal(ip.prefilter(raw), correct)


@dec.parametric
def test_autocall_binops():
    """See https://github.com/ipython/ipython/issues/81"""
    ip.magic('autocall 2')
    f = lambda x: x
    ip.user_ns['f'] = f
    try:
        yield nt.assert_equal(ip.prefilter('f 1'),'f(1)')
        for t in ['f +1', 'f -1']:
            yield nt.assert_equal(ip.prefilter(t), t)

        # Run tests again with a more permissive exclude_regexp, which will
        # allow transformation of binary operations ('f -1' -> 'f(-1)').
        pm = ip.prefilter_manager
        ac = AutocallChecker(shell=pm.shell, prefilter_manager=pm,
                             config=pm.config)
        try:
            ac.priority = 1
            ac.exclude_regexp = r'^[,&^\|\*/]|^is |^not |^in |^and |^or '
            pm.sort_checkers()

            yield nt.assert_equal(ip.prefilter('f -1'), 'f(-1)')
            yield nt.assert_equal(ip.prefilter('f +1'), 'f(+1)')
        finally:
            pm.unregister_checker(ac)
    finally:
        ip.magic('autocall 0')
        del ip.user_ns['f']


@dec.parametric
def test_issue_114():
    """Check that multiline string literals don't expand as magic
    see http://github.com/ipython/ipython/issues/114"""

    template = '"""\n%s\n"""'
    # Store the current value of multi_line_specials and turn it off before
    # running test, since it could be true (case in which the test doesn't make
    # sense, as multiline string literals *will* expand as magic in that case).
    msp = ip.prefilter_manager.multi_line_specials
    ip.prefilter_manager.multi_line_specials = False
    try:
        for mgk in ip.magics_manager.lsmagic()['line']:
            raw = template % mgk
            yield nt.assert_equal(ip.prefilter(raw), raw)
    finally:
        ip.prefilter_manager.multi_line_specials = msp


def test_prefilter_attribute_errors():
    """Capture exceptions thrown by user objects on attribute access.

    See http://github.com/ipython/ipython/issues/988."""

    class X(object):
        def __getattr__(self, k):
            raise ValueError('broken object')
        def __call__(self, x):
            return x

    # Create a callable broken object
    ip.user_ns['x'] = X()
    ip.magic('autocall 2')
    try:
        # Even if x throws an attribute error when looking at its rewrite
        # attribute, we should not crash.  So the test here is simply making
        # the prefilter call and not having an exception.
        ip.prefilter('x 1')
    finally:
        del ip.user_ns['x']
        ip.magic('autocall 0')
