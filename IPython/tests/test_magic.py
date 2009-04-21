"""Tests for various magic functions.

Needs to be run by nose (to make ipython session available).
"""

# Standard library imports
import os
import sys

# Third-party imports
import nose.tools as nt

# From our own code
from IPython.testing import decorators as dec
#-----------------------------------------------------------------------------
# Test functions begin

def test_rehashx():
    # clear up everything
    _ip.IP.alias_table.clear()
    del _ip.db['syscmdlist']
    
    _ip.magic('rehashx')
    # Practically ALL ipython development systems will have more than 10 aliases

    assert len(_ip.IP.alias_table) > 10
    for key, val in _ip.IP.alias_table.items():
        # we must strip dots from alias names
        assert '.' not in key

    # rehashx must fill up syscmdlist
    scoms = _ip.db['syscmdlist']
    assert len(scoms) > 10


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


def doctest_hist_f():
    """Test %hist -f with temporary filename.

    In [9]: import tempfile

    In [10]: tfile = tempfile.mktemp('.py','tmp-ipython-')

    In [11]: %history -n -f $tfile 3
    """

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

def test_run_builtins():
    """Check that %run doesn't damage __builtins__ """
    import sys
    import tempfile
    import types

    # Make an empty file and put 'pass' in it
    f = tempfile.NamedTemporaryFile()
    f.write('pass\n')
    f.flush()

    # Our first test is that the id of __builtins__ is not modified by %run
    bid1 = id(__builtins__)
    _ip.magic('run %s' % f.name)
    bid2 = id(__builtins__)
    yield nt.assert_equals,bid1,bid2
    # However, the above could pass if __builtins__ was already modified to be
    # a dict (it should be a module) by a previous use of %run.  So we also
    # check explicitly that it really is a module:
    yield nt.assert_equals,type(__builtins__),type(sys)
    

def doctest_hist_r():
    """Test %hist -r

    XXX - This test is not recording the output correctly.  Not sure why...

    In [6]: x=1

    In [7]: hist -n -r 2
    x=1  # random
    hist -n -r 2  # random
    """


def test_obj_del():
    """Test that object's __del__ methods are called on exit."""
    test_dir = os.path.dirname(__file__)
    del_file = os.path.join(test_dir,'obj_del.py')
    out = _ip.IP.getoutput('ipython %s' % del_file)
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
    _ip.ex('import numpy as np')
    _ip.ex('a = np.empty(2)')
    
    yield nt.assert_true,'a' in _ip.user_ns
    _ip.magic('clear array')
    yield nt.assert_false,'a' in _ip.user_ns
    

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
