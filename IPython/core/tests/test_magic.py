# -*- coding: utf-8 -*-
"""Tests for various magic functions.

Needs to be run by nose (to make ipython session available).
"""
from __future__ import absolute_import

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import io
import os
import sys
from StringIO import StringIO
from unittest import TestCase

try:
    from importlib import invalidate_caches   # Required from Python 3.3
except ImportError:
    def invalidate_caches():
        pass

import nose.tools as nt

from IPython.core import magic
from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic,
                                register_line_magic, register_cell_magic,
                                register_line_cell_magic)
from IPython.core.magics import execution, script
from IPython.nbformat.v3.tests.nbexamples import nb0
from IPython.nbformat import current
from IPython.testing import decorators as dec
from IPython.testing import tools as tt
from IPython.utils import py3compat
from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.process import find_cmd

#-----------------------------------------------------------------------------
# Test functions begin
#-----------------------------------------------------------------------------

@magic.magics_class
class DummyMagics(magic.Magics): pass

def test_rehashx():
    # clear up everything
    _ip = get_ipython()
    _ip.alias_manager.alias_table.clear()
    del _ip.db['syscmdlist']
    
    _ip.magic('rehashx')
    # Practically ALL ipython development systems will have more than 10 aliases

    yield (nt.assert_true, len(_ip.alias_manager.alias_table) > 10)
    for key, val in _ip.alias_manager.alias_table.iteritems():
        # we must strip dots from alias names
        nt.assert_true('.' not in key)

    # rehashx must fill up syscmdlist
    scoms = _ip.db['syscmdlist']
    yield (nt.assert_true, len(scoms) > 10)


def test_magic_parse_options():
    """Test that we don't mangle paths when parsing magic options."""
    ip = get_ipython()
    path = 'c:\\x'
    m = DummyMagics(ip)
    opts = m.parse_options('-f %s' % path,'f:')[0]
    # argv splitting is os-dependent
    if os.name == 'posix':
        expected = 'c:x'
    else:
        expected = path
    nt.assert_equals(opts['f'], expected)

def test_magic_parse_long_options():
    """Magic.parse_options can handle --foo=bar long options"""
    ip = get_ipython()
    m = DummyMagics(ip)
    opts, _ = m.parse_options('--foo --bar=bubble', 'a', 'foo', 'bar=')
    nt.assert_true('foo' in opts)
    nt.assert_true('bar' in opts)
    nt.assert_true(opts['bar'], "bubble")


@dec.skip_without('sqlite3')
def doctest_hist_f():
    """Test %hist -f with temporary filename.

    In [9]: import tempfile

    In [10]: tfile = tempfile.mktemp('.py','tmp-ipython-')

    In [11]: %hist -nl -f $tfile 3

    In [13]: import os; os.unlink(tfile)
    """


@dec.skip_without('sqlite3')
def doctest_hist_r():
    """Test %hist -r

    XXX - This test is not recording the output correctly.  For some reason, in
    testing mode the raw history isn't getting populated.  No idea why.
    Disabling the output checking for now, though at least we do run it.

    In [1]: 'hist' in _ip.lsmagic()
    Out[1]: True

    In [2]: x=1

    In [3]: %hist -rl 2
    x=1 # random
    %hist -r 2
    """


@dec.skip_without('sqlite3')
def doctest_hist_op():
    """Test %hist -op

    In [1]: class b(float):
       ...:     pass
       ...: 

    In [2]: class s(object):
       ...:     def __str__(self):
       ...:         return 's'
       ...: 

    In [3]: 

    In [4]: class r(b):
       ...:     def __repr__(self):
       ...:         return 'r'
       ...: 

    In [5]: class sr(s,r): pass
       ...: 

    In [6]: 

    In [7]: bb=b()

    In [8]: ss=s()

    In [9]: rr=r()

    In [10]: ssrr=sr()

    In [11]: 4.5
    Out[11]: 4.5

    In [12]: str(ss)
    Out[12]: 's'

    In [13]: 

    In [14]: %hist -op
    >>> class b:
    ...     pass
    ... 
    >>> class s(b):
    ...     def __str__(self):
    ...         return 's'
    ... 
    >>> 
    >>> class r(b):
    ...     def __repr__(self):
    ...         return 'r'
    ... 
    >>> class sr(s,r): pass
    >>> 
    >>> bb=b()
    >>> ss=s()
    >>> rr=r()
    >>> ssrr=sr()
    >>> 4.5
    4.5
    >>> str(ss)
    's'
    >>> 
    """


