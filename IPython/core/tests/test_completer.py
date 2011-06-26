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
from IPython.core import completer
from IPython.external.decorators import knownfailureif
from IPython.utils.tempdir import TemporaryDirectory

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
        self.sp.set_delims(' ')
        nt.assert_equal(self.sp.get_delims(), ' ')
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
