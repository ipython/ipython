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

import functools
import os
import random
import sys
import tempfile
import textwrap
import unittest

import nose.tools as nt
from nose import SkipTest

from IPython.testing import decorators as dec
from IPython.testing import tools as tt
from IPython.utils import py3compat
from IPython.utils.tempdir import TemporaryDirectory
from IPython.core import debugger

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

    In [3]: %run -G print_argv.py print*.py
    ['print*.py']

    """


@dec.skip_win32
def doctest_run_option_parser_for_posix():
    r"""Test option parser in %run (Linux/OSX specific).

    You need double quote to escape glob in POSIX systems:

    In [1]: %run print_argv.py print\\*.py
    ['print*.py']

    You can't use quote to escape glob in POSIX systems:

    In [2]: %run print_argv.py 'print*.py'
    ['print_argv.py']

    """


@dec.skip_if_not_win32
def doctest_run_option_parser_for_windows():
    r"""Test option parser in %run (Windows specific).

    In Windows, you can't escape ``*` `by backslash:

    In [1]: %run print_argv.py print\\*.py
    ['print\\*.py']

    You can use quote to escape glob:

    In [2]: %run print_argv.py 'print*.py'
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
    
    def test_aggressive_namespace_cleanup(self):
        """Test that namespace cleanup is not too aggressive GH-238

        Returning from another run magic deletes the namespace"""
        # see ticket https://github.com/ipython/ipython/issues/238
        class secondtmp(tt.TempFileMixin): pass
        empty = secondtmp()
        empty.mktmp('')
        # On Windows, the filename will have \users in it, so we need to use the
        # repr so that the \u becomes \\u.
        src = ("ip = get_ipython()\n"
               "for i in range(5):\n"
               "   try:\n"
               "       ip.magic(%r)\n"
               "   except NameError as e:\n"
               "       print(i)\n"
               "       break\n" % ('run ' + empty.fname))
        self.mktmp(src)
        _ip.magic('run %s' % self.fname)
        _ip.run_cell('ip == get_ipython()')
        nt.assert_equal(_ip.user_ns['i'], 4)
    
    def test_run_second(self):
        """Test that running a second file doesn't clobber the first, gh-3547
        """
        self.mktmp("avar = 1\n"
                   "def afunc():\n"
                   "  return avar\n")

        empty = tt.TempFileMixin()
        empty.mktmp("")
        
        _ip.magic('run %s' % self.fname)
        _ip.magic('run %s' % empty.fname)
        nt.assert_equal(_ip.user_ns['afunc'](), 1)

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

    def test_run_py_file_attribute(self):
        """Test handling of `__file__` attribute in `%run <file>.py`."""
        src = "t = __file__\n"
        self.mktmp(src)
        _missing = object()
        file1 = _ip.user_ns.get('__file__', _missing)
        _ip.magic('run %s' % self.fname)
        file2 = _ip.user_ns.get('__file__', _missing)

        # Check that __file__ was equal to the filename in the script's
        # namespace.
        nt.assert_equal(_ip.user_ns['t'], self.fname)

        # Check that __file__ was not leaked back into user_ns.
        nt.assert_equal(file1, file2)

    def test_run_ipy_file_attribute(self):
        """Test handling of `__file__` attribute in `%run <file.ipy>`."""
        src = "t = __file__\n"
        self.mktmp(src, ext='.ipy')
        _missing = object()
        file1 = _ip.user_ns.get('__file__', _missing)
        _ip.magic('run %s' % self.fname)
        file2 = _ip.user_ns.get('__file__', _missing)

        # Check that __file__ was equal to the filename in the script's
        # namespace.
        nt.assert_equal(_ip.user_ns['t'], self.fname)

        # Check that __file__ was not leaked back into user_ns.
        nt.assert_equal(file1, file2)

    def test_run_formatting(self):
        """ Test that %run -t -N<N> does not raise a TypeError for N > 1."""
        src = "pass"
        self.mktmp(src)
        _ip.magic('run -t -N 1 %s' % self.fname)
        _ip.magic('run -t -N 10 %s' % self.fname)


class TestMagicRunWithPackage(unittest.TestCase):

    def writefile(self, name, content):
        path = os.path.join(self.tempdir.name, name)
        d = os.path.dirname(path)
        if not os.path.isdir(d):
            os.makedirs(d)
        with open(path, 'w') as f:
            f.write(textwrap.dedent(content))

    def setUp(self):
        self.package = package = 'tmp{0}'.format(repr(random.random())[2:])
        """Temporary valid python package name."""

        self.value = int(random.random() * 10000)

        self.tempdir = TemporaryDirectory()
        self.__orig_cwd = os.getcwdu()
        sys.path.insert(0, self.tempdir.name)

        self.writefile(os.path.join(package, '__init__.py'), '')
        self.writefile(os.path.join(package, 'sub.py'), """
        x = {0!r}
        """.format(self.value))
        self.writefile(os.path.join(package, 'relative.py'), """
        from .sub import x
        """)
        self.writefile(os.path.join(package, 'absolute.py'), """
        from {0}.sub import x
        """.format(package))

    def tearDown(self):
        os.chdir(self.__orig_cwd)
        sys.path[:] = [p for p in sys.path if p != self.tempdir.name]
        self.tempdir.cleanup()

    def check_run_submodule(self, submodule, opts=''):
        _ip.magic('run {2} -m {0}.{1}'.format(self.package, submodule, opts))
        self.assertEqual(_ip.user_ns['x'], self.value,
                         'Variable `x` is not loaded from module `{0}`.'
                         .format(submodule))

    def test_run_submodule_with_absolute_import(self):
        self.check_run_submodule('absolute')

    def test_run_submodule_with_relative_import(self):
        """Run submodule that has a relative import statement (#2727)."""
        self.check_run_submodule('relative')

    def test_prun_submodule_with_absolute_import(self):
        self.check_run_submodule('absolute', '-p')

    def test_prun_submodule_with_relative_import(self):
        self.check_run_submodule('relative', '-p')

    def with_fake_debugger(func):
        @functools.wraps(func)
        def wrapper(*args, **kwds):
            with tt.monkeypatch(debugger.Pdb, 'run', staticmethod(eval)):
                return func(*args, **kwds)
        return wrapper

    @with_fake_debugger
    def test_debug_run_submodule_with_absolute_import(self):
        self.check_run_submodule('absolute', '-d')

    @with_fake_debugger
    def test_debug_run_submodule_with_relative_import(self):
        self.check_run_submodule('relative', '-d')
