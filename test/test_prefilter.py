"""
Test which prefilter transformations get called for various input lines.
Note that this does *not* test the transformations themselves -- it's just
verifying that a particular combination of, e.g. config options and escape
chars trigger the proper handle_X transform of the input line.

Usage: run from the command line with *normal* python, not ipython:
> python test_prefilter.py

Fairly quiet output by default.  Pass in -v to get everyone's favorite dots.
"""

# The prefilter always ends in a call to some self.handle_X method.  We swap
# all of those out so that we can capture which one was called.

import sys
sys.path.append('..')
import IPython
import IPython.ipapi

verbose = False
if len(sys.argv) > 1:
    if sys.argv[1] == '-v':
        sys.argv = sys.argv[:-1]  # IPython is confused by -v, apparently
        verbose = True
    
IPython.Shell.start()

ip = IPython.ipapi.get()

# Collect failed tests + stats and print them at the end
failures = []
num_tests = 0

# Store the results in module vars as we go
last_line      = None
handler_called = None
def install_mock_handler(name):
    """Swap out one of the IP.handle_x methods with a function which can
    record which handler was called and what line was produced. The mock
    handler func always returns '', which causes ipython to cease handling
    the string immediately.  That way, that it doesn't echo output, raise
    exceptions, etc.  But do note that testing multiline strings thus gets
    a bit hard."""    
    def mock_handler(self, line, continue_prompt=None,
                     pre=None,iFun=None,theRest=None,
                     obj=None):
        #print "Inside %s with '%s'" % (name, line)
        global last_line, handler_called
        last_line = line
        handler_called = name
        return ''
    mock_handler.name = name
    setattr(IPython.iplib.InteractiveShell, name, mock_handler)

install_mock_handler('handle_normal')
install_mock_handler('handle_auto')
install_mock_handler('handle_magic')
install_mock_handler('handle_help')
install_mock_handler('handle_shell_escape')
install_mock_handler('handle_alias')
install_mock_handler('handle_emacs')


def reset_esc_handlers():
    """The escape handlers are stored in a hash (as an attribute of the
    InteractiveShell *instance*), so we have to rebuild that hash to get our
    new handlers in there."""
    s = ip.IP
    s.esc_handlers = {s.ESC_PAREN  : s.handle_auto,
                      s.ESC_QUOTE  : s.handle_auto,
                      s.ESC_QUOTE2 : s.handle_auto,
                      s.ESC_MAGIC  : s.handle_magic,
                      s.ESC_HELP   : s.handle_help,
                      s.ESC_SHELL  : s.handle_shell_escape,
                      s.ESC_SH_CAP : s.handle_shell_escape,
                      }
reset_esc_handlers()
    
# This is so I don't have to quote over and over.  Gotta be a better way.
handle_normal       = 'handle_normal'
handle_auto         = 'handle_auto'
handle_magic        = 'handle_magic'
handle_help         = 'handle_help'
handle_shell_escape = 'handle_shell_escape'
handle_alias        = 'handle_alias'
handle_emacs        = 'handle_emacs'

def check(assertion, failure_msg):
    """Check a boolean assertion and fail with a message if necessary. Store
    an error essage in module-level failures list in case of failure.  Print
    '.' or 'F' if module var Verbose is true.
    """
    global num_tests
    num_tests += 1
    if assertion:
        if verbose:
            sys.stdout.write('.')
            sys.stdout.flush()        
    else:
        if verbose:
            sys.stdout.write('F')
            sys.stdout.flush()
        failures.append(failure_msg)
    

def check_handler(expected_handler, line):
    """Verify that the expected hander was called (for the given line,
    passed in for failure reporting).
    
    Pulled out to its own function so that tests which don't use
    run_handler_tests can still take advantage of it."""
    check(handler_called == expected_handler,
          "Expected %s to be called for %s, "
          "instead %s called" % (expected_handler,
                                 repr(line),
                                 handler_called))
    

def run_handler_tests(h_tests):
    """Loop through a series of (input_line, handler_name) pairs, verifying
    that, for each ip calls the given handler for the given line. 

    The verbose complaint includes the line passed in, so if that line can
    include enough info to find the error, the tests are modestly
    self-documenting.
    """    
    for ln, expected_handler in h_tests:
        global handler_called
        handler_called = None
        ip.runlines(ln)
        check_handler(expected_handler, ln)

def run_one_test(ln, expected_handler):
    run_handler_tests([(ln, expected_handler)])
    

# =========================================
# Tests
# =========================================


