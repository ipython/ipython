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

from __future__ import absolute_import

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

# Note: monkeypatch!
# We need to monkeypatch a small problem in nose itself first, before importing
# it for actual use.  This should get into nose upstream, but its release cycle
# is slow and we need it for our parametric tests to work correctly.
from . import nosepatch
# Now, proceed to import nose itself
import nose.plugins.builtin
from nose.core import TestProgram

# Our own imports
from IPython.utils import genutils
from IPython.utils.platutils import find_cmd, FindCmdError
from . import globalipapp
from .plugin.ipdoctest import IPythonDoctest

pjoin = path.join

#-----------------------------------------------------------------------------
# Warnings control
#-----------------------------------------------------------------------------
# Twisted generates annoying warnings with Python 2.6, as will do other code
# that imports 'sets' as of today
warnings.filterwarnings('ignore', 'the sets module is deprecated',
                        DeprecationWarning )

#-----------------------------------------------------------------------------
# Logic for skipping doctests
#-----------------------------------------------------------------------------

def test_for(mod):
    """Test to see if mod is importable."""
    try:
        __import__(mod)
    except ImportError:
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
                  pjoin('IPython_doctest_plugin'),
                  ipjoin('quarantine'),
                  ipjoin('deathrow'),
                  ipjoin('testing', 'attic'),
                  ipjoin('testing', 'tools'),
                  ipjoin('testing', 'mkdoctests'),
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
        exclusions.append(ipjoin('scripts', 'irunner'))

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


#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------

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
    
    def __init__(self,runner='iptest',params=None):
        """Create new test runner."""
        if runner == 'iptest':
            # Find our own 'iptest' script OS-level entry point
            try:
                iptest_path = os.path.abspath(find_cmd('iptest'))
            except FindCmdError:
                # Script not installed (may be the case for testing situations
                # that are running from a source tree only), pull from internal
                # path:
                iptest_path = pjoin(genutils.get_ipython_package_dir(),
                                    'scripts','iptest')
            self.runner = ['python', iptest_path, '-v']
        else:
            self.runner = ['python', os.path.abspath(find_cmd('trial'))]
        if params is None:
            params = []
        if isinstance(params,str):
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

    nose_packages = ['config', 'core', 'extensions', 'frontend', 'lib',
                     'scripts', 'testing', 'utils']
    trial_packages = ['kernel']

    if have_wx:
        nose_packages.append('gui')

    #nose_packages = ['core']  # dbg
    #trial_packages = []  # dbg 

    nose_packages = ['IPython.%s' % m for m in nose_packages ]
    trial_packages = ['IPython.%s' % m for m in trial_packages ]

    # Make runners, most with nose
    nose_testers = [IPTester(params=v) for v in nose_packages]
    runners = dict(zip(nose_packages, nose_testers))
    # And add twisted ones if conditions are met
    if have_zi and have_twisted and have_foolscap:
        trial_testers = [IPTester('trial',params=v) for v in trial_packages]
        runners.update(dict(zip(trial_packages,trial_testers)))
                                 
    return runners


def run_iptest():
    """Run the IPython test suite using nose.
    
    This function is called when this script is **not** called with the form
    `iptest all`.  It simply calls nose with appropriate command line flags
    and accepts all of the standard nose arguments.
    """

    warnings.filterwarnings('ignore', 
        'This will be removed soon.  Use IPython.testing.util instead')

    argv = sys.argv + [ '--detailed-errors',
                        # Loading ipdoctest causes problems with Twisted, but
                        # our test suite runner now separates things and runs
                        # all Twisted tests with trial.
                        '--with-ipdoctest',
                        '--ipdoctest-tests','--ipdoctest-extension=txt',
                        
                        #'-x','-s',  # dbg
                        
                        # We add --exe because of setuptools' imbecility (it
                        # blindly does chmod +x on ALL files).  Nose does the
                        # right thing and it tries to avoid executables,
                        # setuptools unfortunately forces our hand here.  This
                        # has been discussed on the distutils list and the
                        # setuptools devs refuse to fix this problem!
                        '--exe',
                        ]

    # Detect if any tests were required by explicitly calling an IPython
    # submodule or giving a specific path
    has_tests = False
    for arg in sys.argv:
        if 'IPython' in arg or arg.endswith('.py') or \
           (':' in arg and  '.py' in arg):
            has_tests = True
            break
        
    # If nothing was specifically requested, test full IPython
    if not has_tests:
        argv.append('IPython')

    ## # Construct list of plugins, omitting the existing doctest plugin, which
    ## # ours replaces (and extends).
    plugins = [IPythonDoctest(make_exclude())]
    for p in nose.plugins.builtin.plugins:
        plug = p()
        if plug.name == 'doctest':
            continue
        plugins.append(plug)

    # We need a global ipython running in this process
    globalipapp.start_ipython()
    # Now nose can run
    TestProgram(argv=argv,plugins=plugins)


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
    failed = {}
    t_start = time.time()
    try:
        for name,runner in runners.iteritems():
            print '*'*77
            print 'IPython test group:',name
            res = runner.run()
            if res:
                failed[name] = res
    finally:
        os.chdir(curdir)
    t_end = time.time()
    t_tests = t_end - t_start
    nrunners = len(runners)
    nfail = len(failed)
    # summarize results
    print
    print '*'*77
    print 'Ran %s test groups in %.3fs' % (nrunners, t_tests)
    print
    if not failed:
        print 'OK'
    else:
        # If anything went wrong, point out what command to rerun manually to
        # see the actual errors and individual summary
        print 'ERROR - %s out of %s test groups failed.' % (nfail, nrunners)
        for name in failed:
            failed_runner = runners[name]
            print '-'*40
            print 'Runner failed:',name
            print 'You may wish to rerun this one individually, with:'
            print ' '.join(failed_runner.call_args)
            print


def main():
    if len(sys.argv) == 1:
        run_iptestall()
    else:
        if sys.argv[1] == 'all':
            run_iptestall()
        else:
            run_iptest()


if __name__ == '__main__':
    main()
