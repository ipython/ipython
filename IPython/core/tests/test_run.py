# encoding: utf-8
"""Tests for code execution (%run and related), which is particularly tricky.

Because of how %run manages namespaces, and the fact that we are trying here to
verify subtle object deletion and reference counting issues, the %run tests
will be kept in this separate file.  This makes it easier to aggregate in one
place the tricks needed to handle it; most other magics are much easier to test
and we do so in a common test_magic file.
"""
from __future__ import absolute_import

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import sys
import tempfile

import nose.tools as nt
from nose import SkipTest

from IPython.testing import decorators as dec
from IPython.testing import tools as tt
from IPython.utils import py3compat

#-----------------------------------------------------------------------------
# Test functions begin
#-----------------------------------------------------------------------------

def doctest_refbug():
    """Very nasty problem with references held by multiple runs of a script.
    See: https://github.com/ipython/ipython/issues/141

    In [1]: _ip.clear_main_mod_cache()
    # random

    In [2]: %run refbug

    In [3]: call_f()
    lowercased: hello

    In [4]: %run refbug

    In [5]: call_f()
    lowercased: hello
    lowercased: hello
    """


def doctest_run_builtins():
    r"""Check that %run doesn't damage __builtins__.

    In [1]: import tempfile

    In [2]: bid1 = id(__builtins__)

    In [3]: fname = tempfile.mkstemp('.py')[1]

    In [3]: f = open(fname,'w')

    In [4]: dummy= f.write('pass\n')

    In [5]: f.flush()

    In [6]: t1 = type(__builtins__)

    In [7]: %run $fname

    In [7]: f.close()

    In [8]: bid2 = id(__builtins__)

    In [9]: t2 = type(__builtins__)

    In [10]: t1 == t2
    Out[10]: True

    In [10]: bid1 == bid2
    Out[10]: True

    In [12]: try:
       ....:     os.unlink(fname)
       ....: except:
       ....:     pass
       ....:
    """


def doctest_run_option_parser():
    r"""Test option parser in %run.

    In [1]: %run print_argv.py
    []

    In [2]: %run print_argv.py print*.py
    ['print_argv.py']

    In [3]: %run print_argv.py print\\*.py
    ['print*.py']

    In [4]: %run print_argv.py 'print*.py'
    ['print_argv.py']

    In [5]: %run -G print_argv.py print*.py
    ['print*.py']

    """


@py3compat.doctest_refactor_print
def doctest_reset_del():
    """Test that resetting doesn't cause errors in __del__ methods.

    In [2]: class A(object):
       ...:     def __del__(self):
       ...:         print str("Hi")
       ...:

    In [3]: a = A()

    In [4]: get_ipython().reset()
    Hi

    In [5]: 1+1
    Out[5]: 2
    """

# For some tests, it will be handy to organize them in a class with a common
# setup that makes a temp file

class TestMagicRunPass(tt.TempFileMixin):

    def setup(self):
        """Make a valid python temp file."""
        self.mktmp('pass\n')
        
    def run_tmpfile(self):
        _ip = get_ipython()
        # This fails on Windows if self.tmpfile.name has spaces or "~" in it.
        # See below and ticket https://bugs.launchpad.net/bugs/366353
        _ip.magic('run %s' % self.fname)
        
    def run_tmpfile_p(self):
        _ip = get_ipython()
        # This fails on Windows if self.tmpfile.name has spaces or "~" in it.
        # See below and ticket https://bugs.launchpad.net/bugs/366353
        _ip.magic('run -p %s' % self.fname)

    def test_builtins_id(self):
        """Check that %run doesn't damage __builtins__ """
        _ip = get_ipython()
        # Test that the id of __builtins__ is not modified by %run
        bid1 = id(_ip.user_ns['__builtins__'])
        self.run_tmpfile()
        bid2 = id(_ip.user_ns['__builtins__'])
        nt.assert_equal(bid1, bid2)

    def test_builtins_type(self):
        """Check that the type of __builtins__ doesn't change with %run.

        However, the above could pass if __builtins__ was already modified to
        be a dict (it should be a module) by a previous use of %run.  So we
        also check explicitly that it really is a module:
        """
        _ip = get_ipython()
        self.run_tmpfile()
        nt.assert_equal(type(_ip.user_ns['__builtins__']),type(sys))

    def test_prompts(self):
        """Test that prompts correctly generate after %run"""
        self.run_tmpfile()
        _ip = get_ipython()
        p2 = _ip.prompt_manager.render('in2').strip()
        nt.assert_equal(p2[:3], '...')
        
    def test_run_profile( self ):
        """Test that the option -p, which invokes the profiler, do not
        crash by invoking execfile"""
        _ip = get_ipython()
        self.run_tmpfile_p()


