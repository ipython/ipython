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

import os
import os.path as path
import sys
import subprocess
import tempfile
import time
import warnings

import nose.plugins.builtin
from nose.core import TestProgram

from IPython.utils.platutils import find_cmd
from IPython.testing.plugin.ipdoctest import IPythonDoctest

pjoin = path.join

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


def make_exclude():

    # For the IPythonDoctest plugin, we need to exclude certain patterns that cause
    # testing problems.  We should strive to minimize the number of skipped
    # modules, since this means untested code.  As the testing machinery
    # solidifies, this list should eventually become empty.
    EXCLUDE = [pjoin('IPython', 'external'),
               pjoin('IPython', 'frontend', 'process', 'winprocess.py'),
               pjoin('IPython_doctest_plugin'),
               pjoin('IPython', 'extensions', 'ipy_'),
               pjoin('IPython', 'extensions', 'PhysicalQInput'),
               pjoin('IPython', 'extensions', 'PhysicalQInteractive'),
               pjoin('IPython', 'extensions', 'InterpreterPasteInput'),
               pjoin('IPython', 'extensions', 'scitedirector'),
               pjoin('IPython', 'extensions', 'numeric_formats'),
               pjoin('IPython', 'testing', 'attic'),
               pjoin('IPython', 'testing', 'tools'),
               pjoin('IPython', 'testing', 'mkdoctests')
               ]

    if not have_wx:
        EXCLUDE.append(pjoin('IPython', 'extensions', 'igrid'))
        EXCLUDE.append(pjoin('IPython', 'gui'))
        EXCLUDE.append(pjoin('IPython', 'frontend', 'wx'))

    if not have_wx_aui:
        EXCLUDE.append(pjoin('IPython', 'gui', 'wx', 'wxIPython'))

    if not have_objc:
        EXCLUDE.append(pjoin('IPython', 'frontend', 'cocoa'))

    if not have_curses:
        EXCLUDE.append(pjoin('IPython', 'extensions', 'ibrowse'))

    if not sys.platform == 'win32':
        EXCLUDE.append(pjoin('IPython', 'utils', 'platutils_win32'))

    # These have to be skipped on win32 because the use echo, rm, cd, etc.
    # See ticket https://bugs.launchpad.net/bugs/366982
    if sys.platform == 'win32':
        EXCLUDE.append(pjoin('IPython', 'testing', 'plugin', 'test_exampleip'))
        EXCLUDE.append(pjoin('IPython', 'testing', 'plugin', 'dtexample'))

    if not os.name == 'posix':
        EXCLUDE.append(pjoin('IPython', 'utils', 'platutils_posix'))

    if not have_pexpect:
        EXCLUDE.append(pjoin('IPython', 'scripts', 'irunner'))

    # This is scary.  We still have things in frontend and testing that
    # are being tested by nose that use twisted.  We need to rethink
    # how we are isolating dependencies in testing.
    if not (have_twisted and have_zi and have_foolscap):
        EXCLUDE.append(pjoin('IPython', 'frontend', 'asyncfrontendbase'))
        EXCLUDE.append(pjoin('IPython', 'frontend', 'prefilterfrontend'))
        EXCLUDE.append(pjoin('IPython', 'frontend', 'frontendbase'))
        EXCLUDE.append(pjoin('IPython', 'frontend', 'linefrontendbase'))
        EXCLUDE.append(pjoin('IPython', 'frontend', 'tests',
                             'test_linefrontend'))
        EXCLUDE.append(pjoin('IPython', 'frontend', 'tests', 
                             'test_frontendbase'))
        EXCLUDE.append(pjoin('IPython', 'frontend', 'tests',
                             'test_prefilterfrontend'))
        EXCLUDE.append(pjoin('IPython', 'frontend', 'tests',
                             'test_asyncfrontendbase')),
        EXCLUDE.append(pjoin('IPython', 'testing', 'parametric'))
        EXCLUDE.append(pjoin('IPython', 'testing', 'util'))
        EXCLUDE.append(pjoin('IPython', 'testing', 'tests', 
                             'test_decorators_trial'))

    # Skip shell always because of a bug in FakeModule.
    EXCLUDE.append(pjoin('IPython', 'core', 'shell'))

    # This is needed for the reg-exp to match on win32 in the ipdoctest plugin.
    if sys.platform == 'win32':
        EXCLUDE = [s.replace('\\','\\\\') for s in EXCLUDE]

    return EXCLUDE


