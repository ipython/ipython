# -*- coding: utf-8 -*-
"""IPython Test Process Controller

This module runs one or more subprocesses which will actually run the IPython
test suite.

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
from __future__ import print_function

import multiprocessing.pool
import os
import signal
import sys
import subprocess
import tempfile
import time

from .iptest import have, special_test_suites
from IPython.utils import py3compat
from IPython.utils.path import get_ipython_module_path
from IPython.utils.process import pycmd2argv
from IPython.utils.sysinfo import sys_info
from IPython.utils.tempdir import TemporaryDirectory


class IPTester(object):
    """Call that calls iptest or trial in a subprocess.
    """
    #: string, name of test runner that will be called
    runner = None
    #: list, parameters for test runner
    params = None
    #: list, arguments of system call to be made to call test runner
    call_args = None
    #: list, subprocesses we start (for cleanup)
    processes = None
    #: str, coverage xml output file
    coverage_xml = None
    buffer_output = False

    def __init__(self, runner='iptest', params=None):
        """Create new test runner."""
        if runner == 'iptest':
            iptest_app = os.path.abspath(get_ipython_module_path('IPython.testing.iptest'))
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
            if sect.startswith('IPython') or sect in special_test_suites: break
        else:
            raise ValueError("Section not found", self.params)
        
        if '--with-xunit' in self.call_args:
            
            self.call_args.append('--xunit-file')
            # FIXME: when Windows uses subprocess.call, these extra quotes are unnecessary:
            xunit_file = os.path.abspath(sect+'.xunit.xml')
            if sys.platform == 'win32':
                xunit_file = '"%s"' % xunit_file
            self.call_args.append(xunit_file)
        
        if '--with-xml-coverage' in self.call_args:
            self.coverage_xml = os.path.abspath(sect+".coverage.xml")
            self.call_args.remove('--with-xml-coverage')
            self.call_args = ["coverage", "run", "--source="+sect] + self.call_args[1:]

        # Store anything we start to clean up on deletion
        self.processes = []

    def _run_cmd(self):
        with TemporaryDirectory() as IPYTHONDIR:
            env = os.environ.copy()
            env['IPYTHONDIR'] = IPYTHONDIR
            # print >> sys.stderr, '*** CMD:', ' '.join(self.call_args) # dbg
            output = subprocess.PIPE if self.buffer_output else None
            subp = subprocess.Popen(self.call_args, stdout=output,
                    stderr=output, env=env)
            self.processes.append(subp)
            # If this fails, the process will be left in self.processes and
            # cleaned up later, but if the wait call succeeds, then we can
            # clear the stored process.
            retcode = subp.wait()
            self.processes.pop()
            self.stdout = subp.stdout
            self.stderr = subp.stderr
            return retcode

    def run(self):
        """Run the stored commands"""
        try:
            retcode = self._run_cmd()
        except KeyboardInterrupt:
            return -signal.SIGINT
        except:
            import traceback
            traceback.print_exc()
            return 1  # signal failure
        
        if self.coverage_xml:
            subprocess.call(["coverage", "xml", "-o", self.coverage_xml])
        return retcode

    def __del__(self):
        """Cleanup on exit by killing any leftover processes."""
        for subp in self.processes:
            if subp.poll() is not None:
                continue # process is already dead

            try:
                print('Cleaning up stale PID: %d' % subp.pid)
                subp.kill()
            except: # (OSError, WindowsError) ?
                # This is just a best effort, if we fail or the process was
                # really gone, ignore it.
                pass
            else:
                for i in range(10):
                    if subp.poll() is None:
                        time.sleep(0.1)
                    else:
                        break

            if subp.poll() is None:
                # The process did not die...
                print('... failed. Manual cleanup may be required.')

def make_runners(inc_slow=False):
    """Define the top-level packages that need to be tested.
    """

    # Packages to be tested via nose, that only depend on the stdlib
    nose_pkg_names = ['config', 'core', 'extensions', 'lib', 'terminal',
                      'testing', 'utils', 'nbformat']

    if have['qt']:
        nose_pkg_names.append('qt')

    if have['tornado']:
        nose_pkg_names.append('html')
        
    if have['zmq']:
        nose_pkg_names.insert(0, 'kernel')
        nose_pkg_names.insert(1, 'kernel.inprocess')
        if inc_slow:
            nose_pkg_names.insert(0, 'parallel')

    if all((have['pygments'], have['jinja2'], have['sphinx'])):
        nose_pkg_names.append('nbconvert')

    # For debugging this code, only load quick stuff
    #nose_pkg_names = ['core', 'extensions']  # dbg

    # Make fully qualified package names prepending 'IPython.' to our name lists
    nose_packages = ['IPython.%s' % m for m in nose_pkg_names ]

    # Make runners
    runners = [ (v, IPTester('iptest', params=v)) for v in nose_packages ]
    
    for name in special_test_suites:
        runners.append((name, IPTester('iptest', params=name)))

    return runners

def do_run(x):
    print('IPython test group:',x[0])
    ret = x[1].run()
    return ret

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

def run_iptestall(inc_slow=False, fast=False):
    """Run the entire IPython test suite by calling nose and trial.

    This function constructs :class:`IPTester` instances for all IPython
    modules and package and then runs each of them.  This causes the modules
    and packages of IPython to be tested each in their own subprocess using
    nose.
    
    Parameters
    ----------
    
    inc_slow : bool, optional
      Include slow tests, like IPython.parallel. By default, these tests aren't
      run.

    fast : bool, option
      Run the test suite in parallel, if True, using as many threads as there
      are processors
    """
    if fast:
        p = multiprocessing.pool.ThreadPool()
    else:
        p = multiprocessing.pool.ThreadPool(1)

    runners = make_runners(inc_slow=inc_slow)

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
        all_res = p.map(do_run, runners)
        print('*'*70)
        for ((name, runner), res) in zip(runners, all_res):
            tgroup = 'IPython test group: ' + name
            res_string = 'OK' if res == 0 else 'FAILED'
            res_string = res_string.rjust(70 - len(tgroup), '.')
            print(tgroup + res_string)
            if res:
                failed.append( (name, runner) )
                if res == -signal.SIGINT:
                    print("Interrupted")
                    break
    finally:
        os.chdir(curdir)
    t_end = time.time()
    t_tests = t_end - t_start
    nrunners = len(runners)
    nfail = len(failed)
    # summarize results
    print()
    print('*'*70)
    print('Test suite completed for system with the following information:')
    print(report())
    print('Ran %s test groups in %.3fs' % (nrunners, t_tests))
    print()
    print('Status:')
    if not failed:
        print('OK')
    else:
        # If anything went wrong, point out what command to rerun manually to
        # see the actual errors and individual summary
        print('ERROR - %s out of %s test groups failed.' % (nfail, nrunners))
        for name, failed_runner in failed:
            print('-'*40)
            print('Runner failed:',name)
            print('You may wish to rerun this one individually, with:')
            failed_call_args = [py3compat.cast_unicode(x) for x in failed_runner.call_args]
            print(u' '.join(failed_call_args))
            print()
        # Ensure that our exit code indicates failure
        sys.exit(1)


def main():
    for arg in sys.argv[1:]:
        if arg.startswith('IPython') or arg in special_test_suites:
            from .iptest import run_iptest
            # This is in-process
            run_iptest()
    else:
        inc_slow =  "--all" in sys.argv
        if inc_slow:
            sys.argv.remove("--all")

        fast =  "--fast" in sys.argv
        if fast:
            sys.argv.remove("--fast")
            IPTester.buffer_output = True

        # This starts subprocesses
        run_iptestall(inc_slow=inc_slow, fast=fast)


if __name__ == '__main__':
    main()