@dec.skip_without('sqlite3')
def test_macro():
    ip = get_ipython()
    ip.history_manager.reset()   # Clear any existing history.
    cmds = ["a=1", "def b():\n  return a**2", "print(a,b())"]
    for i, cmd in enumerate(cmds, start=1):
        ip.history_manager.store_inputs(i, cmd)
    ip.magic("macro test 1-3")
    nt.assert_equal(ip.user_ns["test"].value, "\n".join(cmds)+"\n")
    
    # List macros.
    assert "test" in ip.magic("macro")


@dec.skip_without('sqlite3')
def test_macro_run():
    """Test that we can run a multi-line macro successfully."""
    ip = get_ipython()
    ip.history_manager.reset()
    cmds = ["a=10", "a+=1", py3compat.doctest_refactor_print("print a"),
                                                            "%macro test 2-3"]
    for cmd in cmds:
        ip.run_cell(cmd, store_history=True)
    nt.assert_equal(ip.user_ns["test"].value,
                            py3compat.doctest_refactor_print("a+=1\nprint a\n"))
    with tt.AssertPrints("12"):
        ip.run_cell("test")
    with tt.AssertPrints("13"):
        ip.run_cell("test")


@dec.skipif_not_numpy
def test_numpy_reset_array_undec():
    "Test '%reset array' functionality"
    _ip.ex('import numpy as np')
    _ip.ex('a = np.empty(2)')
    yield (nt.assert_true, 'a' in _ip.user_ns)
    _ip.magic('reset -f array')
    yield (nt.assert_false, 'a' in _ip.user_ns)

def test_reset_out():
    "Test '%reset out' magic"
    _ip.run_cell("parrot = 'dead'", store_history=True)
    # test '%reset -f out', make an Out prompt
    _ip.run_cell("parrot", store_history=True)
    nt.assert_true('dead' in [_ip.user_ns[x] for x in '_','__','___'])
    _ip.magic('reset -f out')
    nt.assert_false('dead' in [_ip.user_ns[x] for x in '_','__','___'])
    nt.assert_true(len(_ip.user_ns['Out']) == 0)

def test_reset_in():
    "Test '%reset in' magic"
    # test '%reset -f in'
    _ip.run_cell("parrot", store_history=True)
    nt.assert_true('parrot' in [_ip.user_ns[x] for x in '_i','_ii','_iii'])
    _ip.magic('%reset -f in')
    nt.assert_false('parrot' in [_ip.user_ns[x] for x in '_i','_ii','_iii'])
    nt.assert_true(len(set(_ip.user_ns['In'])) == 1)

def test_reset_dhist():
    "Test '%reset dhist' magic"
    _ip.run_cell("tmp = [d for d in _dh]") # copy before clearing
    _ip.magic('cd ' + os.path.dirname(nt.__file__))
    _ip.magic('cd -')
    nt.assert_true(len(_ip.user_ns['_dh']) > 0)
    _ip.magic('reset -f dhist')
    nt.assert_true(len(_ip.user_ns['_dh']) == 0)
    _ip.run_cell("_dh = [d for d in tmp]") #restore

def test_reset_in_length():
    "Test that '%reset in' preserves In[] length"
    _ip.run_cell("print 'foo'")
    _ip.run_cell("reset -f in")
    nt.assert_true(len(_ip.user_ns['In']) == _ip.displayhook.prompt_count+1)

def test_time():
    _ip.magic('time None')

