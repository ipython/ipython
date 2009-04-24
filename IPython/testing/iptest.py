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

from IPython.testing.plugin.ipdoctest import IPythonDoctest

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

# For the IPythonDoctest plugin, we need to exclude certain patterns that cause
# testing problems.  We should strive to minimize the number of skipped
# modules, since this means untested code.  As the testing machinery
# solidifies, this list should eventually become empty.
EXCLUDE = ['IPython/external/',
           'IPython/platutils_win32',
           'IPython/frontend/cocoa',
           'IPython/frontend/process/winprocess.py',
           'IPython_doctest_plugin',
           'IPython/Gnuplot',
           'IPython/Extensions/ipy_',
           'IPython/Extensions/clearcmd',
           'IPython/Extensions/PhysicalQIn',
           'IPython/Extensions/scitedirector',
           'IPython/Extensions/numeric_formats',
           'IPython/testing/attic',
           ]

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
            self.runner = ['trial']
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
    # XXX: Shell.py is also ommited because of a bug in the skip_doctest
    # decorator.  See ticket https://bugs.launchpad.net/bugs/366209
    top_mod = \
      ['background_jobs.py', 'ColorANSI.py', 'completer.py', 'ConfigLoader.py',
       'CrashHandler.py', 'Debugger.py', 'deep_reload.py', 'demo.py',
       'DPyGetOpt.py', 'dtutils.py', 'excolors.py', 'FakeModule.py',
       'generics.py', 'genutils.py', 'history.py', 'hooks.py', 'ipapi.py',
       'iplib.py', 'ipmaker.py', 'ipstruct.py', 'irunner.py', 'Itpl.py',
       'Logger.py', 'macro.py', 'Magic.py', 'OInspect.py',
       'OutputTrap.py', 'platutils.py', 'prefilter.py', 'Prompts.py',
       'PyColorize.py', 'Release.py', 'rlineimpl.py', 'shadowns.py',
       'shellglobals.py', 'strdispatch.py', 'twshell.py',
       'ultraTB.py', 'upgrade_dir.py', 'usage.py', 'wildcard.py',
       # See note above for why this is skipped
       # 'Shell.py',
       'winconsole.py']

    if os.name == 'posix':
        top_mod.append('platutils_posix.py')
    elif sys.platform == 'win32':
        top_mod.append('platutils_win32.py')
    else:
        top_mod.append('platutils_dummy.py')

    top_pack = ['config','Extensions','frontend','gui','kernel',
                'testing','tests','tools','UserConfig']

    modules  = ['IPython.%s' % m[:-3] for m in top_mod ]
    packages = ['IPython.%s' % m for m in top_pack ]

    # Make runners
    runners = dict(zip(top_pack, [IPTester(params=v) for v in packages]))

    try:
        import zope.interface
        import twisted
        import foolscap
    except ImportError:
        pass
    else:
        runners['trial'] = IPTester('trial',['IPython'])

    for m in modules:
        runners[m] = IPTester(params=m)

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
    if sys.argv[1] == 'all':
        run_iptestall()
    else:
        run_iptest()


if __name__ == '__main__':
    main()