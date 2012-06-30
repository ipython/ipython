# -*- coding: utf-8 -*-
"""IPython Test Suite Runner.

This module provides a main entry point to a user script to test IPython
itself from the command line. There are two ways of running this script:

1. With the syntax `iptest all`.  This runs our entire test suite by
   calling this script (with different arguments) recursively.  This
   causes modules and package to be tested in different processes, using nose
   or trial where appropriate.
2. With the regular nose syntax, like `iptest -vvs IPython`.  In this form
   the script simply calls nose, but with special command line flags and
   plugins loaded.

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2009-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Stdlib
import glob
import os
import os.path as path
import signal
import sys
import subprocess
import tempfile
import time
import warnings

# Note: monkeypatch!
# We need to monkeypatch a small problem in nose itself first, before importing
# it for actual use.  This should get into nose upstream, but its release cycle
# is slow and we need it for our parametric tests to work correctly.
from IPython.testing import nosepatch

# Monkeypatch extra assert methods into nose.tools if they're not already there.
# This can be dropped once we no longer test on Python 2.6
from IPython.testing import nose_assert_methods

# Now, proceed to import nose itself
import nose.plugins.builtin
from nose.plugins.xunit import Xunit
from nose import SkipTest
from nose.core import TestProgram

# Our own imports
from IPython.utils import py3compat
from IPython.utils.importstring import import_item
from IPython.utils.path import get_ipython_module_path, get_ipython_package_dir
from IPython.utils.process import find_cmd, pycmd2argv
from IPython.utils.sysinfo import sys_info
from IPython.utils.warn import warn

from IPython.testing import globalipapp
from IPython.testing.plugin.ipdoctest import IPythonDoctest
from IPython.external.decorators import KnownFailure, knownfailureif

pjoin = path.join


#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------


#-----------------------------------------------------------------------------
# Warnings control
#-----------------------------------------------------------------------------

# Twisted generates annoying warnings with Python 2.6, as will do other code
# that imports 'sets' as of today
warnings.filterwarnings('ignore', 'the sets module is deprecated',
                        DeprecationWarning )

# This one also comes from Twisted
warnings.filterwarnings('ignore', 'the sha module is deprecated',
                        DeprecationWarning)

# Wx on Fedora11 spits these out
warnings.filterwarnings('ignore', 'wxPython/wxWidgets release number mismatch',
                        UserWarning)

# ------------------------------------------------------------------------------
# Monkeypatch Xunit to count known failures as skipped.
# ------------------------------------------------------------------------------
def monkeypatch_xunit():
    try:
        knownfailureif(True)(lambda: None)()
    except Exception as e:
        KnownFailureTest = type(e)

    def addError(self, test, err, capt=None):
        if issubclass(err[0], KnownFailureTest):
            err = (SkipTest,) + err[1:]
        return self.orig_addError(test, err, capt)

    Xunit.orig_addError = Xunit.addError
    Xunit.addError = addError

#-----------------------------------------------------------------------------
# Logic for skipping doctests
#-----------------------------------------------------------------------------
def extract_version(mod):
    return mod.__version__

def test_for(item, min_version=None, callback=extract_version):
    """Test to see if item is importable, and optionally check against a minimum
    version.

    If min_version is given, the default behavior is to check against the
    `__version__` attribute of the item, but specifying `callback` allows you to
    extract the value you are interested in. e.g::

        In [1]: import sys

        In [2]: from IPython.testing.iptest import test_for

        In [3]: test_for('sys', (2,6), callback=lambda sys: sys.version_info)
        Out[3]: True

    """
    try:
        check = import_item(item)
    except (ImportError, RuntimeError):
        # GTK reports Runtime error if it can't be initialized even if it's
        # importable.
        return False
    else:
        if min_version:
            if callback:
                # extra processing step to get version to compare
                check = callback(check)

            return check >= min_version
        else:
            return True

# Global dict where we can store information on what we have and what we don't
# have available at test run time
have = {}

have['curses'] = test_for('_curses')
have['matplotlib'] = test_for('matplotlib')
have['numpy'] = test_for('numpy')
have['pexpect'] = test_for('IPython.external.pexpect')
have['pymongo'] = test_for('pymongo')
have['pygments'] = test_for('pygments')
have['qt'] = test_for('IPython.external.qt')
have['rpy2'] = test_for('rpy2')
have['sqlite3'] = test_for('sqlite3')
have['cython'] = test_for('Cython')
have['oct2py'] = test_for('oct2py')
have['tornado'] = test_for('tornado.version_info', (2,1,0), callback=None)
have['wx'] = test_for('wx')
have['wx.aui'] = test_for('wx.aui')

if os.name == 'nt':
    min_zmq = (2,1,7)
else:
    min_zmq = (2,1,4)

def version_tuple(mod):
    "turn '2.1.9' into (2,1,9), and '2.1dev' into (2,1,999)"
    # turn 'dev' into 999, because Python3 rejects str-int comparisons
    vs = mod.__version__.replace('dev', '.999')
    tup = tuple([int(v) for v in vs.split('.') ])
    return tup

have['zmq'] = test_for('zmq', min_zmq, version_tuple)

#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------

def report():
    """Return a string with a summary report of test-related variables."""

    out = [ sys_info(), '\n']

    avail = []
    not_avail = []

    for k, is_avail in have.items():
        if is_avail:
            avail.append(k)
        else:
            not_avail.append(k)

    if avail:
        out.append('\nTools and libraries available at test time:\n')
        avail.sort()
        out.append('   ' + ' '.join(avail)+'\n')

    if not_avail:
        out.append('\nTools and libraries NOT available at test time:\n')
        not_avail.sort()
        out.append('   ' + ' '.join(not_avail)+'\n')

    return ''.join(out)


def make_exclude():
    """Make patterns of modules and packages to exclude from testing.

    For the IPythonDoctest plugin, we need to exclude certain patterns that
    cause testing problems.  We should strive to minimize the number of
    skipped modules, since this means untested code.

    These modules and packages will NOT get scanned by nose at all for tests.
    """
    # Simple utility to make IPython paths more readably, we need a lot of
    # these below
    ipjoin = lambda *paths: pjoin('IPython', *paths)

    exclusions = [ipjoin('external'),
                  ipjoin('quarantine'),
                  ipjoin('deathrow'),
                  # This guy is probably attic material
                  ipjoin('testing', 'mkdoctests'),
                  # Testing inputhook will need a lot of thought, to figure out
                  # how to have tests that don't lock up with the gui event
                  # loops in the picture
                  ipjoin('lib', 'inputhook'),
                  # Config files aren't really importable stand-alone
                  ipjoin('config', 'profile'),
                  ]
    if not have['sqlite3']:
        exclusions.append(ipjoin('core', 'tests', 'test_history'))
        exclusions.append(ipjoin('core', 'history'))
    if not have['wx']:
        exclusions.append(ipjoin('lib', 'inputhookwx'))
    
    # FIXME: temporarily disable autoreload tests, as they can produce
    # spurious failures in subsequent tests (cythonmagic).
    exclusions.append(ipjoin('extensions', 'autoreload'))
    exclusions.append(ipjoin('extensions', 'tests', 'test_autoreload'))

    # We do this unconditionally, so that the test suite doesn't import
    # gtk, changing the default encoding and masking some unicode bugs.
    exclusions.append(ipjoin('lib', 'inputhookgtk'))
    exclusions.append(ipjoin('zmq', 'gui', 'gtkembed'))

    # These have to be skipped on win32 because the use echo, rm, cd, etc.
    # See ticket https://github.com/ipython/ipython/issues/87
    if sys.platform == 'win32':
        exclusions.append(ipjoin('testing', 'plugin', 'test_exampleip'))
        exclusions.append(ipjoin('testing', 'plugin', 'dtexample'))

    if not have['pexpect']:
        exclusions.extend([ipjoin('lib', 'irunner'),
                           ipjoin('lib', 'tests', 'test_irunner'),
                           ipjoin('frontend', 'terminal', 'console'),
                           ])

    if not have['zmq']:
        exclusions.append(ipjoin('zmq'))
        exclusions.append(ipjoin('frontend', 'qt'))
        exclusions.append(ipjoin('frontend', 'html'))
        exclusions.append(ipjoin('frontend', 'consoleapp.py'))
        exclusions.append(ipjoin('frontend', 'terminal', 'console'))
        exclusions.append(ipjoin('parallel'))
    elif not have['qt'] or not have['pygments']:
        exclusions.append(ipjoin('frontend', 'qt'))

    if not have['pymongo']:
        exclusions.append(ipjoin('parallel', 'controller', 'mongodb'))
        exclusions.append(ipjoin('parallel', 'tests', 'test_mongodb'))

    if not have['matplotlib']:
        exclusions.extend([ipjoin('core', 'pylabtools'),
                           ipjoin('core', 'tests', 'test_pylabtools'),
                           ipjoin('zmq', 'pylab'),
        ])

    if not have['cython']:
        exclusions.extend([ipjoin('extensions', 'cythonmagic')])
        exclusions.extend([ipjoin('extensions', 'tests', 'test_cythonmagic')])

    if not have['oct2py']:
        exclusions.extend([ipjoin('extensions', 'octavemagic')])
        exclusions.extend([ipjoin('extensions', 'tests', 'test_octavemagic')])

    if not have['tornado']:
        exclusions.append(ipjoin('frontend', 'html'))

    if not have['rpy2'] or not have['numpy']:
        exclusions.append(ipjoin('extensions', 'rmagic'))
        exclusions.append(ipjoin('extensions', 'tests', 'test_rmagic'))

    # This is needed for the reg-exp to match on win32 in the ipdoctest plugin.
    if sys.platform == 'win32':
        exclusions = [s.replace('\\','\\\\') for s in exclusions]
    
    # check for any exclusions that don't seem to exist:
    parent, _ = os.path.split(get_ipython_package_dir())
    for exclusion in exclusions:
        if exclusion.endswith(('deathrow', 'quarantine')):
            # ignore deathrow/quarantine, which exist in dev, but not install
            continue
        fullpath = pjoin(parent, exclusion)
        if not os.path.exists(fullpath) and not glob.glob(fullpath + '.*'):
            warn("Excluding nonexistent file: %r\n" % exclusion)

    return exclusions


class IPTester(object):
    """Call that calls iptest or trial in a subprocess.
    """
    #: string, name of test runner that will be called
    runner = None
    #: list, parameters for test runner
    params = None
    #: list, arguments of system call to be made to call test runner
    call_args = None
    #: list, process ids of subprocesses we start (for cleanup)
    pids = None
    #: str, coverage xml output file
    coverage_xml = None

    def __init__(self, runner='iptest', params=None):
        """Create new test runner."""
        p = os.path
        if runner == 'iptest':
            iptest_app = get_ipython_module_path('IPython.testing.iptest')
            self.runner = pycmd2argv(iptest_app) + sys.argv[1:]
        else:
            raise Exception('Not a valid test runner: %s' % repr(runner))
        if params is None:
            params = []
        if isinstance(params, str):
            params = [params]
        self.params = params

        # Assemble call
        self.call_args = self.runner+self.params
        
        # Find the section we're testing (IPython.foo)
        for sect in self.params:
            if sect.startswith('IPython'): break
        else:
            raise ValueError("Section not found", self.params)
        
        if '--with-xunit' in self.call_args:
            
            self.call_args.append('--xunit-file')
            # FIXME: when Windows uses subprocess.call, these extra quotes are unnecessary:
            xunit_file = path.abspath(sect+'.xunit.xml')
            if sys.platform == 'win32':
                xunit_file = '"%s"' % xunit_file
            self.call_args.append(xunit_file)
        
        if '--with-xml-coverage' in self.call_args:
            self.coverage_xml = path.abspath(sect+".coverage.xml")
            self.call_args.remove('--with-xml-coverage')
            self.call_args = ["coverage", "run", "--source="+sect] + self.call_args[1:]

        # Store pids of anything we start to clean up on deletion, if possible
        # (on posix only, since win32 has no os.kill)
        self.pids = []

    if sys.platform == 'win32':
        def _run_cmd(self):
            # On Windows, use os.system instead of subprocess.call, because I
            # was having problems with subprocess and I just don't know enough
            # about win32 to debug this reliably.  Os.system may be the 'old
            # fashioned' way to do it, but it works just fine.  If someone
            # later can clean this up that's fine, as long as the tests run
            # reliably in win32.
            # What types of problems are you having. They may be related to
            # running Python in unboffered mode. BG.
            for ndx, arg in enumerate(self.call_args):
                # Enclose in quotes if necessary and legal
                if ' ' in arg and os.path.isfile(arg) and arg[0] != '"':
                    self.call_args[ndx] = '"%s"' % arg
            call_args = [py3compat.cast_unicode(x) for x in self.call_args]
            cmd = py3compat.unicode_to_str(u' '.join(call_args))
            return os.system(cmd)
    else:
        def _run_cmd(self):
            # print >> sys.stderr, '*** CMD:', ' '.join(self.call_args) # dbg
            subp = subprocess.Popen(self.call_args)
            self.pids.append(subp.pid)
            # If this fails, the pid will be left in self.pids and cleaned up
            # later, but if the wait call succeeds, then we can clear the
            # stored pid.
            retcode = subp.wait()
            self.pids.pop()
            return retcode

    def run(self):
        """Run the stored commands"""
        try:
            retcode = self._run_cmd()
        except:
            import traceback
            traceback.print_exc()
            return 1  # signal failure
        
        if self.coverage_xml:
            subprocess.call(["coverage", "xml", "-o", self.coverage_xml])
        return retcode

    def __del__(self):
        """Cleanup on exit by killing any leftover processes."""

        if not hasattr(os, 'kill'):
            return

        for pid in self.pids:
            try:
                print 'Cleaning stale PID:', pid
                os.kill(pid, signal.SIGKILL)
            except OSError:
                # This is just a best effort, if we fail or the process was
                # really gone, ignore it.
                pass


def make_runners():
    """Define the top-level packages that need to be tested.
    """

    # Packages to be tested via nose, that only depend on the stdlib
    nose_pkg_names = ['config', 'core', 'extensions', 'frontend', 'lib',
                     'testing', 'utils', 'nbformat' ]

    if have['zmq']:
        nose_pkg_names.append('zmq')
        nose_pkg_names.append('parallel')

    # For debugging this code, only load quick stuff
    #nose_pkg_names = ['core', 'extensions']  # dbg

    # Make fully qualified package names prepending 'IPython.' to our name lists
    nose_packages = ['IPython.%s' % m for m in nose_pkg_names ]

    # Make runners
    runners = [ (v, IPTester('iptest', params=v)) for v in nose_packages ]

    return runners


def run_iptest():
    """Run the IPython test suite using nose.

    This function is called when this script is **not** called with the form
    `iptest all`.  It simply calls nose with appropriate command line flags
    and accepts all of the standard nose arguments.
    """
    # Apply our monkeypatch to Xunit
    if '--with-xunit' in sys.argv and not hasattr(Xunit, 'orig_addError'):
        monkeypatch_xunit()

    warnings.filterwarnings('ignore',
        'This will be removed soon.  Use IPython.testing.util instead')

    argv = sys.argv + [ '--detailed-errors',  # extra info in tracebacks

                        '--with-ipdoctest',
                        '--ipdoctest-tests','--ipdoctest-extension=txt',

                        # We add --exe because of setuptools' imbecility (it
                        # blindly does chmod +x on ALL files).  Nose does the
                        # right thing and it tries to avoid executables,
                        # setuptools unfortunately forces our hand here.  This
                        # has been discussed on the distutils list and the
                        # setuptools devs refuse to fix this problem!
                        '--exe',
                        ]

    if nose.__version__ >= '0.11':
        # I don't fully understand why we need this one, but depending on what
        # directory the test suite is run from, if we don't give it, 0 tests
        # get run.  Specifically, if the test suite is run from the source dir
        # with an argument (like 'iptest.py IPython.core', 0 tests are run,
        # even if the same call done in this directory works fine).  It appears
        # that if the requested package is in the current dir, nose bails early
        # by default.  Since it's otherwise harmless, leave it in by default
        # for nose >= 0.11, though unfortunately nose 0.10 doesn't support it.
        argv.append('--traverse-namespace')

    # use our plugin for doctesting.  It will remove the standard doctest plugin
    # if it finds it enabled
    plugins = [IPythonDoctest(make_exclude()), KnownFailure()]
    # We need a global ipython running in this process
    globalipapp.start_ipython()
    # Now nose can run
    TestProgram(argv=argv, addplugins=plugins)


def run_iptestall():
    """Run the entire IPython test suite by calling nose and trial.

    This function constructs :class:`IPTester` instances for all IPython
    modules and package and then runs each of them.  This causes the modules
    and packages of IPython to be tested each in their own subprocess using
    nose.
    """

    runners = make_runners()

    # Run the test runners in a temporary dir so we can nuke it when finished
    # to clean up any junk files left over by accident.  This also makes it
    # robust against being run in non-writeable directories by mistake, as the
    # temp dir will always be user-writeable.
    curdir = os.getcwdu()
    testdir = tempfile.gettempdir()
    os.chdir(testdir)

    # Run all test runners, tracking execution time
    failed = []
    t_start = time.time()
    try:
        for (name, runner) in runners:
            print '*'*70
            print 'IPython test group:',name
            res = runner.run()
            if res:
                failed.append( (name, runner) )
    finally:
        os.chdir(curdir)
    t_end = time.time()
    t_tests = t_end - t_start
    nrunners = len(runners)
    nfail = len(failed)
    # summarize results
    print
    print '*'*70
    print 'Test suite completed for system with the following information:'
    print report()
    print 'Ran %s test groups in %.3fs' % (nrunners, t_tests)
    print
    print 'Status:'
    if not failed:
        print 'OK'
    else:
        # If anything went wrong, point out what command to rerun manually to
        # see the actual errors and individual summary
        print 'ERROR - %s out of %s test groups failed.' % (nfail, nrunners)
        for name, failed_runner in failed:
            print '-'*40
            print 'Runner failed:',name
            print 'You may wish to rerun this one individually, with:'
            failed_call_args = [py3compat.cast_unicode(x) for x in failed_runner.call_args]
            print u' '.join(failed_call_args)
            print
        # Ensure that our exit code indicates failure
        sys.exit(1)


def main():
    for arg in sys.argv[1:]:
        if arg.startswith('IPython'):
            # This is in-process
            run_iptest()
    else:
        # This starts subprocesses
        run_iptestall()


if __name__ == '__main__':
    main()