#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------

def run_iptest():
    """Run the IPython test suite using nose.
    
    This function is called when this script is **not** called with the form
    `iptest all`.  It simply calls nose with appropriate command line flags
    and accepts all of the standard nose arguments.
    """

    warnings.filterwarnings('ignore', 
        'This will be removed soon.  Use IPython.testing.util instead')

    argv = sys.argv + [ 
                        # Loading ipdoctest causes problems with Twisted.
                        # I am removing this as a temporary fix to get the 
                        # test suite back into working shape.  Our nose
                        # plugin needs to be gone through with a fine
                        # toothed comb to find what is causing the problem.
                        '--with-ipdoctest',
                        '--ipdoctest-tests','--ipdoctest-extension=txt',
                        '--detailed-errors',
                       
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

    # Construct list of plugins, omitting the existing doctest plugin, which
    # ours replaces (and extends).
    EXCLUDE = make_exclude()
    plugins = [IPythonDoctest(EXCLUDE)]
    for p in nose.plugins.builtin.plugins:
        plug = p()
        if plug.name == 'doctest':
            continue
        plugins.append(plug)

    TestProgram(argv=argv,plugins=plugins)


class IPTester(object):
    """Call that calls iptest or trial in a subprocess.
    """
    def __init__(self,runner='iptest',params=None):
        """ """
        if runner == 'iptest':
            self.runner = ['iptest','-v']
        else:
            self.runner = [find_cmd('trial')]
        if params is None:
            params = []
        if isinstance(params,str):
            params = [params]
        self.params = params

        # Assemble call
        self.call_args = self.runner+self.params

    if sys.platform == 'win32':
        def run(self):
            """Run the stored commands"""
            # On Windows, cd to temporary directory to run tests.  Otherwise,
            # Twisted's trial may not be able to execute 'trial IPython', since
            # it will confuse the IPython module name with the ipython
            # execution scripts, because the windows file system isn't case
            # sensitive.
            # We also use os.system instead of subprocess.call, because I was
            # having problems with subprocess and I just don't know enough
            # about win32 to debug this reliably.  Os.system may be the 'old
            # fashioned' way to do it, but it works just fine.  If someone
            # later can clean this up that's fine, as long as the tests run
            # reliably in win32.
            curdir = os.getcwd()
            os.chdir(tempfile.gettempdir())
            stat = os.system(' '.join(self.call_args))
            os.chdir(curdir)
            return stat
    else:
        def run(self):
            """Run the stored commands"""
            return subprocess.call(self.call_args)


def make_runners():
    """Define the top-level packages that need to be tested.
    """

    nose_packages = ['config', 'core', 'extensions',
                     'frontend', 'lib', 'quarantine',
                     'scripts', 'testing', 'utils']
    trial_packages = ['kernel']

    if have_wx:
        nose_packages.append('gui')

    nose_packages = ['IPython.%s' % m for m in nose_packages ]
    trial_packages = ['IPython.%s' % m for m in trial_packages ]

    # Make runners
    runners = dict()
    
    nose_runners = dict(zip(nose_packages, [IPTester(params=v) for v in nose_packages]))
    if have_zi and have_twisted and have_foolscap:
        trial_runners = dict(zip(trial_packages, [IPTester('trial',params=v) for v in trial_packages]))
    runners.update(nose_runners)
    runners.update(trial_runners)

    return runners


def run_iptestall():
    """Run the entire IPython test suite by calling nose and trial.
    
    This function constructs :class:`IPTester` instances for all IPython
    modules and package and then runs each of them.  This causes the modules
    and packages of IPython to be tested each in their own subprocess using
    nose or twisted.trial appropriately.
    """

    runners = make_runners()

    # Run all test runners, tracking execution time
    failed = {}
    t_start = time.time()
    for name,runner in runners.iteritems():
        print '*'*77
        print 'IPython test group:',name
        res = runner.run()
        if res:
            failed[name] = res
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
