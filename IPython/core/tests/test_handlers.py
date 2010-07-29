"""Tests for input handlers.
"""
#-----------------------------------------------------------------------------
# Module imports
#-----------------------------------------------------------------------------

# third party
import nose.tools as nt

# our own packages
from IPython.core import autocall
from IPython.testing import decorators as dec
from IPython.testing.globalipapp import get_ipython

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
    for pre, post in tests:
        global num_tests
        num_tests += 1        
        ip.runlines(pre)
        ip.runlines('_i')  # Not sure why I need this...
        actual = ip.user_ns['_i']
        if actual != None:
            actual = actual.rstrip('\n')
        if actual != post:
            failures.append('Expected %r to become %r, found %r' % (
                pre, post, actual))


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
    run([("an_alias",    'get_ipython().system("true ")'),     # alias
         # Below: recursive aliases should expand whitespace-surrounded
         # chars, *not* initial chars which happen to be aliases:
         ("top",         'get_ipython().system("d:/cygwin/top ")'),
         ])
    ip.system = old_system_cmd

    call_idx = CallableIndexable()
    ip.user_ns['call_idx'] = call_idx

    # For many of the below, we're also checking that leading whitespace
    # turns off the esc char, which it should unless there is a continuation
    # line.
    run([('"no change"', '"no change"'),             # normal
         ("!true",       'get_ipython().system("true")'),      # shell_escapes
         ("!! true",     'get_ipython().magic("sx  true")'),   # shell_escapes + magic
         ("!!true",      'get_ipython().magic("sx true")'),    # shell_escapes + magic
         ("%lsmagic",    'get_ipython().magic("lsmagic ")'),   # magic
         ("lsmagic",     'get_ipython().magic("lsmagic ")'),   # magic
         #("a = b # PYTHON-MODE", '_i'),          # emacs -- avoids _in cache

         # post-esc-char whitespace goes inside
         ("! true",   'get_ipython().system(" true")'),  

         # handle_help

         # These are weak tests -- just looking at what the help handlers
         # logs, which is not how it really does its work.  But it still
         # lets us check the key paths through the handler.

         ("x=1 # what?", "x=1 # what?"), # no help if valid python
         ])

    # multi_line_specials
    ip.prefilter_manager.multi_line_specials = False
    # W/ multi_line_specials off, leading ws kills esc chars/autoexpansion
    run([
        ('if 1:\n    !true',    'if 1:\n    !true'),
        ('if 1:\n    lsmagic',  'if 1:\n    lsmagic'),
        ('if 1:\n    an_alias', 'if 1:\n    an_alias'),
        ])

    ip.prefilter_manager.multi_line_specials = True
    # initial indents must be preserved.
    run([
         ('if 1:\n    !true',    'if 1:\n    get_ipython().system("true")'),
         ('if 2:\n    lsmagic',  'if 2:\n    get_ipython().magic("lsmagic ")'),
         ('if 1:\n    an_alias', 'if 1:\n    get_ipython().system("true ")'),
         # Weird one
         ('if 1:\n    !!true',   'if 1:\n    get_ipython().magic("sx true")'),

         # Even with m_l_s on, autocall is off even with special chars
         ('if 1:\n    /fun 1 2', 'if 1:\n    /fun 1 2'), 
         ('if 1:\n    ;fun 1 2', 'if 1:\n    ;fun 1 2'),
         ('if 1:\n    ,fun 1 2', 'if 1:\n    ,fun 1 2'),
         ('if 1:\n    ?fun 1 2', 'if 1:\n    ?fun 1 2'),
         # What about !!  
         ])

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
        (",list 1 2 3",     'list("1", "2", "3")'),
        (";list 1 2 3",     'list("1 2 3")'),      
        ("/len range(1,4)", 'len(range(1,4))'),
        ])
    ip.magic('autocall 1')
    run([
        (",list 1 2 3", 'list("1", "2", "3")'),
        (";list 1 2 3", 'list("1 2 3")'),      
        ("/len range(1,4)", 'len(range(1,4))'),
        ('len "abc"', 'len("abc")'),
        ('len "abc";', 'len("abc");'),  # ; is special -- moves out of parens
        # Autocall is turned off if first arg is [] and the object
        # is both callable and indexable.  Like so:
        ('len [1,2]', 'len([1,2])'),      # len doesn't support __getitem__...
        ('call_idx [1]', 'call_idx [1]'), # call_idx *does*..
        ('call_idx 1', 'call_idx(1)'),
        ('len', 'len '), # only at 2 does it auto-call on single args
        ])
    ip.magic('autocall 2')
    run([
        (",list 1 2 3", 'list("1", "2", "3")'),
        (";list 1 2 3", 'list("1 2 3")'),      
        ("/len range(1,4)", 'len(range(1,4))'),
        ('len "abc"', 'len("abc")'),
        ('len "abc";', 'len("abc");'),
        ('len [1,2]', 'len([1,2])'),   
        ('call_idx [1]', 'call_idx [1]'),
        ('call_idx 1', 'call_idx(1)'),
        # This is what's different:
        ('len', 'len()'), # only at 2 does it auto-call on single args
        ])
    ip.magic('autocall 1')

    nt.assert_equals(failures, [])