def test_tb_syntaxerror():
    """test %tb after a SyntaxError"""
    ip = get_ipython()
    ip.run_cell("for")
    
    # trap and validate stdout
    save_stdout = sys.stdout
    try:
        sys.stdout = StringIO()
        ip.run_cell("%tb")
        out = sys.stdout.getvalue()
    finally:
        sys.stdout = save_stdout
    # trim output, and only check the last line
    last_line = out.rstrip().splitlines()[-1].strip()
    nt.assert_equals(last_line, "SyntaxError: invalid syntax")


@py3compat.doctest_refactor_print
def doctest_time():
    """
    In [10]: %time None
    CPU times: user 0.00 s, sys: 0.00 s, total: 0.00 s
    Wall time: 0.00 s
    
    In [11]: def f(kmjy):
       ....:    %time print 2*kmjy
       
    In [12]: f(3)
    6
    CPU times: user 0.00 s, sys: 0.00 s, total: 0.00 s
    Wall time: 0.00 s
    """


def test_doctest_mode():
    "Toggle doctest_mode twice, it should be a no-op and run without error"
    _ip.magic('doctest_mode')
    _ip.magic('doctest_mode')


def test_parse_options():
    """Tests for basic options parsing in magics."""
    # These are only the most minimal of tests, more should be added later.  At
    # the very least we check that basic text/unicode calls work OK.
    m = DummyMagics(_ip)
    nt.assert_equal(m.parse_options('foo', '')[1], 'foo')
    nt.assert_equal(m.parse_options(u'foo', '')[1], u'foo')

    
def test_dirops():
    """Test various directory handling operations."""
    # curpath = lambda :os.path.splitdrive(os.getcwdu())[1].replace('\\','/')
    curpath = os.getcwdu
    startdir = os.getcwdu()
    ipdir = os.path.realpath(_ip.ipython_dir)
    try:
        _ip.magic('cd "%s"' % ipdir)
        nt.assert_equal(curpath(), ipdir)
        _ip.magic('cd -')
        nt.assert_equal(curpath(), startdir)
        _ip.magic('pushd "%s"' % ipdir)
        nt.assert_equal(curpath(), ipdir)
        _ip.magic('popd')
        nt.assert_equal(curpath(), startdir)
    finally:
        os.chdir(startdir)


def test_xmode():
    # Calling xmode three times should be a no-op
    xmode = _ip.InteractiveTB.mode
    for i in range(3):
        _ip.magic("xmode")
    nt.assert_equal(_ip.InteractiveTB.mode, xmode)
    
def test_reset_hard():
    monitor = []
    class A(object):
        def __del__(self):
            monitor.append(1)
        def __repr__(self):
            return "<A instance>"
            
    _ip.user_ns["a"] = A()
    _ip.run_cell("a")
    
    nt.assert_equal(monitor, [])
    _ip.magic("reset -f")
    nt.assert_equal(monitor, [1])
    
class TestXdel(tt.TempFileMixin):
    def test_xdel(self):
        """Test that references from %run are cleared by xdel."""
        src = ("class A(object):\n"
               "    monitor = []\n"
               "    def __del__(self):\n"
               "        self.monitor.append(1)\n"
               "a = A()\n")
        self.mktmp(src)
        # %run creates some hidden references...
        _ip.magic("run %s" % self.fname)
        # ... as does the displayhook.
        _ip.run_cell("a")
        
        monitor = _ip.user_ns["A"].monitor
        nt.assert_equal(monitor, [])
        
        _ip.magic("xdel a")
        
        # Check that a's __del__ method has been called.
        nt.assert_equal(monitor, [1])

def doctest_who():
    """doctest for %who
    
    In [1]: %reset -f
    
    In [2]: alpha = 123
    
    In [3]: beta = 'beta'
    
    In [4]: %who int
    alpha
    
    In [5]: %who str
    beta
    
    In [6]: %whos
    Variable   Type    Data/Info
    ----------------------------
    alpha      int     123
    beta       str     beta
    
    In [7]: %who_ls
    Out[7]: ['alpha', 'beta']
    """

