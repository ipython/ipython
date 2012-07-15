"""Tests for the IPython tab-completion machinery.
"""
#-----------------------------------------------------------------------------
# Module imports
#-----------------------------------------------------------------------------

# stdlib
import os
import sys
import unittest

# third party
import nose.tools as nt

# our own packages
from IPython.config.loader import Config
from IPython.core import completer
from IPython.external.decorators import knownfailureif
from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.generics import complete_object

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
    # On posix, we also protect parens and other special characters
    if sys.platform != 'win32':
        pairs.extend( [('a(bc',r'a\(bc'),
                       ('a)bc',r'a\)bc'),
                       ('a( )bc',r'a\(\ \)bc'),
                       ('a[1]bc', r'a\[1\]bc'),
                       ('a{1}bc', r'a\{1\}bc'),
                       ('a#bc', r'a\#bc'),
                       ('a?bc', r'a\?bc'),
                       ('a=bc', r'a\=bc'),
                       ('a\\bc', r'a\\bc'),
                       ('a|bc', r'a\|bc'),
                       ('a;bc', r'a\;bc'),
                       ('a:bc', r'a\:bc'),
                       ("a'bc", r"a\'bc"),
                       ('a*bc', r'a\*bc'),
                       ('a"bc', r'a\"bc'),
                       ('a^bc', r'a\^bc'),
                       ('a&bc', r'a\&bc'),
                       ] )
    # run the actual tests
    for s1, s2 in pairs:
        s1p = completer.protect_filename(s1)
        nt.assert_equals(s1p, s2)


def check_line_split(splitter, test_specs):
    for part1, part2, split in test_specs:
        cursor_pos = len(part1)
        line = part1+part2
        out = splitter.split_line(line, cursor_pos)
        nt.assert_equal(out, split)


def test_line_split():
    """Basice line splitter test with default specs."""
    sp = completer.CompletionSplitter()
    # The format of the test specs is: part1, part2, expected answer.  Parts 1
    # and 2 are joined into the 'line' sent to the splitter, as if the cursor
    # was at the end of part1.  So an empty part2 represents someone hitting
    # tab at the end of the line, the most common case.
    t = [('run some/scrip', '', 'some/scrip'),
         ('run scripts/er', 'ror.py foo', 'scripts/er'),
         ('echo $HOM', '', 'HOM'),
         ('print sys.pa', '', 'sys.pa'),
         ('print(sys.pa', '', 'sys.pa'),
         ("execfile('scripts/er", '', 'scripts/er'),
         ('a[x.', '', 'x.'),
         ('a[x.', 'y', 'x.'),
         ('cd "some_file/', '', 'some_file/'),
         ]
    check_line_split(sp, t)
    # Ensure splitting works OK with unicode by re-running the tests with
    # all inputs turned into unicode
    check_line_split(sp, [ map(unicode, p) for p in t] )


def test_custom_completion_error():
    """Test that errors from custom attribute completers are silenced."""
    ip = get_ipython()
    class A(object): pass
    ip.user_ns['a'] = A()
    
    @complete_object.when_type(A)
    def complete_A(a, existing_completions):
        raise TypeError("this should be silenced")
    
    ip.complete("a.")


def test_unicode_completions():
    ip = get_ipython()
    # Some strings that trigger different types of completion.  Check them both
    # in str and unicode forms
    s = ['ru', '%ru', 'cd /', 'floa', 'float(x)/']
    for t in s + map(unicode, s):
        # We don't need to check exact completion values (they may change
        # depending on the state of the namespace, but at least no exceptions
        # should be thrown and the return value should be a pair of text, list
        # values.
        text, matches = ip.complete(t)
        nt.assert_true(isinstance(text, basestring))
        nt.assert_true(isinstance(matches, list))


class CompletionSplitterTestCase(unittest.TestCase):
    def setUp(self):
        self.sp = completer.CompletionSplitter()

    def test_delim_setting(self):
        self.sp.delims = ' '
        nt.assert_equal(self.sp.delims, ' ')
        nt.assert_equal(self.sp._delim_expr, '[\ ]')

    def test_spaces(self):
        """Test with only spaces as split chars."""
        self.sp.delims = ' '
        t = [('foo', '', 'foo'),
             ('run foo', '', 'foo'),
             ('run foo', 'bar', 'foo'),
             ]
        check_line_split(self.sp, t)


def test_has_open_quotes1():
    for s in ["'", "'''", "'hi' '"]:
        nt.assert_equal(completer.has_open_quotes(s), "'")


def test_has_open_quotes2():
    for s in ['"', '"""', '"hi" "']:
        nt.assert_equal(completer.has_open_quotes(s), '"')


def test_has_open_quotes3():
    for s in ["''", "''' '''", "'hi' 'ipython'"]:
        nt.assert_false(completer.has_open_quotes(s))


def test_has_open_quotes4():
    for s in ['""', '""" """', '"hi" "ipython"']:
        nt.assert_false(completer.has_open_quotes(s))


@knownfailureif(sys.platform == 'win32', "abspath completions fail on Windows")
def test_abspath_file_completions():
    ip = get_ipython()
    with TemporaryDirectory() as tmpdir:
        prefix = os.path.join(tmpdir, 'foo')
        suffixes = map(str, [1,2])
        names = [prefix+s for s in suffixes]
        for n in names:
            open(n, 'w').close()

        # Check simple completion
        c = ip.complete(prefix)[1]
        nt.assert_equal(c, names)

        # Now check with a function call
        cmd = 'a = f("%s' % prefix
        c = ip.complete(prefix, cmd)[1]
        comp = [prefix+s for s in suffixes]
        nt.assert_equal(c, comp)


