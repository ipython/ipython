# encoding: utf-8
"""Tests for the IPython tab-completion machinery."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import sys
import unittest

from contextlib import contextmanager

import nose.tools as nt

from traitlets.config.loader import Config
from IPython import get_ipython
from IPython.core import completer
from IPython.external.decorators import knownfailureif
from IPython.utils.tempdir import TemporaryDirectory, TemporaryWorkingDirectory
from IPython.utils.generics import complete_object
from IPython.utils.py3compat import string_types, unicode_type
from IPython.testing import decorators as dec

#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------

@contextmanager
def greedy_completion():
    ip = get_ipython()
    greedy_original = ip.Completer.greedy
    try:
        ip.Completer.greedy = True
        yield
    finally:
        ip.Completer.greedy = greedy_original

def test_protect_filename():
    if sys.platform == 'win32':
        pairs = [('abc','abc'),
                 (' abc','" abc"'),
                 ('a bc','"a bc"'),
                 ('a  bc','"a  bc"'),
                 ('  bc','"  bc"'),
                 ]
    else:
        pairs = [('abc','abc'),
                 (' abc',r'\ abc'),
                 ('a bc',r'a\ bc'),
                 ('a  bc',r'a\ \ bc'),
                 ('  bc',r'\ \ bc'),
                 # On posix, we also protect parens and other special characters.
                 ('a(bc',r'a\(bc'),
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
                 ]
    # run the actual tests
    for s1, s2 in pairs:
        s1p = completer.protect_filename(s1)
        nt.assert_equal(s1p, s2)


def check_line_split(splitter, test_specs):
    for part1, part2, split in test_specs:
        cursor_pos = len(part1)
        line = part1+part2
        out = splitter.split_line(line, cursor_pos)
        nt.assert_equal(out, split)


def test_line_split():
    """Basic line splitter test with default specs."""
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
    check_line_split(sp, [ map(unicode_type, p) for p in t] )


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
    for t in s + list(map(unicode_type, s)):
        # We don't need to check exact completion values (they may change
        # depending on the state of the namespace, but at least no exceptions
        # should be thrown and the return value should be a pair of text, list
        # values.
        text, matches = ip.complete(t)
        nt.assert_true(isinstance(text, string_types))
        nt.assert_true(isinstance(matches, list))

@dec.onlyif(sys.version_info[0] >= 3, 'This test only applies in Py>=3')
def test_latex_completions():
    from IPython.core.latex_symbols import latex_symbols
    import random
    ip = get_ipython()
    # Test some random unicode symbols
    keys = random.sample(latex_symbols.keys(), 10)
    for k in keys:
        text, matches = ip.complete(k)
        nt.assert_equal(len(matches),1)
        nt.assert_equal(text, k)
        nt.assert_equal(matches[0], latex_symbols[k])
    # Test a more complex line
    text, matches = ip.complete(u'print(\\alpha')
    nt.assert_equals(text, u'\\alpha')
    nt.assert_equals(matches[0], latex_symbols['\\alpha'])
    # Test multiple matching latex symbols
    text, matches = ip.complete(u'\\al')
    nt.assert_in('\\alpha', matches)
    nt.assert_in('\\aleph', matches)




@dec.onlyif(sys.version_info[0] >= 3, 'This test only apply on python3')
def test_back_latex_completion():
    ip = get_ipython()

    # do not return more than 1 matches fro \beta, only the latex one.
    name, matches = ip.complete('\\β')
    nt.assert_equal(len(matches), 1)
    nt.assert_equal(matches[0], '\\beta')

@dec.onlyif(sys.version_info[0] >= 3, 'This test only apply on python3')
def test_back_unicode_completion():
    ip = get_ipython()
    
    name, matches = ip.complete('\\Ⅴ')
    nt.assert_equal(len(matches), 1)
    nt.assert_equal(matches[0], '\\ROMAN NUMERAL FIVE')


@dec.onlyif(sys.version_info[0] >= 3, 'This test only apply on python3')
def test_forward_unicode_completion():
    ip = get_ipython()
    
    name, matches = ip.complete('\\ROMAN NUMERAL FIVE')
    nt.assert_equal(len(matches), 1)
    nt.assert_equal(matches[0], 'Ⅴ')

@dec.onlyif(sys.version_info[0] >= 3, 'This test only apply on python3')
@dec.knownfailureif(sys.platform == 'win32', 'Fails if there is a C:\\j... path')
def test_no_ascii_back_completion():
    ip = get_ipython()
    with TemporaryWorkingDirectory():  # Avoid any filename completions
        # single ascii letter that don't have yet completions
        for letter in 'jJ' :
            name, matches = ip.complete('\\'+letter)
            nt.assert_equal(matches, [])




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
        suffixes = ['1', '2']
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
    with TemporaryWorkingDirectory():
        prefix = './foo'
        suffixes = ['1', '2']
        names = [prefix+s for s in suffixes]
        for n in names:
            open(n, 'w').close()

        # Check simple completion
        c = ip.complete(prefix)[1]
        nt.assert_equal(c, names)

        # Now check with a function call
        cmd = 'a = f("%s' % prefix
        c = ip.complete(prefix, cmd)[1]
        comp = set(prefix+s for s in suffixes)
        nt.assert_true(comp.issubset(set(c)))


def test_greedy_completions():
    ip = get_ipython()
    ip.ex('a=list(range(5))')
    _,c = ip.complete('.',line='a[0].')
    nt.assert_false('.real' in c,
                    "Shouldn't have completed on a[0]: %s"%c)
    with greedy_completion():
        def _(line, cursor_pos, expect, message):
            _,c = ip.complete('.', line=line, cursor_pos=cursor_pos)
            nt.assert_in(expect, c, message%c)

        yield _, 'a[0].', 5, 'a[0].real', "Should have completed on a[0].: %s"
        yield _, 'a[0].r', 6, 'a[0].real', "Should have completed on a[0].r: %s"
        
        if sys.version_info > (3,4):
            yield _, 'a[0].from_', 10, 'a[0].from_bytes', "Should have completed on a[0].from_: %s"



def test_omit__names():
    # also happens to test IPCompleter as a configurable
    ip = get_ipython()
    ip._hidden_attr = 1
    ip._x = {}
    c = ip.Completer
    ip.ex('ip=get_ipython()')
    cfg = Config()
    cfg.IPCompleter.omit__names = 0
    c.update_config(cfg)
    s,matches = c.complete('ip.')
    nt.assert_in('ip.__str__', matches)
    nt.assert_in('ip._hidden_attr', matches)
    cfg = Config()
    cfg.IPCompleter.omit__names = 1
    c.update_config(cfg)
    s,matches = c.complete('ip.')
    nt.assert_not_in('ip.__str__', matches)
    nt.assert_in('ip._hidden_attr', matches)
    cfg = Config()
    cfg.IPCompleter.omit__names = 2
    c.update_config(cfg)
    s,matches = c.complete('ip.')
    nt.assert_not_in('ip.__str__', matches)
    nt.assert_not_in('ip._hidden_attr', matches)
    s,matches = c.complete('ip._x.')
    nt.assert_in('ip._x.keys', matches)
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
    nt.assert_in('d.x', matches)


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
    s, matches = c.complete(None, 'myfunc(1,b)', 10)
    nt.assert_in('b=', matches)
    s, matches = c.complete(None, 'myfunc(a="escaped\\")string",b')
    nt.assert_in('b=', matches)
    #builtin function
    s, matches = c.complete(None, 'min(k, k')
    nt.assert_in('key=', matches)


def test_default_arguments_from_docstring():
    ip = get_ipython()
    c = ip.Completer
    kwd = c._default_arguments_from_docstring(
        'min(iterable[, key=func]) -> value')
    nt.assert_equal(kwd, ['key'])
    #with cython type etc
    kwd = c._default_arguments_from_docstring(
        'Minuit.migrad(self, int ncall=10000, resume=True, int nsplit=1)\n')
    nt.assert_equal(kwd, ['ncall', 'resume', 'nsplit'])
    #white spaces
    kwd = c._default_arguments_from_docstring(
        '\n Minuit.migrad(self, int ncall=10000, resume=True, int nsplit=1)\n')
    nt.assert_equal(kwd, ['ncall', 'resume', 'nsplit'])

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


def test_magic_completion_order():

    ip = get_ipython()
    c = ip.Completer

    # Test ordering of magics and non-magics with the same name
    # We want the non-magic first

    # Before importing matplotlib, there should only be one option:

    text, matches = c.complete('mat')
    nt.assert_equal(matches, ["%matplotlib"])


    ip.run_cell("matplotlib = 1")  # introduce name into namespace

    # After the import, there should be two options, ordered like this:
    text, matches = c.complete('mat')
    nt.assert_equal(matches, ["matplotlib", "%matplotlib"])


    ip.run_cell("timeit = 1")  # define a user variable called 'timeit'

    # Order of user variable and line and cell magics with same name:
    text, matches = c.complete('timeit')
    nt.assert_equal(matches, ["timeit", "%timeit","%%timeit"])


def test_dict_key_completion_string():
    """Test dictionary key completion for string keys"""
    ip = get_ipython()
    complete = ip.Completer.complete

    ip.user_ns['d'] = {'abc': None}

    # check completion at different stages
    _, matches = complete(line_buffer="d[")
    nt.assert_in("'abc'", matches)
    nt.assert_not_in("'abc']", matches)

    _, matches = complete(line_buffer="d['")
    nt.assert_in("abc", matches)
    nt.assert_not_in("abc']", matches)

    _, matches = complete(line_buffer="d['a")
    nt.assert_in("abc", matches)
    nt.assert_not_in("abc']", matches)

    # check use of different quoting
    _, matches = complete(line_buffer="d[\"")
    nt.assert_in("abc", matches)
    nt.assert_not_in('abc\"]', matches)

    _, matches = complete(line_buffer="d[\"a")
    nt.assert_in("abc", matches)
    nt.assert_not_in('abc\"]', matches)

    # check sensitivity to following context
    _, matches = complete(line_buffer="d[]", cursor_pos=2)
    nt.assert_in("'abc'", matches)

    _, matches = complete(line_buffer="d['']", cursor_pos=3)
    nt.assert_in("abc", matches)
    nt.assert_not_in("abc'", matches)
    nt.assert_not_in("abc']", matches)

    # check multiple solutions are correctly returned and that noise is not
    ip.user_ns['d'] = {'abc': None, 'abd': None, 'bad': None, object(): None,
                       5: None}

    _, matches = complete(line_buffer="d['a")
    nt.assert_in("abc", matches)
    nt.assert_in("abd", matches)
    nt.assert_not_in("bad", matches)
    assert not any(m.endswith((']', '"', "'")) for m in matches), matches

    # check escaping and whitespace
    ip.user_ns['d'] = {'a\nb': None, 'a\'b': None, 'a"b': None, 'a word': None}
    _, matches = complete(line_buffer="d['a")
    nt.assert_in("a\\nb", matches)
    nt.assert_in("a\\'b", matches)
    nt.assert_in("a\"b", matches)
    nt.assert_in("a word", matches)
    assert not any(m.endswith((']', '"', "'")) for m in matches), matches

    # - can complete on non-initial word of the string
    _, matches = complete(line_buffer="d['a w")
    nt.assert_in("word", matches)

    # - understands quote escaping
    _, matches = complete(line_buffer="d['a\\'")
    nt.assert_in("b", matches)

    # - default quoting should work like repr
    _, matches = complete(line_buffer="d[")
    nt.assert_in("\"a'b\"", matches)

    # - when opening quote with ", possible to match with unescaped apostrophe
    _, matches = complete(line_buffer="d[\"a'")
    nt.assert_in("b", matches)

    # need to not split at delims that readline won't split at
    if '-' not in ip.Completer.splitter.delims:
        ip.user_ns['d'] = {'before-after': None}
        _, matches = complete(line_buffer="d['before-af")
        nt.assert_in('before-after', matches)

def test_dict_key_completion_contexts():
    """Test expression contexts in which dict key completion occurs"""
    ip = get_ipython()
    complete = ip.Completer.complete
    d = {'abc': None}
    ip.user_ns['d'] = d

    class C:
        data = d
    ip.user_ns['C'] = C
    ip.user_ns['get'] = lambda: d

    def assert_no_completion(**kwargs):
        _, matches = complete(**kwargs)
        nt.assert_not_in('abc', matches)
        nt.assert_not_in('abc\'', matches)
        nt.assert_not_in('abc\']', matches)
        nt.assert_not_in('\'abc\'', matches)
        nt.assert_not_in('\'abc\']', matches)

    def assert_completion(**kwargs):
        _, matches = complete(**kwargs)
        nt.assert_in("'abc'", matches)
        nt.assert_not_in("'abc']", matches)

    # no completion after string closed, even if reopened
    assert_no_completion(line_buffer="d['a'")
    assert_no_completion(line_buffer="d[\"a\"")
    assert_no_completion(line_buffer="d['a' + ")
    assert_no_completion(line_buffer="d['a' + '")

    # completion in non-trivial expressions
    assert_completion(line_buffer="+ d[")
    assert_completion(line_buffer="(d[")
    assert_completion(line_buffer="C.data[")

    # greedy flag
    def assert_completion(**kwargs):
        _, matches = complete(**kwargs)
        nt.assert_in("get()['abc']", matches)
    
    assert_no_completion(line_buffer="get()[")
    with greedy_completion():
        assert_completion(line_buffer="get()[")
        assert_completion(line_buffer="get()['")
        assert_completion(line_buffer="get()['a")
        assert_completion(line_buffer="get()['ab")
        assert_completion(line_buffer="get()['abc")



@dec.onlyif(sys.version_info[0] >= 3, 'This test only applies in Py>=3')
def test_dict_key_completion_bytes():
    """Test handling of bytes in dict key completion"""
    ip = get_ipython()
    complete = ip.Completer.complete

    ip.user_ns['d'] = {'abc': None, b'abd': None}

    _, matches = complete(line_buffer="d[")
    nt.assert_in("'abc'", matches)
    nt.assert_in("b'abd'", matches)

    if False:  # not currently implemented
        _, matches = complete(line_buffer="d[b")
        nt.assert_in("b'abd'", matches)
        nt.assert_not_in("b'abc'", matches)

        _, matches = complete(line_buffer="d[b'")
        nt.assert_in("abd", matches)
        nt.assert_not_in("abc", matches)

        _, matches = complete(line_buffer="d[B'")
        nt.assert_in("abd", matches)
        nt.assert_not_in("abc", matches)

        _, matches = complete(line_buffer="d['")
        nt.assert_in("abc", matches)
        nt.assert_not_in("abd", matches)


@dec.onlyif(sys.version_info[0] < 3, 'This test only applies in Py<3')
def test_dict_key_completion_unicode_py2():
    """Test handling of unicode in dict key completion"""
    ip = get_ipython()
    complete = ip.Completer.complete

    ip.user_ns['d'] = {u'abc': None,
                       u'a\u05d0b': None}

    _, matches = complete(line_buffer="d[")
    nt.assert_in("u'abc'", matches)
    nt.assert_in("u'a\\u05d0b'", matches)

    _, matches = complete(line_buffer="d['a")
    nt.assert_in("abc", matches)
    nt.assert_not_in("a\\u05d0b", matches)

    _, matches = complete(line_buffer="d[u'a")
    nt.assert_in("abc", matches)
    nt.assert_in("a\\u05d0b", matches)

    _, matches = complete(line_buffer="d[U'a")
    nt.assert_in("abc", matches)
    nt.assert_in("a\\u05d0b", matches)

    # query using escape
    if sys.platform != 'win32':
        # Known failure on Windows
        _, matches = complete(line_buffer=u"d[u'a\\u05d0")
        nt.assert_in("u05d0b", matches)  # tokenized after \\

    # query using character
    _, matches = complete(line_buffer=u"d[u'a\u05d0")
    nt.assert_in(u"a\u05d0b", matches)
    
    with greedy_completion():
        _, matches = complete(line_buffer="d[")
        nt.assert_in("d[u'abc']", matches)
        nt.assert_in("d[u'a\\u05d0b']", matches)

        _, matches = complete(line_buffer="d['a")
        nt.assert_in("d['abc']", matches)
        nt.assert_not_in("d[u'a\\u05d0b']", matches)

        _, matches = complete(line_buffer="d[u'a")
        nt.assert_in("d[u'abc']", matches)
        nt.assert_in("d[u'a\\u05d0b']", matches)

        _, matches = complete(line_buffer="d[U'a")
        nt.assert_in("d[U'abc']", matches)
        nt.assert_in("d[U'a\\u05d0b']", matches)

        # query using escape
        _, matches = complete(line_buffer=u"d[u'a\\u05d0")
        nt.assert_in("d[u'a\\u05d0b']", matches)  # tokenized after \\

        # query using character
        _, matches = complete(line_buffer=u"d[u'a\u05d0")
        nt.assert_in(u"d[u'a\u05d0b']", matches)


@dec.onlyif(sys.version_info[0] >= 3, 'This test only applies in Py>=3')
def test_dict_key_completion_unicode_py3():
    """Test handling of unicode in dict key completion"""
    ip = get_ipython()
    complete = ip.Completer.complete

    ip.user_ns['d'] = {u'a\u05d0': None}

    # query using escape
    if sys.platform != 'win32':
        # Known failure on Windows
        _, matches = complete(line_buffer="d['a\\u05d0")
        nt.assert_in("u05d0", matches)  # tokenized after \\

    # query using character
    _, matches = complete(line_buffer="d['a\u05d0")
    nt.assert_in(u"a\u05d0", matches)
    
    with greedy_completion():
        # query using escape
        _, matches = complete(line_buffer="d['a\\u05d0")
        nt.assert_in("d['a\\u05d0']", matches)  # tokenized after \\

        # query using character
        _, matches = complete(line_buffer="d['a\u05d0")
        nt.assert_in(u"d['a\u05d0']", matches)
        


@dec.skip_without('numpy')
def test_struct_array_key_completion():
    """Test dict key completion applies to numpy struct arrays"""
    import numpy
    ip = get_ipython()
    complete = ip.Completer.complete
    ip.user_ns['d'] = numpy.array([], dtype=[('hello', 'f'), ('world', 'f')])
    _, matches = complete(line_buffer="d['")
    nt.assert_in("hello", matches)
    nt.assert_in("world", matches)
    # complete on the numpy struct itself
    dt = numpy.dtype([('my_head', [('my_dt', '>u4'), ('my_df', '>u4')]),
                      ('my_data', '>f4', 5)])
    x = numpy.zeros(2, dtype=dt)
    ip.user_ns['d'] = x[1]
    _, matches = complete(line_buffer="d['")
    nt.assert_in("my_head", matches)
    nt.assert_in("my_data", matches)
    # complete on a nested level
    with greedy_completion():
        ip.user_ns['d'] = numpy.zeros(2, dtype=dt)
        _, matches = complete(line_buffer="d[1]['my_head']['")
        nt.assert_true(any(["my_dt" in m for m in matches]))
        nt.assert_true(any(["my_df" in m for m in matches]))


@dec.skip_without('pandas')
def test_dataframe_key_completion():
    """Test dict key completion applies to pandas DataFrames"""
    import pandas
    ip = get_ipython()
    complete = ip.Completer.complete
    ip.user_ns['d'] = pandas.DataFrame({'hello': [1], 'world': [2]})
    _, matches = complete(line_buffer="d['")
    nt.assert_in("hello", matches)
    nt.assert_in("world", matches)


def test_dict_key_completion_invalids():
    """Smoke test cases dict key completion can't handle"""
    ip = get_ipython()
    complete = ip.Completer.complete

    ip.user_ns['no_getitem'] = None
    ip.user_ns['no_keys'] = []
    ip.user_ns['cant_call_keys'] = dict
    ip.user_ns['empty'] = {}
    ip.user_ns['d'] = {'abc': 5}

    _, matches = complete(line_buffer="no_getitem['")
    _, matches = complete(line_buffer="no_keys['")
    _, matches = complete(line_buffer="cant_call_keys['")
    _, matches = complete(line_buffer="empty['")
    _, matches = complete(line_buffer="name_error['")
    _, matches = complete(line_buffer="d['\\")  # incomplete escape

