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

import argparse
import multiprocessing.pool
import os
import signal
import sys
import subprocess
import time

from .iptest import have, test_group_names, test_sections
from IPython.utils import py3compat
from IPython.utils.sysinfo import sys_info
from IPython.utils.tempdir import TemporaryDirectory


class IPTestController(object):
    """Run iptest in a subprocess
    """
    #: str, IPython test suite to be executed.
    section = None
    #: list, command line arguments to be executed
    cmd = None
    #: dict, extra environment variables to set for the subprocess
    env = None
    #: list, TemporaryDirectory instances to clear up when the process finishes
    dirs = None
    #: subprocess.Popen instance
    process = None
    buffer_output = False

    def __init__(self, section):
        """Create new test runner."""
        self.section = section
        self.cmd = [sys.executable, '-m', 'IPython.testing.iptest', section]
        self.env = {}
        self.dirs = []
        ipydir = TemporaryDirectory()
        self.dirs.append(ipydir)
        self.env['IPYTHONDIR'] = ipydir.name
        workingdir = TemporaryDirectory()
        self.dirs.append(workingdir)
        self.env['IPTEST_WORKING_DIR'] = workingdir.name
    
    def add_xunit(self):
        xunit_file = os.path.abspath(self.section + '.xunit.xml')
        self.cmd.extend(['--with-xunit', '--xunit-file', xunit_file])
    
    def add_coverage(self, xml=True):
        self.cmd.extend(['--with-coverage', '--cover-package', self.section])
        if xml:
            coverage_xml = os.path.abspath(self.section + ".coverage.xml")
            self.cmd.extend(['--cover-xml', '--cover-xml-file', coverage_xml])
        

    def launch(self):
        # print('*** ENV:', self.env)  # dbg
        # print('*** CMD:', self.cmd)  # dbg
        env = os.environ.copy()
        env.update(self.env)
        output = subprocess.PIPE if self.buffer_output else None
        self.process = subprocess.Popen(self.cmd, stdout=output,
                stderr=output, env=env)

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

    def cleanup_process(self):
        """Cleanup on exit by killing any leftover processes."""
        subp = self.process
        if subp is None or (subp.poll() is not None):
            return  # Process doesn't exist, or is already dead.

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
    
    def cleanup(self):
        "Kill process if it's still alive, and clean up temporary directories"
        self.cleanup_process()
        for td in self.dirs:
            td.cleanup()
    
    __del__ = cleanup

def test_controllers_to_run(inc_slow=False):
    """Returns an ordered list of IPTestController instances to be run."""
    res = []
    if not inc_slow:
        test_sections['parallel'].enabled = False
    for name in test_group_names:
        if test_sections[name].will_run:
            res.append(IPTestController(name))
    return res

def do_run(controller):
    try:
        try:
            controller.launch()
        except Exception:
            import traceback
            traceback.print_exc()
            return controller, 1  # signal failure
    
        exitcode = controller.process.wait()
        controller.cleanup()
        return controller, exitcode
    
    except KeyboardInterrupt:
        controller.cleanup()
        return controller, -signal.SIGINT

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

def run_iptestall(inc_slow=False, jobs=1, xunit=False, coverage=False):
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
    pool = multiprocessing.pool.ThreadPool(jobs)
    if jobs != 1:
        IPTestController.buffer_output = True

    controllers = test_controllers_to_run(inc_slow=inc_slow)

    # Run all test runners, tracking execution time
    failed = []
    t_start = time.time()

    print('*'*70)
    for (controller, res) in pool.imap_unordered(do_run, controllers):
        tgroup = 'IPython test group: ' + controller.section
        res_string = 'OK' if res == 0 else 'FAILED'
        res_string = res_string.rjust(70 - len(tgroup), '.')
        print(tgroup + res_string)
        if res:
            failed.append(controller)
            if res == -signal.SIGINT:
                print("Interrupted")
                break
    
    t_end = time.time()
    t_tests = t_end - t_start
    nrunners = len(controllers)
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
        for controller in failed:
            print('-'*40)
            print('Runner failed:', controller.section)
            print('You may wish to rerun this one individually, with:')
            failed_call_args = [py3compat.cast_unicode(x) for x in controller.cmd]
            print(u' '.join(failed_call_args))
            print()
        # Ensure that our exit code indicates failure
        sys.exit(1)


def main():
    if len(sys.argv) > 1 and (sys.argv[1] in test_sections):
        from .iptest import run_iptest
        # This is in-process
        run_iptest()
        return
            
    parser = argparse.ArgumentParser(description='Run IPython test suite')
    parser.add_argument('--all', action='store_true',
                        help='Include slow tests not run by default.')
    parser.add_argument('-j', '--fast', nargs='?', const=None, default=1,
                        help='Run test sections in parallel.')
    parser.add_argument('--xunit', action='store_true',
                        help='Produce Xunit XML results')
    parser.add_argument('--coverage', action='store_true',
                        help='Measure test coverage.')

    options = parser.parse_args()

    # This starts subprocesses
    run_iptestall(inc_slow=options.all, jobs=options.fast,
                  xunit=options.xunit, coverage=options.coverage)


if __name__ == '__main__':
    main()
