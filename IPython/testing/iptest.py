# -*- coding: utf-8 -*-
"""IPython Test Suite Runner.

This module provides a main entry point to a user script to test IPython
itself from the command line. There are two ways of running this script:

1. With the syntax `iptest all`.  This runs our entire test suite by
   calling this script (with different arguments) or trial recursively.  This
   causes modules and package to be tested in different processes, using nose
   or trial where appropriate.
2. With the regular nose syntax, like `iptest -vvs IPython`.  In this form
   the script simply calls nose, but with special command line flags and
   plugins loaded.

For now, this script requires that both nose and twisted are installed.  This
will change in the future.
"""

#-----------------------------------------------------------------------------
# Module imports
#-----------------------------------------------------------------------------

# Stdlib
import os
import os.path as path
import signal
import sys
import subprocess
import tempfile
import time
import warnings


# Ugly,  but necessary hack to ensure the test suite finds our version of
# IPython and not a possibly different one that may exist system-wide.
# Note that this must be done here, so the imports that come next work
# correctly even if IPython isn't installed yet.
p = os.path
ippath = p.abspath(p.join(p.dirname(__file__),'..','..'))
sys.path.insert(0, ippath)

# Note: monkeypatch!
# We need to monkeypatch a small problem in nose itself first, before importing
# it for actual use.  This should get into nose upstream, but its release cycle
# is slow and we need it for our parametric tests to work correctly.
from IPython.testing import nosepatch
# Now, proceed to import nose itself
import nose.plugins.builtin
from nose.core import TestProgram

# Our own imports
from IPython.utils import genutils
from IPython.utils.platutils import find_cmd, FindCmdError
from IPython.testing import globalipapp
from IPython.testing import tools
from IPython.testing.plugin.ipdoctest import IPythonDoctest

pjoin = path.join


#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

# By default, we assume IPython has been installed.  But if the test suite is
# being run from a source tree that has NOT been installed yet, this flag can
# be set to False by the entry point scripts, to let us know that we must call
# the source tree versions of the scripts which manipulate sys.path instead of
# assuming that things exist system-wide.
INSTALLED = True

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

#-----------------------------------------------------------------------------
# Logic for skipping doctests
#-----------------------------------------------------------------------------

def test_for(mod):
    """Test to see if mod is importable."""
    try:
        __import__(mod)
    except (ImportError, RuntimeError):
        # GTK reports Runtime error if it can't be initialized even if  it's
        # importable.
        return False
    else:
        return True

have_curses = test_for('_curses')
have_wx = test_for('wx')
have_wx_aui = test_for('wx.aui')
have_zi = test_for('zope.interface')
have_twisted = test_for('twisted')
have_foolscap = test_for('foolscap')
have_objc = test_for('objc')
have_pexpect = test_for('pexpect')
have_gtk = test_for('gtk')
have_gobject = test_for('gobject')

#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------

