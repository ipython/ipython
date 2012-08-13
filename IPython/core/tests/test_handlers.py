"""Tests for input handlers.
"""
#-----------------------------------------------------------------------------
# Module imports
#-----------------------------------------------------------------------------

# third party
import nose.tools as nt

# our own packages
from IPython.core import autocall
from IPython.testing import tools as tt
from IPython.testing.globalipapp import get_ipython
from IPython.utils import py3compat

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

# Get the public instance of IPython
ip = get_ipython()

failures = []
num_tests = 0

#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------

class CallableIndexable(object):
    def __getitem__(self, idx): return True
    def __call__(self, *args, **kws): return True


class Autocallable(autocall.IPyAutocall):
    def __call__(self):
        return "called"


def run(tests):
    """Loop through a list of (pre, post) inputs, where pre is the string
    handed to ipython, and post is how that string looks after it's been
    transformed (i.e. ipython's notion of _i)"""
    tt.check_pairs(ip.prefilter_manager.prefilter_lines, tests)


def test_handlers():
    # alias expansion

    # We're using 'true' as our syscall of choice because it doesn't
    # write anything to stdout.

    # Turn off actual execution of aliases, because it's noisy
    old_system_cmd = ip.system
    ip.system = lambda cmd: None


    ip.alias_manager.alias_table['an_alias'] = (0, 'true')
    # These are useful for checking a particular recursive alias issue
    ip.alias_manager.alias_table['top'] = (0, 'd:/cygwin/top')
    ip.alias_manager.alias_table['d'] =   (0, 'true')
    run([(i,py3compat.u_format(o)) for i,o in \
        [("an_alias",    "get_ipython().system({u}'true ')"),     # alias
         # Below: recursive aliases should expand whitespace-surrounded
         # chars, *not* initial chars which happen to be aliases:
         ("top",         "get_ipython().system({u}'d:/cygwin/top ')"),
         ]])
    ip.system = old_system_cmd

    call_idx = CallableIndexable()
    ip.user_ns['call_idx'] = call_idx

    # For many of the below, we're also checking that leading whitespace
    # turns off the esc char, which it should unless there is a continuation
    # line.
    run([(i,py3compat.u_format(o)) for i,o in \
        [('"no change"', '"no change"'),             # normal
         (u"lsmagic",     "get_ipython().magic({u}'lsmagic ')"),   # magic
         #("a = b # PYTHON-MODE", '_i'),          # emacs -- avoids _in cache
         ]])

    # Objects which are instances of IPyAutocall are *always* autocalled
    autocallable = Autocallable()
    ip.user_ns['autocallable'] = autocallable

    # auto
    ip.magic('autocall 0')
    # Only explicit escapes or instances of IPyAutocallable should get
    # expanded
    run([
        ('len "abc"',       'len "abc"'),
        ('autocallable',    'autocallable()'),
        # Don't add extra brackets (gh-1117)
        ('autocallable()',    'autocallable()'),
        ])
    ip.magic('autocall 1')
    run([
        ('len "abc"', 'len("abc")'),
        ('len "abc";', 'len("abc");'),  # ; is special -- moves out of parens
        # Autocall is turned off if first arg is [] and the object
        # is both callable and indexable.  Like so:
        ('len [1,2]', 'len([1,2])'),      # len doesn't support __getitem__...
        ('call_idx [1]', 'call_idx [1]'), # call_idx *does*..
        ('call_idx 1', 'call_idx(1)'),
        ('len', 'len'), # only at 2 does it auto-call on single args
        ])
    ip.magic('autocall 2')
    run([
        ('len "abc"', 'len("abc")'),
        ('len "abc";', 'len("abc");'),
        ('len [1,2]', 'len([1,2])'),
        ('call_idx [1]', 'call_idx [1]'),
        ('call_idx 1', 'call_idx(1)'),
        # This is what's different:
        ('len', 'len()'), # only at 2 does it auto-call on single args
        ])
    ip.magic('autocall 1')

    nt.assert_equal(failures, [])