def test_whos():
    """Check that whos is protected against objects where repr() fails."""
    class A(object):
        def __repr__(self):
            raise Exception()
    _ip.user_ns['a'] = A()
    _ip.magic("whos")

@py3compat.u_format
def doctest_precision():
    """doctest for %precision
    
    In [1]: f = get_ipython().display_formatter.formatters['text/plain']
    
    In [2]: %precision 5
    Out[2]: {u}'%.5f'
    
    In [3]: f.float_format
    Out[3]: {u}'%.5f'
    
    In [4]: %precision %e
    Out[4]: {u}'%e'
    
    In [5]: f(3.1415927)
    Out[5]: {u}'3.141593e+00'
    """

def test_psearch():
    with tt.AssertPrints("dict.fromkeys"):
        _ip.run_cell("dict.fr*?")

def test_timeit_shlex():
    """test shlex issues with timeit (#1109)"""
    _ip.ex("def f(*a,**kw): pass")
    _ip.magic('timeit -n1 "this is a bug".count(" ")')
    _ip.magic('timeit -r1 -n1 f(" ", 1)')
    _ip.magic('timeit -r1 -n1 f(" ", 1, " ", 2, " ")')
    _ip.magic('timeit -r1 -n1 ("a " + "b")')
    _ip.magic('timeit -r1 -n1 f("a " + "b")')
    _ip.magic('timeit -r1 -n1 f("a " + "b ")')


def test_timeit_arguments():
    "Test valid timeit arguments, should not cause SyntaxError (GH #1269)"
    _ip.magic("timeit ('#')")


def test_timeit_special_syntax():
    "Test %%timeit with IPython special syntax"
    from IPython.core.magic import register_line_magic

    @register_line_magic
    def lmagic(line):
        ip = get_ipython()
        ip.user_ns['lmagic_out'] = line

    # line mode test
    _ip.run_line_magic('timeit', '-n1 -r1 %lmagic my line')
    nt.assert_equal(_ip.user_ns['lmagic_out'], 'my line')
    # cell mode test
    _ip.run_cell_magic('timeit', '-n1 -r1', '%lmagic my line2')
    nt.assert_equal(_ip.user_ns['lmagic_out'], 'my line2')
    

@dec.skipif(execution.profile is None)
def test_prun_quotes():
    "Test that prun does not clobber string escapes (GH #1302)"
    _ip.magic(r"prun -q x = '\t'")
    nt.assert_equal(_ip.user_ns['x'], '\t')

def test_extension():
    tmpdir = TemporaryDirectory()
    orig_ipython_dir = _ip.ipython_dir
    try:
        _ip.ipython_dir = tmpdir.name
        nt.assert_raises(ImportError, _ip.magic, "load_ext daft_extension")
        url = os.path.join(os.path.dirname(__file__), "daft_extension.py")
        _ip.magic("install_ext %s" % url)
        _ip.user_ns.pop('arq', None)
        invalidate_caches()   # Clear import caches
        _ip.magic("load_ext daft_extension")
        tt.assert_equal(_ip.user_ns['arq'], 185)
        _ip.magic("unload_ext daft_extension")
        assert 'arq' not in _ip.user_ns
    finally:
        _ip.ipython_dir = orig_ipython_dir
        
def test_notebook_export_json():
    with TemporaryDirectory() as td:
        outfile = os.path.join(td, "nb.ipynb")
        _ip.ex(py3compat.u_format(u"u = {u}'héllo'"))
        _ip.magic("notebook -e %s" % outfile)

def test_notebook_export_py():
    with TemporaryDirectory() as td:
        outfile = os.path.join(td, "nb.py")
        _ip.ex(py3compat.u_format(u"u = {u}'héllo'"))
        _ip.magic("notebook -e %s" % outfile)

def test_notebook_reformat_py():
    with TemporaryDirectory() as td:
        infile = os.path.join(td, "nb.ipynb")
        with io.open(infile, 'w', encoding='utf-8') as f:
            current.write(nb0, f, 'json')
            
        _ip.ex(py3compat.u_format(u"u = {u}'héllo'"))
        _ip.magic("notebook -f py %s" % infile)

