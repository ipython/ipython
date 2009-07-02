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
have_zi = test_for('zope.interface')
have_twisted = test_for('twisted')
have_foolscap = test_for('foolscap')
have_objc = test_for('objc')
have_pexpect = test_for('pexpect')

# For the IPythonDoctest plugin, we need to exclude certain patterns that cause
# testing problems.  We should strive to minimize the number of skipped
# modules, since this means untested code.  As the testing machinery
# solidifies, this list should eventually become empty.
EXCLUDE = [pjoin('IPython', 'external'),
           pjoin('IPython', 'frontend', 'process', 'winprocess.py'),
           pjoin('IPython_doctest_plugin'),
           pjoin('IPython', 'Gnuplot'),
           pjoin('IPython', 'Extensions', 'ipy_'),
           pjoin('IPython', 'Extensions', 'clearcmd'),
           pjoin('IPython', 'Extensions', 'PhysicalQInteractive'),
           pjoin('IPython', 'Extensions', 'scitedirector'),
           pjoin('IPython', 'Extensions', 'numeric_formats'),
           pjoin('IPython', 'testing', 'attic'),
           pjoin('IPython', 'testing', 'tutils'),
           pjoin('IPython', 'testing', 'tools'),
           pjoin('IPython', 'testing', 'mkdoctests')
           ]

if not have_wx:
    EXCLUDE.append(pjoin('IPython', 'Extensions', 'igrid'))
    EXCLUDE.append(pjoin('IPython', 'gui'))
    EXCLUDE.append(pjoin('IPython', 'frontend', 'wx'))

if not have_objc:
    EXCLUDE.append(pjoin('IPython', 'frontend', 'cocoa'))

if not have_curses:
    EXCLUDE.append(pjoin('IPython', 'Extensions', 'ibrowse'))

if not sys.platform == 'win32':
    EXCLUDE.append(pjoin('IPython', 'platutils_win32'))

# These have to be skipped on win32 because the use echo, rm, cd, etc.
# See ticket https://bugs.launchpad.net/bugs/366982
if sys.platform == 'win32':
    EXCLUDE.append(pjoin('IPython', 'testing', 'plugin', 'test_exampleip'))
    EXCLUDE.append(pjoin('IPython', 'testing', 'plugin', 'dtexample'))

if not os.name == 'posix':
    EXCLUDE.append(pjoin('IPython', 'platutils_posix'))

if not have_pexpect:
    EXCLUDE.append(pjoin('IPython', 'lib', 'irunner'))

# This is needed for the reg-exp to match on win32 in the ipdoctest plugin.
if sys.platform == 'win32':
    EXCLUDE = [s.replace('\\','\\\\') for s in EXCLUDE]


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
    plugins = [IPythonDoctest(EXCLUDE)]
    for p in nose.plugins.builtin.plugins:
        plug = p()
        if plug.name == 'doctest':
            continue

        #print '*** adding plugin:',plug.name  # dbg
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

    def run(self):
        """Run the stored commands"""
        return subprocess.call(self.call_args)


def make_runners():
    """Define the modules and packages that need to be tested.
    """
    
    # This omits additional top-level modules that should not be doctested.
    # XXX: shell.py is also ommited because of a bug in the skip_doctest
    # decorator.  See ticket https://bugs.launchpad.net/bugs/366209
    top_mod = \
      ['backgroundjobs.py', 'coloransi.py', 'completer.py', 'configloader.py',
       'crashhandler.py', 'debugger.py', 'deepreload.py', 'demo.py',
       'DPyGetOpt.py', 'dtutils.py', 'excolors.py', 'fakemodule.py',
       'generics.py', 'genutils.py', 'history.py', 'hooks.py', 'ipapi.py',
       'iplib.py', 'ipmaker.py', 'ipstruct.py', 'Itpl.py',
       'logger.py', 'macro.py', 'magic.py', 'oinspect.py',
       'outputtrap.py', 'platutils.py', 'prefilter.py', 'prompts.py',
       'PyColorize.py', 'release.py', 'rlineimpl.py', 'shadowns.py',
       'shellglobals.py', 'strdispatch.py', 'twshell.py',
       'ultratb.py', 'upgradedir.py', 'usage.py', 'wildcard.py',
       # See note above for why this is skipped
       # 'shell.py',
       'winconsole.py']

    if have_pexpect:
        top_mod.append('irunner.py')

    if sys.platform == 'win32':
        top_mod.append('platutils_win32.py')
    elif os.name == 'posix':
        top_mod.append('platutils_posix.py')
    else:
        top_mod.append('platutils_dummy.py')

    # These are tested by nose, so skip IPython.kernel
    top_pack = ['config','Extensions','frontend',
                'testing','tests','tools','UserConfig']

    if have_wx:
        top_pack.append('gui')

    modules  = ['IPython.%s' % m[:-3] for m in top_mod ]
    packages = ['IPython.%s' % m for m in top_pack ]

    # Make runners
    runners = dict(zip(top_pack, [IPTester(params=v) for v in packages]))
    
    # Test IPython.kernel using trial if twisted is installed
    if have_zi and have_twisted and have_foolscap:
        runners['trial'] = IPTester('trial',['IPython'])

    runners['modules'] = IPTester(params=modules)

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
        print 'IPython test set:',name
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
    print 'Ran %s test sets in %.3fs' % (nrunners, t_tests)
    print
    if not failed:
        print 'OK'
    else:
        # If anything went wrong, point out what command to rerun manually to
        # see the actual errors and individual summary
        print 'ERROR - %s out of %s test sets failed.' % (nfail, nrunners)
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