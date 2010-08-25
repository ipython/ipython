"""Tests for the IPython tab-completion machinery.
"""
#-----------------------------------------------------------------------------
# Module imports
#-----------------------------------------------------------------------------

# stdlib
import sys
import unittest

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


class CompletionSplitterTestCase(unittest.TestCase):
    def setUp(self):
        self.sp = completer.CompletionSplitter()

    def test_delim_setting(self):
        self.sp.delims = ' '
        # Validate that property handling works ok
        nt.assert_equal(self.sp.delims, ' ')
        nt.assert_equal(self.sp.delim_expr, '[\ ]')

    def test_spaces(self):
        """Test with only spaces as split chars."""
        self.sp.delims = ' '
        t = [('foo', '', 'foo'),
             ('run foo', '', 'foo'),
             ('run foo', 'bar', 'foo'),
             ]
        check_line_split(self.sp, t)