def test_notebook_reformat_json():
    with TemporaryDirectory() as td:
        infile = os.path.join(td, "nb.py")
        with io.open(infile, 'w', encoding='utf-8') as f:
            current.write(nb0, f, 'py')
            
        _ip.ex(py3compat.u_format(u"u = {u}'héllo'"))
        _ip.magic("notebook -f ipynb %s" % infile)
        _ip.magic("notebook -f json %s" % infile)

def test_env():
    env = _ip.magic("env")
    assert isinstance(env, dict), type(env)


class CellMagicTestCase(TestCase):

    def check_ident(self, magic):
        # Manually called, we get the result
        out = _ip.run_cell_magic(magic, 'a', 'b')
        nt.assert_equals(out, ('a','b'))
        # Via run_cell, it goes into the user's namespace via displayhook
        _ip.run_cell('%%' + magic +' c\nd')
        nt.assert_equals(_ip.user_ns['_'], ('c','d'))

    def test_cell_magic_func_deco(self):
        "Cell magic using simple decorator"
        @register_cell_magic
        def cellm(line, cell):
            return line, cell

        self.check_ident('cellm')

    def test_cell_magic_reg(self):
        "Cell magic manually registered"
        def cellm(line, cell):
            return line, cell

        _ip.register_magic_function(cellm, 'cell', 'cellm2')
        self.check_ident('cellm2')

    def test_cell_magic_class(self):
        "Cell magics declared via a class"
        @magics_class
        class MyMagics(Magics):

            @cell_magic
            def cellm3(self, line, cell):
                return line, cell

        _ip.register_magics(MyMagics)
        self.check_ident('cellm3')

    def test_cell_magic_class2(self):
        "Cell magics declared via a class, #2"
        @magics_class
        class MyMagics2(Magics):

            @cell_magic('cellm4')
            def cellm33(self, line, cell):
                return line, cell
            
        _ip.register_magics(MyMagics2)
        self.check_ident('cellm4')
        # Check that nothing is registered as 'cellm33'
        c33 = _ip.find_cell_magic('cellm33')
        nt.assert_equals(c33, None)

def test_file():
    """Basic %%file"""
    ip = get_ipython()
    with TemporaryDirectory() as td:
        fname = os.path.join(td, 'file1')
        ip.run_cell_magic("file", fname, u'\n'.join([
            'line1',
            'line2',
        ]))
        with open(fname) as f:
            s = f.read()
        nt.assert_in('line1\n', s)
        nt.assert_in('line2', s)

def test_file_unicode():
    """%%file with unicode cell"""
    ip = get_ipython()
    with TemporaryDirectory() as td:
        fname = os.path.join(td, 'file1')
        ip.run_cell_magic("file", fname, u'\n'.join([
            u'liné1',
            u'liné2',
        ]))
        with io.open(fname, encoding='utf-8') as f:
            s = f.read()
        nt.assert_in(u'liné1\n', s)
        nt.assert_in(u'liné2', s)

def test_file_amend():
    """%%file -a amends files"""
    ip = get_ipython()
    with TemporaryDirectory() as td:
        fname = os.path.join(td, 'file2')
        ip.run_cell_magic("file", fname, u'\n'.join([
            'line1',
            'line2',
        ]))
        ip.run_cell_magic("file", "-a %s" % fname, u'\n'.join([
            'line3',
            'line4',
        ]))
        with open(fname) as f:
            s = f.read()
        nt.assert_in('line1\n', s)
        nt.assert_in('line3\n', s)
        
    
def test_script_config():
    ip = get_ipython()
    ip.config.ScriptMagics.script_magics = ['whoda']
    sm = script.ScriptMagics(shell=ip)
    nt.assert_in('whoda', sm.magics['cell'])

@dec.skip_win32
def test_script_out():
    ip = get_ipython()
    ip.run_cell_magic("script", "--out output sh", "echo 'hi'")
    nt.assert_equals(ip.user_ns['output'], 'hi\n')