# Fundamental escape characters + whitespace & misc
# =================================================
esc_handler_tests = [
    ( '?thing',    handle_help,  ),
    ( 'thing?',    handle_help ),  # '?' can trail...
    ( 'thing!',    handle_normal), # but only '?' can trail
    ( '   ?thing', handle_normal), # leading whitespace turns off esc chars
    ( '!ls',       handle_shell_escape),
    ( '! true',    handle_shell_escape),
    ( '!! true',   handle_shell_escape),
    ( '%magic',    handle_magic),
    # XXX Possibly, add test for /,; once those are unhooked from %autocall
    ( 'emacs_mode # PYTHON-MODE', handle_emacs ),
    ( ' ',         handle_normal), 

    # Trailing qmark combos.  Odd special cases abound

    # ! always takes priority!
    ( '!thing?',      handle_shell_escape), 
    ( '!thing arg?',  handle_shell_escape),
    ( '!!thing?',     handle_shell_escape),
    ( '!!thing arg?', handle_shell_escape),
    ( '    !!thing arg?', handle_shell_escape),

    # For all other leading esc chars, we always trigger help
    ( '%cmd?',     handle_help),
    ( '%cmd ?',    handle_help),
    ( '/cmd?',     handle_help),
    ( '/cmd ?',    handle_help),
    ( ';cmd?',     handle_help),
    ( ',cmd?',     handle_help),
    ]
run_handler_tests(esc_handler_tests)



# Shell Escapes in Multi-line statements
# ======================================
#
# We can't test this via runlines, since the hacked-over-for-testing
# handlers all return None, so continue_prompt never becomes true.  Instead
# we drop into prefilter directly and pass in continue_prompt.

old_mls = ip.options.multi_line_specials
for ln in [ '    !ls $f multi_line_specials %s',
            '    !!ls $f multi_line_specials %s',  # !! escapes work on mls
            # Trailing ? doesn't trigger help:            
            '    !ls $f multi_line_specials %s ?', 
            '    !!ls $f multi_line_specials %s ?',
            ]:
    ip.options.multi_line_specials = 1
    on_ln = ln % 'on'
    ignore = ip.IP.prefilter(on_ln, continue_prompt=True)
    check_handler(handle_shell_escape, on_ln)

    ip.options.multi_line_specials = 0
    off_ln = ln % 'off'
    ignore = ip.IP.prefilter(off_ln, continue_prompt=True)
    check_handler(handle_normal, off_ln)

ip.options.multi_line_specials = old_mls


# Automagic
# =========

# Pick one magic fun and one non_magic fun, make sure both exist
assert hasattr(ip.IP, "magic_cpaste")
assert not hasattr(ip.IP, "magic_does_not_exist")
ip.options.autocall = 0 # gotta have this off to get handle_normal
ip.options.automagic = 0
run_handler_tests([
    # Without automagic, only shows up with explicit escape
    ( 'cpaste', handle_normal),
    ( '%cpaste', handle_magic),
    ( '%does_not_exist', handle_magic),
    ])
ip.options.automagic = 1
run_handler_tests([
    ( 'cpaste',          handle_magic),
    ( '%cpaste',         handle_magic),
    ( 'does_not_exist',  handle_normal),
    ( '%does_not_exist', handle_magic),
    ( 'cd /',            handle_magic),
    ( 'cd = 2',          handle_normal),
    ( 'r',               handle_magic),
    ( 'r thing',         handle_magic),
    ( 'r"str"',          handle_normal),
    ])

# If next elt starts with anything that could be an assignment, func call,
# etc, we don't call the magic func, unless explicitly escaped to do so.
#magic_killing_tests = []
#for c in list('!=()<>,'):
#    magic_killing_tests.append(('cpaste %s killed_automagic' % c, handle_normal))
#    magic_killing_tests.append(('%%cpaste %s escaped_magic' % c,   handle_magic))
#run_handler_tests(magic_killing_tests)

# magic on indented continuation lines -- on iff multi_line_specials == 1
ip.options.multi_line_specials = 0
ln = '    cpaste multi_line off kills magic'
ignore = ip.IP.prefilter(ln, continue_prompt=True)
check_handler(handle_normal, ln)

ip.options.multi_line_specials = 1
ln = '    cpaste multi_line on enables magic'
ignore = ip.IP.prefilter(ln, continue_prompt=True)
check_handler(handle_magic, ln)

# user namespace shadows the magic one unless shell escaped
ip.user_ns['cpaste']     = 'user_ns'
run_handler_tests([
    ( 'cpaste',    handle_normal),
    ( '%cpaste',   handle_magic)])
del ip.user_ns['cpaste']



# Check for !=() turning off .ofind
# =================================
class AttributeMutator(object):
    """A class which will be modified on attribute access, to test ofind"""
    def __init__(self):
        self.called = False

    def getFoo(self): self.called = True
    foo = property(getFoo)

attr_mutator = AttributeMutator()
ip.to_user_ns('attr_mutator')

ip.options.autocall = 1 

run_one_test('attr_mutator.foo should mutate', handle_normal)
check(attr_mutator.called, 'ofind should be called in absence of assign characters')

for c in list('!=()<>+*/%^&|'): 
    attr_mutator.called = False
    run_one_test('attr_mutator.foo %s should *not* mutate' % c, handle_normal)
    run_one_test('attr_mutator.foo%s should *not* mutate' % c, handle_normal)
    
    check(not attr_mutator.called,
          'ofind should not be called near character %s' % c)



# Alias expansion
# ===============

