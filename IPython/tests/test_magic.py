"""Tests for various magic functions.

Needs to be run by nose (to make ipython session available).
"""

import os
import sys
import tempfile
import types

import nose.tools as nt

from IPython.platutils import find_cmd, get_long_path_name
from IPython.testing import decorators as dec
from IPython.testing import tools as tt

#-----------------------------------------------------------------------------
# Test functions begin

def test_rehashx():
    # clear up everything
    _ip.IP.alias_table.clear()
    del _ip.db['syscmdlist']
    
    _ip.magic('rehashx')
    # Practically ALL ipython development systems will have more than 10 aliases

    yield (nt.assert_true, len(_ip.IP.alias_table) > 10)
    for key, val in _ip.IP.alias_table.items():
        # we must strip dots from alias names
        nt.assert_true('.' not in key)

    # rehashx must fill up syscmdlist
    scoms = _ip.db['syscmdlist']
    yield (nt.assert_true, len(scoms) > 10)


def doctest_hist_f():
    """Test %hist -f with temporary filename.

    In [9]: import tempfile

    In [10]: tfile = tempfile.mktemp('.py','tmp-ipython-')

    In [11]: %hist -n -f $tfile 3

    """


def doctest_hist_r():
    """Test %hist -r

    XXX - This test is not recording the output correctly.  Not sure why...

    In [20]: 'hist' in _ip.IP.lsmagic()
    Out[20]: True

    In [6]: x=1

    In [7]: %hist -n -r 2
    x=1  # random
    hist -n -r 2  # random
    """

# This test is known to fail on win32.
# See ticket https://bugs.launchpad.net/bugs/366334
def test_obj_del():
    """Test that object's __del__ methods are called on exit."""
    test_dir = os.path.dirname(__file__)
    del_file = os.path.join(test_dir,'obj_del.py')
    ipython_cmd = find_cmd('ipython')
    out = _ip.IP.getoutput('%s %s' % (ipython_cmd, del_file))
    nt.assert_equals(out,'obj_del.py: object A deleted')


def test_shist():
    # Simple tests of ShadowHist class - test generator.
    import os, shutil, tempfile

    from IPython.Extensions import pickleshare
    from IPython.history import ShadowHist
    
    tfile = tempfile.mktemp('','tmp-ipython-')
    
    db = pickleshare.PickleShareDB(tfile)
    s = ShadowHist(db)
    s.add('hello')
    s.add('world')
    s.add('hello')
    s.add('hello')
    s.add('karhu')

    yield nt.assert_equals,s.all(),[(1, 'hello'), (2, 'world'), (3, 'karhu')]
    
    yield nt.assert_equal,s.get(2),'world'
    
    shutil.rmtree(tfile)
    
@dec.skipif_not_numpy
def test_numpy_clear_array_undec():
    from IPython.Extensions import clearcmd

    _ip.ex('import numpy as np')
    _ip.ex('a = np.empty(2)')
    yield (nt.assert_true, 'a' in _ip.user_ns)
    _ip.magic('clear array')
    yield (nt.assert_false, 'a' in _ip.user_ns)
    

@dec.skip()
def test_fail_dec(*a,**k):
    yield nt.assert_true, False

@dec.skip('This one shouldn not run')
def test_fail_dec2(*a,**k):
    yield nt.assert_true, False

@dec.skipknownfailure
def test_fail_dec3(*a,**k):
    yield nt.assert_true, False


def doctest_refbug():
    """Very nasty problem with references held by multiple runs of a script.
    See: https://bugs.launchpad.net/ipython/+bug/269966

    In [1]: _ip.IP.clear_main_mod_cache()
    
    In [2]: run refbug

    In [3]: call_f()
    lowercased: hello

    In [4]: run refbug

    In [5]: call_f()
    lowercased: hello
    lowercased: hello
    """

#-----------------------------------------------------------------------------
# Tests for %run
#-----------------------------------------------------------------------------

# %run is critical enough that it's a good idea to have a solid collection of
# tests for it, some as doctests and some as normal tests.

def doctest_run_ns():
    """Classes declared %run scripts must be instantiable afterwards.

    In [11]: run tclass foo

    In [12]: isinstance(f(),foo)
    Out[12]: True
    """

    
