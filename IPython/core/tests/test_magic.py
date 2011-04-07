"""Tests for various magic functions.

Needs to be run by nose (to make ipython session available).
"""
from __future__ import absolute_import

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import sys
import tempfile
import types
from cStringIO import StringIO

import nose.tools as nt

from IPython.utils.path import get_long_path_name
from IPython.testing import decorators as dec
from IPython.testing import tools as tt

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

    
def doctest_hist_f():
    """Test %hist -f with temporary filename.

    In [9]: import tempfile

    In [10]: tfile = tempfile.mktemp('.py','tmp-ipython-')

    In [11]: %hist -nl -f $tfile 3

    In [13]: import os; os.unlink(tfile)
    """


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

def doctest_hist_op():
    """Test %hist -op

    In [1]: class b:
       ...:         pass
       ...: 

    In [2]: class s(b):
       ...:         def __str__(self):
       ...:             return 's'
       ...: 

    In [3]: 

    In [4]: class r(b):
       ...:         def __repr__(self):
       ...:             return 'r'
       ...: 

    In [5]: class sr(s,r): pass
       ...: 

    In [6]: 

    In [7]: bb=b()

    In [8]: ss=s()

    In [9]: rr=r()

    In [10]: ssrr=sr()

    In [11]: bb
    Out[11]: <...b instance at ...>

    In [12]: ss
    Out[12]: <...s instance at ...>

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
    >>> bb
    <...b instance at ...>
    >>> ss
    <...s instance at ...>
    >>> 
    """
  
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

def test_macro_run():
    """Test that we can run a multi-line macro successfully."""
    ip = get_ipython()
    ip.history_manager.reset()
    cmds = ["a=10", "a+=1", "print a", "%macro test 2-3"]
    for cmd in cmds:
        ip.run_cell(cmd)
    nt.assert_equal(ip.user_ns["test"].value, "a+=1\nprint a\n")
    original_stdout = sys.stdout
    new_stdout = StringIO()
    sys.stdout = new_stdout
    try:
        ip.run_cell("test")
        nt.assert_true("12" in new_stdout.getvalue())
        ip.run_cell("test")
        nt.assert_true("13" in new_stdout.getvalue())
    finally:
        sys.stdout = original_stdout
        new_stdout.close()

    
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
    

# Multiple tests for clipboard pasting
@dec.parametric
def test_paste():
    _ip = get_ipython()
    def paste(txt, flags='-q'):
        """Paste input text, by default in quiet mode"""
        hooks.clipboard_get = lambda : txt
        _ip.magic('paste '+flags)

    # Inject fake clipboard hook but save original so we can restore it later
    hooks = _ip.hooks
    user_ns = _ip.user_ns
    original_clip = hooks.clipboard_get

    try:
        # This try/except with an emtpy except clause is here only because
        # try/yield/finally is invalid syntax in Python 2.4.  This will be
        # removed when we drop 2.4-compatibility, and the emtpy except below
        # will be changed to a finally.

        # Run tests with fake clipboard function
        user_ns.pop('x', None)
        paste('x=1')
        yield nt.assert_equal(user_ns['x'], 1)

        user_ns.pop('x', None)
        paste('>>> x=2')
        yield nt.assert_equal(user_ns['x'], 2)

        paste("""
        >>> x = [1,2,3]
        >>> y = []
        >>> for i in x:
        ...     y.append(i**2)
        ...
        """)
        yield nt.assert_equal(user_ns['x'], [1,2,3])
        yield nt.assert_equal(user_ns['y'], [1,4,9])

        # Now, test that paste -r works
        user_ns.pop('x', None)
        yield nt.assert_false('x' in user_ns)
        _ip.magic('paste -r')
        yield nt.assert_equal(user_ns['x'], [1,2,3])

        # Also test paste echoing, by temporarily faking the writer
        w = StringIO()
        writer = _ip.write
        _ip.write = w.write
        code = """
        a = 100
        b = 200"""
        try:
            paste(code,'')
            out = w.getvalue()
        finally:
            _ip.write = writer
        yield nt.assert_equal(user_ns['a'], 100)
        yield nt.assert_equal(user_ns['b'], 200)
        yield nt.assert_equal(out, code+"\n## -- End pasted text --\n")
        
    finally:
        # This should be in a finally clause, instead of the bare except above.
        # Restore original hook
        hooks.clipboard_get = original_clip


def test_time():
    _ip.magic('time None')


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
    curpath = lambda :os.path.splitdrive(os.getcwdu())[1].replace('\\','/')

    startdir = os.getcwdu()
    ipdir = _ip.ipython_dir
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


def check_cpaste(code, should_fail=False):
    """Execute code via 'cpaste' and ensure it was executed, unless
    should_fail is set.
    """
    _ip.user_ns['code_ran'] = False

    src = StringIO()
    src.write('\n')
    src.write(code)
    src.write('\n--\n')
    src.seek(0)

    stdin_save = sys.stdin
    sys.stdin = src
    
    try:
        _ip.magic('cpaste')
    except:
        if not should_fail:
            raise AssertionError("Failure not expected : '%s'" %
                                 code)
    else:
        assert _ip.user_ns['code_ran']
        if should_fail:
            raise AssertionError("Failure expected : '%s'" % code)
    finally:
        sys.stdin = stdin_save


def test_cpaste():
    """Test cpaste magic"""

    def run():
        """Marker function: sets a flag when executed.
        """
        _ip.user_ns['code_ran'] = True
        return 'run' # return string so '+ run()' doesn't result in success

    tests = {'pass': ["> > > run()",
                      ">>> > run()",
                      "+++ run()",
                      "++ run()",
                      "  >>> run()"],

             'fail': ["+ + run()",
                      " ++ run()"]}

    _ip.user_ns['run'] = run

    for code in tests['pass']:
        check_cpaste(code)

    for code in tests['fail']:
        check_cpaste(code, should_fail=True)

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
    _ip.magic_reset("-hf")
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

def doctest_precision():
    """doctest for %precision
    
    In [1]: f = get_ipython().shell.display_formatter.formatters['text/plain']
    
    In [2]: %precision 5
    Out[2]: '%.5f'
    
    In [3]: f.float_format
    Out[3]: '%.5f'
    
    In [4]: %precision %e
    Out[4]: '%e'
    
    In [5]: f(3.1415927)
    Out[5]: '3.141593e+00'
    """