class TestMagicRunSimple(tt.TempFileMixin):

    def test_simpledef(self):
        """Test that simple class definitions work."""
        src = ("class foo: pass\n"
               "def f(): return foo()")
        self.mktmp(src)
        _ip.magic('run %s' % self.fname)
        _ip.run_cell('t = isinstance(f(), foo)')
        nt.assert_true(_ip.user_ns['t'])

    def test_obj_del(self):
        """Test that object's __del__ methods are called on exit."""
        if sys.platform == 'win32':
            try:
                import win32api
            except ImportError:
                raise SkipTest("Test requires pywin32")
        src = ("class A(object):\n"
               "    def __del__(self):\n"
               "        print 'object A deleted'\n"
               "a = A()\n")
        self.mktmp(py3compat.doctest_refactor_print(src))
        if dec.module_not_available('sqlite3'):
            err = 'WARNING: IPython History requires SQLite, your history will not be saved\n'
        else:
            err = None
        tt.ipexec_validate(self.fname, 'object A deleted', err)
    
    @dec.skip_known_failure 
    def test_aggressive_namespace_cleanup(self):
        """Test that namespace cleanup is not too aggressive GH-238

        Returning from another run magic deletes the namespace"""
        # see ticket https://github.com/ipython/ipython/issues/238
        class secondtmp(tt.TempFileMixin): pass
        empty = secondtmp()
        empty.mktmp('')
        src = ("ip = get_ipython()\n"
               "for i in range(5):\n"
               "   try:\n"
               "       ip.magic('run %s')\n"
               "   except NameError as e:\n"
               "       print i;break\n" % empty.fname)
        self.mktmp(py3compat.doctest_refactor_print(src))
        _ip.magic('run %s' % self.fname)
        _ip.run_cell('ip == get_ipython()')
        nt.assert_equal(_ip.user_ns['i'], 5)

    @dec.skip_win32
    def test_tclass(self):
        mydir = os.path.dirname(__file__)
        tc = os.path.join(mydir, 'tclass')
        src = ("%%run '%s' C-first\n"
               "%%run '%s' C-second\n"
               "%%run '%s' C-third\n") % (tc, tc, tc)
        self.mktmp(src, '.ipy')
        out = """\
ARGV 1-: ['C-first']
ARGV 1-: ['C-second']
tclass.py: deleting object: C-first
ARGV 1-: ['C-third']
tclass.py: deleting object: C-second
tclass.py: deleting object: C-third
"""
        if dec.module_not_available('sqlite3'):
            err = 'WARNING: IPython History requires SQLite, your history will not be saved\n'
        else:
            err = None
        tt.ipexec_validate(self.fname, out, err)

    def test_run_i_after_reset(self):
        """Check that %run -i still works after %reset (gh-693)"""
        src = "yy = zz\n"
        self.mktmp(src)
        _ip.run_cell("zz = 23")
        _ip.magic('run -i %s' % self.fname)
        nt.assert_equal(_ip.user_ns['yy'], 23)
        _ip.magic('reset -f')
        _ip.run_cell("zz = 23")
        _ip.magic('run -i %s' % self.fname)
        nt.assert_equal(_ip.user_ns['yy'], 23)
    
    def test_unicode(self):
        """Check that files in odd encodings are accepted."""
        mydir = os.path.dirname(__file__)
        na = os.path.join(mydir, 'nonascii.py')
        _ip.magic('run "%s"' % na)
        nt.assert_equal(_ip.user_ns['u'], u'Ўт№Ф')
