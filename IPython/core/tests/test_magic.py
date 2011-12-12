"""Tests for various magic functions.

Needs to be run by nose (to make ipython session available).
"""
from __future__ import absolute_import

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os

import nose.tools as nt

from IPython.testing import decorators as dec
from IPython.testing import tools as tt
from IPython.utils import py3compat

#-----------------------------------------------------------------------------
# Test functions begin
#-----------------------------------------------------------------------------

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
    opts = ip.parse_options('-f %s' % path,'f:')[0]
    # argv splitting is os-dependent
    if os.name == 'posix':
        expected = 'c:x'
    else:
        expected = path
    nt.assert_equals(opts['f'], expected)


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

    
# XXX failing for now, until we get clearcmd out of quarantine.  But we should
# fix this and revert the skip to happen only if numpy is not around.
#@dec.skipif_not_numpy
@dec.skip_known_failure
def test_numpy_clear_array_undec():
    from IPython.extensions import clearcmd

    _ip.ex('import numpy as np')
    _ip.ex('a = np.empty(2)')
    yield (nt.assert_true, 'a' in _ip.user_ns)
    _ip.magic('clear array')
    yield (nt.assert_false, 'a' in _ip.user_ns)
    

def test_time():
    _ip.magic('time None')


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
    nt.assert_equal(_ip.parse_options('foo', '')[1], 'foo')
    nt.assert_equal(_ip.parse_options(u'foo', '')[1], u'foo')

    
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
    _ip.magic_reset("-f")
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

@py3compat.u_format
def doctest_precision():
    """doctest for %precision
    
    In [1]: f = get_ipython().shell.display_formatter.formatters['text/plain']
    
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