# With autocall on or off, aliases should be shadowed by user, internal and
# __builtin__ namespaces
#
# XXX Can aliases have '.' in their name?  With autocall off, that works,
# with autocall on, it doesn't.  Hmmm.
import __builtin__
for ac_state in [0,1]:
    ip.options.autocall = ac_state
    ip.IP.alias_table['alias_cmd'] = 'alias_result'
    ip.IP.alias_table['alias_head.with_dot'] = 'alias_result'
    run_handler_tests([
        ("alias_cmd",           handle_alias),
        # XXX See note above
        #("alias_head.with_dot unshadowed, autocall=%s" % ac_state, handle_alias), 
        ("alias_cmd.something aliases must match whole expr", handle_normal),
        ("alias_cmd /", handle_alias),
        ])

    for ns in [ip.user_ns, ip.IP.internal_ns, __builtin__.__dict__ ]:
        ns['alias_cmd'] = 'a user value'
        ns['alias_head'] = 'a user value'
        run_handler_tests([
            ("alias_cmd",           handle_normal),
            ("alias_head.with_dot", handle_normal)])
        del ns['alias_cmd']
        del ns['alias_head']

ip.options.autocall = 1




# Autocall
# ========

# For all the tests below, 'len' is callable / 'thing' is not

# Objects which are instances of IPyAutocall are *always* autocalled
import IPython.ipapi
class Autocallable(IPython.ipapi.IPyAutocall):
    def __call__(self):
        return "called"
    
autocallable = Autocallable()
ip.to_user_ns('autocallable')


# First, with autocalling fully off
ip.options.autocall = 0
run_handler_tests( [
    # With no escapes, no autocalling expansions happen, callable or not,
    # unless the obj extends IPyAutocall
    ( 'len autocall_0',     handle_normal),
    ( 'thing autocall_0',   handle_normal),
    ( 'autocallable',       handle_auto),
    
    # With explicit escapes, callable and non-callables both get expanded,
    # regardless of the %autocall setting:
    ( '/len autocall_0',    handle_auto),
    ( ',len autocall_0 b0', handle_auto),
    ( ';len autocall_0 b0', handle_auto),
    
    ( '/thing autocall_0',    handle_auto),
    ( ',thing autocall_0 b0', handle_auto),
    ( ';thing autocall_0 b0', handle_auto),

    # Explicit autocall should not trigger if there is leading whitespace
    ( ' /len autocall_0',    handle_normal),
    ( ' ;len autocall_0',    handle_normal),
    ( ' ,len autocall_0',    handle_normal),
    ( ' / len autocall_0',   handle_normal),

    # But should work if the whitespace comes after the esc char
    ( '/ len autocall_0',    handle_auto),
    ( '; len autocall_0',    handle_auto),
    ( ', len autocall_0',    handle_auto),
    ( '/  len autocall_0',   handle_auto),
    ])


# Now, with autocall in default, 'smart' mode
ip.options.autocall = 1 
run_handler_tests( [
    # Autocalls without escapes -- only expand if it's callable
    ( 'len a1',       handle_auto),
    ( 'thing a1',     handle_normal),
    ( 'autocallable', handle_auto),

    # As above, all explicit escapes generate auto-calls, callable or not
    ( '/len a1',      handle_auto),
    ( ',len a1 b1',   handle_auto),
    ( ';len a1 b1',   handle_auto),
    ( '/thing a1',    handle_auto),
    ( ',thing a1 b1', handle_auto),
    ( ';thing a1 b1', handle_auto),

    # Autocalls only happen on things which look like funcs, even if
    # explicitly requested. Which, in this case means they look like a
    # sequence of identifiers and . attribute references. Possibly the
    # second of these two should trigger handle_auto.  But not for now.
    ( '"abc".join range(4)',   handle_normal),
    ( '/"abc".join range(4)',  handle_normal),
    ])


# No tests for autocall = 2, since the extra magic there happens inside the
# handle_auto function, which our test doesn't examine.

# Note that we leave autocall in default, 1, 'smart' mode


# Autocall / Binary operators
# ==========================

# Even with autocall on, 'len in thing' won't transform.
# But ';len in thing' will

# Note, the tests below don't check for multi-char ops. It could.

# XXX % is a binary op and should be in the list, too, but fails
bin_ops = list(r'<>,&^|*/+-') + 'is not in and or'.split()
bin_tests = []
for b in bin_ops:
    bin_tests.append(('len %s binop_autocall'  % b, handle_normal))
    bin_tests.append((';len %s binop_autocall' % b, handle_auto))
    bin_tests.append((',len %s binop_autocall' % b, handle_auto))
    bin_tests.append(('/len %s binop_autocall' % b, handle_auto))
    
# Who loves auto-generating tests? 
run_handler_tests(bin_tests)


# Possibly add tests for namespace shadowing (really ofind's business?).
#
# user > ipython internal > python builtin > alias > magic


# ============
# Test Summary
# ============
num_f = len(failures)
if verbose:
    print 
print "%s tests run, %s failure%s" % (num_tests,
                                      num_f,
                                      num_f != 1 and "s" or "")
for f in failures:
    print f

