#!/usr/bin/env python
"""Master test runner for IPython - EXPERIMENTAL CODE!!!

This tries

XXX - Big limitation right now: we don't summarize the total test counts.  That
would require parsing the output of the subprocesses.
"""
import os.path as path
import subprocess as subp
import time

class IPTester(object):
    """Object to call iptest with specific parameters.
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
        return subp.call(self.call_args)


def make_runners():
    top_mod = \
      ['background_jobs.py', 'ColorANSI.py', 'completer.py', 'ConfigLoader.py',
       'CrashHandler.py', 'Debugger.py', 'deep_reload.py', 'demo.py',
       'DPyGetOpt.py', 'dtutils.py', 'excolors.py', 'FakeModule.py',
       'generics.py', 'genutils.py', 'Gnuplot2.py', 'GnuplotInteractive.py',
       'GnuplotRuntime.py', 'history.py', 'hooks.py', 'ipapi.py',
       'iplib.py', 'ipmaker.py', 'ipstruct.py', 'irunner.py', 'Itpl.py',
       'Logger.py', 'macro.py', 'Magic.py', 'numutils.py', 'OInspect.py',
       'OutputTrap.py', 'platutils_dummy.py', 'platutils_posix.py',
       'platutils.py', 'platutils_win32.py', 'prefilter.py', 'Prompts.py',
       'PyColorize.py', 'Release.py', 'rlineimpl.py', 'shadowns.py',
       'shellglobals.py', 'Shell.py', 'strdispatch.py', 'twshell.py',
       'ultraTB.py', 'upgrade_dir.py', 'usage.py', 'wildcard.py',
       'winconsole.py']

    top_pack = ['config','Extensions','frontend','gui','kernel',
                'testing','tests','tools','UserConfig']

    modules  = ['IPython.%s' % m for m in top_mod ]
    packages = ['IPython.%s' % m for m in top_pack ]

    # Make runners
    runners = dict(zip(top_pack, [IPTester(params=v) for v in packages]))
    runners['trial'] = IPTester('trial',['IPython'])

    return runners

    
def main():
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


if __name__ == '__main__':
    main()
