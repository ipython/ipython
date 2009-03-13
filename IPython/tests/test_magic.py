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

    In [11]: run tclass

    In [12]: isinstance(f(),foo)
    Out[12]: True
    """

    
def doctest_run_ns2():
    """Classes declared %run scripts must be instantiable afterwards.

    In [3]: run tclass.py

    In [4]: run tclass first_pass

    In [5]: run tclass second_pass
    Deleting object: first_pass
    """


def doctest_hist_f():
    """Test %hist -f with temporary filename.

    In [9]: import tempfile

    In [10]: tfile = tempfile.mktemp('.py','tmp-ipython-')

    In [11]: %history -n -f $tfile 3
    """


def doctest_hist_r():
    """Test %hist -r

    XXX - This test is not recording the output correctly.  Not sure why...

    In [6]: x=1

    In [7]: hist -n -r 2
    x=1  # random
    hist -n -r 2  # random
    """


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