def test_local_file_completions():
    ip = get_ipython()
    cwd = os.getcwdu()
    try:
        with TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            prefix = './foo'
            suffixes = map(str, [1,2])
            names = [prefix+s for s in suffixes]
            for n in names:
                open(n, 'w').close()

            # Check simple completion
            c = ip.complete(prefix)[1]
            nt.assert_equal(c, names)

            # Now check with a function call
            cmd = 'a = f("%s' % prefix
            c = ip.complete(prefix, cmd)[1]
            comp = [prefix+s for s in suffixes]
            nt.assert_equal(c, comp)
    finally:
        # prevent failures from making chdir stick
        os.chdir(cwd)


def test_greedy_completions():
    ip = get_ipython()
    greedy_original = ip.Completer.greedy
    try:
        ip.Completer.greedy = False
        ip.ex('a=range(5)')
        _,c = ip.complete('.',line='a[0].')
        nt.assert_false('a[0].real' in c,
                        "Shouldn't have completed on a[0]: %s"%c)
        ip.Completer.greedy = True
        _,c = ip.complete('.',line='a[0].')
        nt.assert_true('a[0].real' in c, "Should have completed on a[0]: %s"%c)
    finally:
        ip.Completer.greedy = greedy_original


def test_omit__names():
    # also happens to test IPCompleter as a configurable
    ip = get_ipython()
    ip._hidden_attr = 1
    c = ip.Completer
    ip.ex('ip=get_ipython()')
    cfg = Config()
    cfg.IPCompleter.omit__names = 0
    c.update_config(cfg)
    s,matches = c.complete('ip.')
    nt.assert_true('ip.__str__' in matches)
    nt.assert_true('ip._hidden_attr' in matches)
    cfg.IPCompleter.omit__names = 1
    c.update_config(cfg)
    s,matches = c.complete('ip.')
    nt.assert_false('ip.__str__' in matches)
    nt.assert_true('ip._hidden_attr' in matches)
    cfg.IPCompleter.omit__names = 2
    c.update_config(cfg)
    s,matches = c.complete('ip.')
    nt.assert_false('ip.__str__' in matches)
    nt.assert_false('ip._hidden_attr' in matches)
    del ip._hidden_attr


def test_limit_to__all__False_ok():
    ip = get_ipython()
    c = ip.Completer
    ip.ex('class D: x=24')
    ip.ex('d=D()')
    cfg = Config()
    cfg.IPCompleter.limit_to__all__ = False
    c.update_config(cfg)
    s, matches = c.complete('d.')
    nt.assert_true('d.x' in matches) 


def test_limit_to__all__True_ok():
    ip = get_ipython()
    c = ip.Completer
    ip.ex('class D: x=24')
    ip.ex('d=D()')
    ip.ex("d.__all__=['z']")
    cfg = Config()
    cfg.IPCompleter.limit_to__all__ = True
    c.update_config(cfg)
    s, matches = c.complete('d.')
    nt.assert_true('d.z' in matches) 
    nt.assert_false('d.x' in matches)


def test_get__all__entries_ok():
    class A(object):
        __all__ = ['x', 1]
    words = completer.get__all__entries(A())
    nt.assert_equal(words, ['x'])


def test_get__all__entries_no__all__ok():
    class A(object):
        pass
    words = completer.get__all__entries(A())
    nt.assert_equal(words, [])


def test_func_kw_completions():
    ip = get_ipython()
    c = ip.Completer
    ip.ex('def myfunc(a=1,b=2): return a+b')
    s, matches = c.complete(None, 'myfunc(1,b')
    nt.assert_in('b=', matches)
    # Simulate completing with cursor right after b (pos==10):
    s, matches = c.complete(None,'myfunc(1,b)', 10)
    nt.assert_in('b=', matches)
    s, matches = c.complete(None,'myfunc(a="escaped\\")string",b')
    nt.assert_in('b=', matches)


def test_line_magics():
    ip = get_ipython()
    c = ip.Completer
    s, matches = c.complete(None, 'lsmag')
    nt.assert_in('%lsmagic', matches)
    s, matches = c.complete(None, '%lsmag')
    nt.assert_in('%lsmagic', matches)


def test_cell_magics():
    from IPython.core.magic import register_cell_magic

    @register_cell_magic
    def _foo_cellm(line, cell):
        pass
    
    ip = get_ipython()
    c = ip.Completer

    s, matches = c.complete(None, '_foo_ce')
    nt.assert_in('%%_foo_cellm', matches)
    s, matches = c.complete(None, '%%_foo_ce')
    nt.assert_in('%%_foo_cellm', matches)


def test_line_cell_magics():
    from IPython.core.magic import register_line_cell_magic

    @register_line_cell_magic
    def _bar_cellm(line, cell):
        pass
    
    ip = get_ipython()
    c = ip.Completer

    # The policy here is trickier, see comments in completion code.  The
    # returned values depend on whether the user passes %% or not explicitly,
    # and this will show a difference if the same name is both a line and cell
    # magic.
    s, matches = c.complete(None, '_bar_ce')
    nt.assert_in('%_bar_cellm', matches)
    nt.assert_in('%%_bar_cellm', matches)
    s, matches = c.complete(None, '%_bar_ce')
    nt.assert_in('%_bar_cellm', matches)
    nt.assert_in('%%_bar_cellm', matches)
    s, matches = c.complete(None, '%%_bar_ce')
    nt.assert_not_in('%_bar_cellm', matches)
    nt.assert_in('%%_bar_cellm', matches)

