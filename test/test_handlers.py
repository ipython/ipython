"""Test the various handlers which do the actual rewriting of the line."""

from StringIO import StringIO
import sys
sys.path.append('..')

failures = []
num_tests = 0

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


# Shutdown stdout/stderr so that ipython isn't noisy during tests.  Have to
# do this *before* importing IPython below.
#
# NOTE: this means that, if you stick print statements into code as part of
# debugging, you won't see the results (unless you comment out some of the
# below).  I keep on doing this, so apparently it's easy.  Or I am an idiot.
old_stdout = sys.stdout
old_stderr = sys.stderr

sys.stdout = StringIO()
sys.stderr = StringIO()

import IPython
import IPython.ipapi

IPython.Shell.start()
ip = IPython.ipapi.get()

class CallableIndexable(object):
    def __getitem__(self, idx): return True
    def __call__(self, *args, **kws): return True

    
try:
    # alias expansion
    
    # We're using 'true' as our syscall of choice because it doesn't
    # write anything to stdout.

    # Turn off actual execution of aliases, because it's noisy
    old_system_cmd = ip.system
    ip.system = lambda cmd: None
    
    
    ip.IP.alias_table['an_alias'] = (0, 'true')
    # These are useful for checking a particular recursive alias issue
    ip.IP.alias_table['top'] = (0, 'd:/cygwin/top')
    ip.IP.alias_table['d'] =   (0, 'true')
    run([("an_alias",    '_ip.system("true ")'),     # alias
         # Below: recursive aliases should expand whitespace-surrounded
         # chars, *not* initial chars which happen to be aliases:
         ("top",         '_ip.system("d:/cygwin/top ")'),
         ])
    ip.system = old_system_cmd


    call_idx = CallableIndexable()
    ip.to_user_ns('call_idx')

    # For many of the below, we're also checking that leading whitespace
    # turns off the esc char, which it should unless there is a continuation
    # line.
    run([('"no change"', '"no change"'),             # normal
         ("!true",       '_ip.system("true")'),      # shell_escapes
         ("!! true",     '_ip.magic("sx  true")'),   # shell_escapes + magic
         ("!!true",      '_ip.magic("sx true")'),    # shell_escapes + magic
         ("%lsmagic",    '_ip.magic("lsmagic ")'),   # magic
         ("lsmagic",     '_ip.magic("lsmagic ")'),   # magic
         ("a = b # PYTHON-MODE", '_i'),          # emacs -- avoids _in cache

         # post-esc-char whitespace goes inside
         ("! true",   '_ip.system(" true")'),  

         # Leading whitespace generally turns off escape characters
         (" ! true",     ' ! true'),  
         (" !true",      ' !true'),  

         # handle_help

         # These are weak tests -- just looking at what the help handlers
         # logs, which is not how it really does its work.  But it still
         # lets us check the key paths through the handler.
        
         ("x=1 # what?", "x=1 # what?"), # no help if valid python
         ("len?",  "#?len"),             # this is what help logs when it runs
         ("len??", "#?len?"),                           
         ("?len",  "#?len"),                            
         ])

    # multi_line_specials
    ip.options.multi_line_specials = 0
    # W/ multi_line_specials off, leading ws kills esc chars/autoexpansion
    run([
        ('if 1:\n    !true',    'if 1:\n    !true'),
        ('if 1:\n    lsmagic',  'if 1:\n    lsmagic'),
        ('if 1:\n    an_alias', 'if 1:\n    an_alias'),
        ])

    ip.options.multi_line_specials = 1
    # initial indents must be preserved.
    run([
         ('if 1:\n    !true',    'if 1:\n    _ip.system("true")'),
         ('if 1:\n    lsmagic',  'if 1:\n    _ip.magic("lsmagic ")'),
         ('if 1:\n    an_alias', 'if 1:\n    _ip.system("true ")'),
         # Weird one
         ('if 1:\n    !!true',   'if 1:\n    _ip.magic("sx true")'),
         

         # Even with m_l_s on, all esc_chars except ! are off
         ('if 1:\n    %lsmagic', 'if 1:\n    %lsmagic'),
         ('if 1:\n    /fun 1 2', 'if 1:\n    /fun 1 2'), 
         ('if 1:\n    ;fun 1 2', 'if 1:\n    ;fun 1 2'),
         ('if 1:\n    ,fun 1 2', 'if 1:\n    ,fun 1 2'),
         ('if 1:\n    ?fun 1 2', 'if 1:\n    ?fun 1 2'),
         # What about !!  
         ])

         
    # Objects which are instances of IPyAutocall are *always* autocalled
    import IPython.ipapi
    class Autocallable(IPython.ipapi.IPyAutocall):
        def __call__(self):
            return "called"
    
    autocallable = Autocallable()
    ip.to_user_ns('autocallable')

    # auto 
    ip.options.autocall = 0
    # Only explicit escapes or instances of IPyAutocallable should get
    # expanded
    run([
        ('len "abc"',       'len "abc"'),        
        ('autocallable',    'autocallable()'),     
        (",list 1 2 3",     'list("1", "2", "3")'),
        (";list 1 2 3",     'list("1 2 3")'),      
        ("/len range(1,4)", 'len(range(1,4))'),
        ])
    ip.options.autocall = 1
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

    ip.options.autocall = 2
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
    ip.options.autocall = 1

    # Ignoring handle_emacs, 'cause it doesn't do anything.
finally:
    sys.stdout = old_stdout
    sys.stderr = old_stderr




num_f = len(failures)
#if verbose:
#    print


print "%s tests run, %s failure%s" % (num_tests,
                                      num_f,
                                      num_f != 1 and "s" or "")
for f in failures:
    print f