def doctest_run_ns2():
    """Classes declared %run scripts must be instantiable afterwards.

    In [4]: run tclass C-first_pass

    In [5]: run tclass C-second_pass
    tclass.py: deleting object: C-first_pass
    """

@dec.skip_win32
def doctest_run_builtins():
    """Check that %run doesn't damage __builtins__ via a doctest.

    This is similar to the test_run_builtins, but I want *both* forms of the
    test to catch any possible glitches in our testing machinery, since that
    modifies %run somewhat.  So for this, we have both a normal test (below)
    and a doctest (this one).

    In [1]: import tempfile

    In [2]: bid1 = id(__builtins__)

    In [3]: f = tempfile.NamedTemporaryFile()

    In [4]: f.write('pass\\n')

    In [5]: f.flush()

    In [6]: print 'B1:',type(__builtins__)
    B1: <type 'module'>

    In [7]: %run $f.name

    In [8]: bid2 = id(__builtins__)

    In [9]: print 'B2:',type(__builtins__)
    B2: <type 'module'>

    In [10]: bid1 == bid2
    Out[10]: True
    """

# For some tests, it will be handy to organize them in a class with a common
# setup that makes a temp file

class TestMagicRun(object):

    def setup(self):
        """Make a valid python temp file."""
        f = tempfile.NamedTemporaryFile()
        f.write('pass\n')
        f.flush()
        self.tmpfile = f

    def run_tmpfile(self):
        # This fails on Windows if self.tmpfile.name has spaces or "~" in it.
        # See below and ticket https://bugs.launchpad.net/bugs/366353
        _ip.magic('run %s' % self.tmpfile.name)

    # See https://bugs.launchpad.net/bugs/366353
    @dec.skip_if_not_win32
    def test_run_tempfile_path(self):
        tt.assert_equals(True,False,"%run doesn't work with tempfile paths on win32.")

    # See https://bugs.launchpad.net/bugs/366353
    @dec.skip_win32
    def test_builtins_id(self):
        """Check that %run doesn't damage __builtins__ """

        # Test that the id of __builtins__ is not modified by %run
        bid1 = id(_ip.user_ns['__builtins__'])
        self.run_tmpfile()
        bid2 = id(_ip.user_ns['__builtins__'])
        tt.assert_equals(bid1, bid2)

    # See https://bugs.launchpad.net/bugs/366353
    @dec.skip_win32
    def test_builtins_type(self):
        """Check that the type of __builtins__ doesn't change with %run.
        
        However, the above could pass if __builtins__ was already modified to
        be a dict (it should be a module) by a previous use of %run.  So we
        also check explicitly that it really is a module:
        """
        self.run_tmpfile()
        tt.assert_equals(type(_ip.user_ns['__builtins__']),type(sys))

    # See https://bugs.launchpad.net/bugs/366353
    @dec.skip_win32
    def test_prompts(self):
        """Test that prompts correctly generate after %run"""
        self.run_tmpfile()
        p2 = str(_ip.IP.outputcache.prompt2).strip()
        nt.assert_equals(p2[:3], '...')

    def teardown(self):
        self.tmpfile.close()

# Multiple tests for clipboard pasting
def test_paste():

    def paste(txt):
        hooks.clipboard_get = lambda : txt
        _ip.magic('paste')

    # Inject fake clipboard hook but save original so we can restore it later
    hooks = _ip.IP.hooks
    user_ns = _ip.user_ns
    original_clip = hooks.clipboard_get

    try:
        # Run tests with fake clipboard function
        user_ns.pop('x', None)
        paste('x=1')
        yield (nt.assert_equal, user_ns['x'], 1)

        user_ns.pop('x', None)
        paste('>>> x=2')
        yield (nt.assert_equal, user_ns['x'], 2)

        paste("""
        >>> x = [1,2,3]
        >>> y = []
        >>> for i in x:
        ...     y.append(i**2)
        ...
        """)
        yield (nt.assert_equal, user_ns['x'], [1,2,3])
        yield (nt.assert_equal, user_ns['y'], [1,4,9])

    finally:
        # Restore original hook
        hooks.clipboard_get = original_clip