@dec.skip_win32
def test_script_err():
    ip = get_ipython()
    ip.run_cell_magic("script", "--err error sh", "echo 'hello' >&2")
    nt.assert_equals(ip.user_ns['error'], 'hello\n')

@dec.skip_win32
def test_script_out_err():
    ip = get_ipython()
    ip.run_cell_magic("script", "--out output --err error sh", "echo 'hi'\necho 'hello' >&2")
    nt.assert_equals(ip.user_ns['output'], 'hi\n')
    nt.assert_equals(ip.user_ns['error'], 'hello\n')

@dec.skip_win32
def test_script_bg_out():
    ip = get_ipython()
    ip.run_cell_magic("script", "--bg --out output sh", "echo 'hi'")
    nt.assert_equals(ip.user_ns['output'].read(), b'hi\n')

@dec.skip_win32
def test_script_bg_err():
    ip = get_ipython()
    ip.run_cell_magic("script", "--bg --err error sh", "echo 'hello' >&2")
    nt.assert_equals(ip.user_ns['error'].read(), b'hello\n')

@dec.skip_win32
def test_script_bg_out_err():
    ip = get_ipython()
    ip.run_cell_magic("script", "--bg --out output --err error sh", "echo 'hi'\necho 'hello' >&2")
    nt.assert_equals(ip.user_ns['output'].read(), b'hi\n')
    nt.assert_equals(ip.user_ns['error'].read(), b'hello\n')

def test_script_defaults():
    ip = get_ipython()
    for cmd in ['sh', 'bash', 'perl', 'ruby']:
        try:
            find_cmd(cmd)
        except Exception:
            pass
        else:
            nt.assert_in(cmd, ip.magics_manager.magics['cell'])


@magics_class
class FooFoo(Magics):
    """class with both %foo and %%foo magics"""
    @line_magic('foo')
    def line_foo(self, line):
        "I am line foo"
        pass

    @cell_magic("foo")
    def cell_foo(self, line, cell):
        "I am cell foo, not line foo"
        pass

def test_line_cell_info():
    """%%foo and %foo magics are distinguishable to inspect"""
    ip = get_ipython()
    ip.magics_manager.register(FooFoo)
    oinfo = ip.object_inspect('foo')
    nt.assert_true(oinfo['found'])
    nt.assert_true(oinfo['ismagic'])
    
    oinfo = ip.object_inspect('%%foo')
    nt.assert_true(oinfo['found'])
    nt.assert_true(oinfo['ismagic'])
    nt.assert_equals(oinfo['docstring'], FooFoo.cell_foo.__doc__)

    oinfo = ip.object_inspect('%foo')
    nt.assert_true(oinfo['found'])
    nt.assert_true(oinfo['ismagic'])
    nt.assert_equals(oinfo['docstring'], FooFoo.line_foo.__doc__)

def test_multiple_magics():
    ip = get_ipython()
    foo1 = FooFoo(ip)
    foo2 = FooFoo(ip)
    mm = ip.magics_manager
    mm.register(foo1)
    nt.assert_true(mm.magics['line']['foo'].im_self is foo1)
    mm.register(foo2)
    nt.assert_true(mm.magics['line']['foo'].im_self is foo2)

def test_alias_magic():
    """Test %alias_magic."""
    ip = get_ipython()
    mm = ip.magics_manager

    # Basic operation: both cell and line magics are created, if possible.
    ip.run_line_magic('alias_magic', 'timeit_alias timeit')
    nt.assert_true('timeit_alias' in mm.magics['line'])
    nt.assert_true('timeit_alias' in mm.magics['cell'])

    # --cell is specified, line magic not created.
    ip.run_line_magic('alias_magic', '--cell timeit_cell_alias timeit')
    nt.assert_false('timeit_cell_alias' in mm.magics['line'])
    nt.assert_true('timeit_cell_alias' in mm.magics['cell'])

    # Test that line alias is created successfully.
    ip.run_line_magic('alias_magic', '--line env_alias env')
    nt.assert_equal(ip.run_line_magic('env', ''),
                    ip.run_line_magic('env_alias', ''))