def make_exclude():
    """Make patterns of modules and packages to exclude from testing.
    
    For the IPythonDoctest plugin, we need to exclude certain patterns that
    cause testing problems.  We should strive to minimize the number of
    skipped modules, since this means untested code.  As the testing
    machinery solidifies, this list should eventually become empty.
    These modules and packages will NOT get scanned by nose at all for tests.
    """
    # Simple utility to make IPython paths more readably, we need a lot of
    # these below
    ipjoin = lambda *paths: pjoin('IPython', *paths)
    
    exclusions = [ipjoin('external'),
                  ipjoin('frontend', 'process', 'winprocess.py'),
                  # Deprecated old Shell and iplib modules, skip to avoid
                  # warnings
                  ipjoin('Shell'),
                  ipjoin('iplib'),
                  pjoin('IPython_doctest_plugin'),
                  ipjoin('quarantine'),
                  ipjoin('deathrow'),
                  ipjoin('testing', 'attic'),
                  # This guy is probably attic material
                  ipjoin('testing', 'mkdoctests'),
                  # Testing inputhook will need a lot of thought, to figure out
                  # how to have tests that don't lock up with the gui event
                  # loops in the picture
                  ipjoin('lib', 'inputhook'),
                  # Config files aren't really importable stand-alone
                  ipjoin('config', 'default'),
                  ipjoin('config', 'profile'),
                  ]

    if not have_wx:
        exclusions.append(ipjoin('gui'))
        exclusions.append(ipjoin('frontend', 'wx'))
        exclusions.append(ipjoin('lib', 'inputhookwx'))

    if not have_gtk or not have_gobject:
        exclusions.append(ipjoin('lib', 'inputhookgtk'))

    if not have_wx_aui:
        exclusions.append(ipjoin('gui', 'wx', 'wxIPython'))

    if not have_objc:
        exclusions.append(ipjoin('frontend', 'cocoa'))

    if not sys.platform == 'win32':
        exclusions.append(ipjoin('utils', 'platutils_win32'))

    # These have to be skipped on win32 because the use echo, rm, cd, etc.
    # See ticket https://bugs.launchpad.net/bugs/366982
    if sys.platform == 'win32':
        exclusions.append(ipjoin('testing', 'plugin', 'test_exampleip'))
        exclusions.append(ipjoin('testing', 'plugin', 'dtexample'))

    if not os.name == 'posix':
        exclusions.append(ipjoin('utils', 'platutils_posix'))

    if not have_pexpect:
        exclusions.extend([ipjoin('scripts', 'irunner'),
                           ipjoin('lib', 'irunner')])

    # This is scary.  We still have things in frontend and testing that
    # are being tested by nose that use twisted.  We need to rethink
    # how we are isolating dependencies in testing.
    if not (have_twisted and have_zi and have_foolscap):
        exclusions.extend(
            [ipjoin('frontend', 'asyncfrontendbase'),
             ipjoin('frontend', 'prefilterfrontend'),
             ipjoin('frontend', 'frontendbase'),
             ipjoin('frontend', 'linefrontendbase'),
             ipjoin('frontend', 'tests', 'test_linefrontend'),
             ipjoin('frontend', 'tests', 'test_frontendbase'),
             ipjoin('frontend', 'tests', 'test_prefilterfrontend'),
             ipjoin('frontend', 'tests', 'test_asyncfrontendbase'),
             ipjoin('testing', 'parametric'),
             ipjoin('testing', 'util'),
             ipjoin('testing', 'tests', 'test_decorators_trial'),
             ] )

    # This is needed for the reg-exp to match on win32 in the ipdoctest plugin.
    if sys.platform == 'win32':
        exclusions = [s.replace('\\','\\\\') for s in exclusions]

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
    
    def __init__(self, runner='iptest', params=None):
        """Create new test runner."""
        p = os.path
        if runner == 'iptest':
            if INSTALLED:
                self.runner = tools.cmd2argv(
                    p.abspath(find_cmd('iptest'))) + sys.argv[1:]
            else:
                # Find our own 'iptest' script OS-level entry point.  Don't
                # look system-wide, so we are sure we pick up *this one*.  And
                # pass through to subprocess call our own sys.argv
                ippath = p.abspath(p.join(p.dirname(__file__),'..','..'))
                script = p.join(ippath, 'iptest.py')
                self.runner = tools.cmd2argv(script) + sys.argv[1:]
                
        else:
            # For trial, it needs to be installed system-wide
            self.runner = tools.cmd2argv(p.abspath(find_cmd('trial')))
        if params is None:
            params = []
        if isinstance(params, str):
            params = [params]
        self.params = params

        # Assemble call
        self.call_args = self.runner+self.params

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
            return os.system(' '.join(self.call_args))
    else:
        def _run_cmd(self):
            #print >> sys.stderr, '*** CMD:', ' '.join(self.call_args) # dbg
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
            return self._run_cmd()
        except:
            import traceback
            traceback.print_exc()
            return 1  # signal failure

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
                     'scripts', 'testing', 'utils' ]
    # The machinery in kernel needs twisted for real testing
    trial_pkg_names = []

    if have_wx:
        nose_pkg_names.append('gui')

    # And add twisted ones if conditions are met
    if have_zi and have_twisted and have_foolscap:
        # Note that we list the kernel here, though the bulk of it is
        # twisted-based, because nose picks up doctests that twisted doesn't.
        nose_pkg_names.append('kernel')
        trial_pkg_names.append('kernel')

    # For debugging this code, only load quick stuff
    #nose_pkg_names = ['core', 'extensions']  # dbg
    #trial_pkg_names = []  # dbg 

    # Make fully qualified package names prepending 'IPython.' to our name lists
    nose_packages = ['IPython.%s' % m for m in nose_pkg_names ]
    trial_packages = ['IPython.%s' % m for m in trial_pkg_names ]

    # Make runners
    runners = [ (v, IPTester('iptest', params=v)) for v in nose_packages ]
    runners.extend([ (v, IPTester('trial', params=v)) for v in trial_packages ])
    
    return runners


def run_iptest():
    """Run the IPython test suite using nose.
    
    This function is called when this script is **not** called with the form
    `iptest all`.  It simply calls nose with appropriate command line flags
    and accepts all of the standard nose arguments.
    """

    warnings.filterwarnings('ignore', 
        'This will be removed soon.  Use IPython.testing.util instead')

    argv = sys.argv + [ '--detailed-errors',  # extra info in tracebacks
                                                
                        # Loading ipdoctest causes problems with Twisted, but
                        # our test suite runner now separates things and runs
                        # all Twisted tests with trial.
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

    # Construct list of plugins, omitting the existing doctest plugin, which
    # ours replaces (and extends).
    plugins = [IPythonDoctest(make_exclude())]
    for p in nose.plugins.builtin.plugins:
        plug = p()
        if plug.name == 'doctest':
            continue
        plugins.append(plug)

    # We need a global ipython running in this process
    globalipapp.start_ipython()
    # Now nose can run
    TestProgram(argv=argv, plugins=plugins)


def run_iptestall():
    """Run the entire IPython test suite by calling nose and trial.
    
    This function constructs :class:`IPTester` instances for all IPython
    modules and package and then runs each of them.  This causes the modules
    and packages of IPython to be tested each in their own subprocess using
    nose or twisted.trial appropriately.
    """

    runners = make_runners()

    # Run the test runners in a temporary dir so we can nuke it when finished
    # to clean up any junk files left over by accident.  This also makes it
    # robust against being run in non-writeable directories by mistake, as the
    # temp dir will always be user-writeable.
    curdir = os.getcwd()
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
    print 'Ran %s test groups in %.3fs' % (nrunners, t_tests)
    print
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
            print ' '.join(failed_runner.call_args)
            print


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