class KeyCompletable(object):
    def __init__(self, things=()):
        self.things = things

    def _ipython_key_completions_(self):
        return list(self.things)

def test_object_key_completion():
    ip = get_ipython()
    ip.user_ns['key_completable'] = KeyCompletable(['qwerty', 'qwick'])

    _, matches = ip.Completer.complete(line_buffer="key_completable['qw")
    nt.assert_in('qwerty', matches)
    nt.assert_in('qwick', matches)


def test_aimport_module_completer():
    ip = get_ipython()
    _, matches = ip.complete('i', '%aimport i')
    nt.assert_in('io', matches)
    nt.assert_not_in('int', matches)

def test_nested_import_module_completer():
    ip = get_ipython()
    _, matches = ip.complete(None, 'import IPython.co', 17)
    nt.assert_in('IPython.core', matches)
    nt.assert_not_in('import IPython.core', matches)
    nt.assert_not_in('IPython.display', matches)

def test_import_module_completer():
    ip = get_ipython()
    _, matches = ip.complete('i', 'import i')
    nt.assert_in('io', matches)
    nt.assert_not_in('int', matches)

def test_from_module_completer():
    ip = get_ipython()
    _, matches = ip.complete('B', 'from io import B', 16)
    nt.assert_in('BytesIO', matches)
    nt.assert_not_in('BaseException', matches)
