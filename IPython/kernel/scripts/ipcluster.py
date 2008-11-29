#!/usr/bin/env python
# encoding: utf-8

"""Start an IPython cluster = (controller + engines)."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import re
import sys
import signal
pjoin = os.path.join

from twisted.internet import reactor, defer
from twisted.internet.protocol import ProcessProtocol
from twisted.python import failure, log
from twisted.internet.error import ProcessDone, ProcessTerminated
from twisted.internet.utils import getProcessOutput

from IPython.external import argparse
from IPython.external import Itpl
from IPython.kernel.twistedutil import gatherBoth
from IPython.kernel.util import printer
from IPython.genutils import get_ipython_dir, num_cpus

#-----------------------------------------------------------------------------
# General process handling code
#-----------------------------------------------------------------------------

def find_exe(cmd):
    try:
        import win32api
    except ImportError:
        raise ImportError('you need to have pywin32 installed for this to work')
    else:
        (path, offest) = win32api.SearchPath(os.environ['PATH'],cmd)
        return path

class ProcessStateError(Exception):
    pass

class UnknownStatus(Exception):
    pass

class LauncherProcessProtocol(ProcessProtocol):
    """
    A ProcessProtocol to go with the ProcessLauncher.
    """
    def __init__(self, process_launcher):
        self.process_launcher = process_launcher
    
    def connectionMade(self):
        self.process_launcher.fire_start_deferred(self.transport.pid)
    
    def processEnded(self, status):
        value = status.value
        if isinstance(value, ProcessDone):
            self.process_launcher.fire_stop_deferred(0)
        elif isinstance(value, ProcessTerminated):
            self.process_launcher.fire_stop_deferred(
                {'exit_code':value.exitCode,
                 'signal':value.signal,
                 'status':value.status
                }
            )
        else:
            raise UnknownStatus("unknown exit status, this is probably a bug in Twisted")

    def outReceived(self, data):
        log.msg(data)

    def errReceived(self, data):
        log.err(data)

class ProcessLauncher(object):
    """
    Start and stop an external process in an asynchronous manner.
    
    Currently this uses deferreds to notify other parties of process state
    changes.  This is an awkward design and should be moved to using
    a formal NotificationCenter.
    """
    def __init__(self, cmd_and_args):
        self.cmd = cmd_and_args[0]
        self.args = cmd_and_args
        self._reset()
    
    def _reset(self):
        self.process_protocol = None
        self.pid = None
        self.start_deferred = None
        self.stop_deferreds = []
        self.state = 'before' # before, running, or after
    
    @property
    def running(self):
        if self.state == 'running':
            return True
        else:
            return False
    
    def fire_start_deferred(self, pid):
        self.pid = pid
        self.state = 'running'
        log.msg('Process %r has started with pid=%i' % (self.args, pid))
        self.start_deferred.callback(pid)
    
    def start(self):
        if self.state == 'before':
            self.process_protocol = LauncherProcessProtocol(self)
            self.start_deferred = defer.Deferred()
            self.process_transport = reactor.spawnProcess(
                self.process_protocol,
                self.cmd,
                self.args,
                env=os.environ
            )
            return self.start_deferred
        else:
            s = 'the process has already been started and has state: %r' % \
                self.state
            return defer.fail(ProcessStateError(s))
    
    def get_stop_deferred(self):
        if self.state == 'running' or self.state == 'before':
            d = defer.Deferred()
            self.stop_deferreds.append(d)
            return d
        else:
            s = 'this process is already complete'
            return defer.fail(ProcessStateError(s))
    
    def fire_stop_deferred(self, exit_code):
        log.msg('Process %r has stopped with %r' % (self.args, exit_code))
        self.state = 'after'
        for d in self.stop_deferreds:
            d.callback(exit_code)
    
    def signal(self, sig):
        """
        Send a signal to the process.
        
        The argument sig can be ('KILL','INT', etc.) or any signal number.
        """
        if self.state == 'running':
            self.process_transport.signalProcess(sig)
    
    # def __del__(self):
    #     self.signal('KILL')
    
    def interrupt_then_kill(self, delay=1.0):
        self.signal('INT')
        reactor.callLater(delay, self.signal, 'KILL')


#-----------------------------------------------------------------------------
# Code for launching controller and engines
#-----------------------------------------------------------------------------


class ControllerLauncher(ProcessLauncher):
    
    def __init__(self, extra_args=None):
        if sys.platform == 'win32':
            args = [find_exe('ipcontroller.bat')]
        else:
            args = ['ipcontroller']
        self.extra_args = extra_args
        if extra_args is not None:
            args.extend(extra_args)
        
        ProcessLauncher.__init__(self, args)


class EngineLauncher(ProcessLauncher):
    
    def __init__(self, extra_args=None):
        if sys.platform == 'win32':
            args = [find_exe('ipengine.bat')]
        else:
            args = ['ipengine']
        self.extra_args = extra_args
        if extra_args is not None:
            args.extend(extra_args)
        
        ProcessLauncher.__init__(self, args)


class LocalEngineSet(object):
    
    def __init__(self, extra_args=None):
        self.extra_args = extra_args
        self.launchers = []
    
    def start(self, n):
        dlist = []
        for i in range(n):
            el = EngineLauncher(extra_args=self.extra_args)
            d = el.start()
            self.launchers.append(el)
            dlist.append(d)
        dfinal = gatherBoth(dlist, consumeErrors=True)
        dfinal.addCallback(self._handle_start)
        return dfinal
    
    def _handle_start(self, r):
        log.msg('Engines started with pids: %r' % r)
        return r
    
    def _handle_stop(self, r):
        log.msg('Engines received signal: %r' % r)
        return r
    
    def signal(self, sig):
        dlist = []
        for el in self.launchers:
            d = el.get_stop_deferred()
            dlist.append(d)
            el.signal(sig)
        dfinal = gatherBoth(dlist, consumeErrors=True)
        dfinal.addCallback(self._handle_stop)
        return dfinal
    
    def interrupt_then_kill(self, delay=1.0):
        dlist = []
        for el in self.launchers:
            d = el.get_stop_deferred()
            dlist.append(d)
            el.interrupt_then_kill(delay)
        dfinal = gatherBoth(dlist, consumeErrors=True)
        dfinal.addCallback(self._handle_stop)
        return dfinal


class BatchEngineSet(object):
    
    # Subclasses must fill these in.  See PBSEngineSet
    submit_command = ''
    delete_command = ''
    job_id_regexp = ''
    
    def __init__(self, template_file, **kwargs):
        self.template_file = template_file
        self.context = {}
        self.context.update(kwargs)
        self.batch_file = self.template_file+'-run'

    def parse_job_id(self, output):
        m = re.match(self.job_id_regexp, output)
        if m is not None:
            job_id = m.group()
        else:
            raise Exception("job id couldn't be determined: %s" % output)
        self.job_id = job_id
        log.msg('Job started with job id: %r' % job_id)
        return job_id
    
    def write_batch_script(self, n):
        self.context['n'] = n
        template = open(self.template_file, 'r').read()
        log.msg('Using template for batch script: %s' % self.template_file)
        script_as_string = Itpl.itplns(template, self.context)
        log.msg('Writing instantiated batch script: %s' % self.batch_file)
        f = open(self.batch_file,'w')
        f.write(script_as_string)
        f.close()

    def handle_error(self, f):
        f.printTraceback()
        f.raiseException()
    
    def start(self, n):
        self.write_batch_script(n)
        d = getProcessOutput(self.submit_command,
            [self.batch_file],env=os.environ)
        d.addCallback(self.parse_job_id)
        d.addErrback(self.handle_error)
        return d
        
    def kill(self):
        d = getProcessOutput(self.delete_command,
            [self.job_id],env=os.environ)
        return d

class PBSEngineSet(BatchEngineSet):
    
    submit_command = 'qsub'
    delete_command = 'qdel'
    job_id_regexp = '\d+'
    
    def __init__(self, template_file, **kwargs):
        BatchEngineSet.__init__(self, template_file, **kwargs)


#-----------------------------------------------------------------------------
# Main functions for the different types of clusters
#-----------------------------------------------------------------------------

# TODO:
# The logic in these codes should be moved into classes like LocalCluster
# MpirunCluster, PBSCluster, etc.  This would remove alot of the duplications.
# The main functions should then just parse the command line arguments, create
# the appropriate class and call a 'start' method.

def main_local(args):
    cont_args = []
    cont_args.append('--logfile=%s' % pjoin(args.logdir,'ipcontroller'))
    if args.x:
        cont_args.append('-x')
    if args.y:
        cont_args.append('-y')
    cl = ControllerLauncher(extra_args=cont_args)
    dstart = cl.start()
    def start_engines(cont_pid):
        engine_args = []
        engine_args.append('--logfile=%s' % \
            pjoin(args.logdir,'ipengine%s-' % cont_pid))
        eset = LocalEngineSet(extra_args=engine_args)
        def shutdown(signum, frame):
            log.msg('Stopping local cluster')
            # We are still playing with the times here, but these seem
            # to be reliable in allowing everything to exit cleanly.
            eset.interrupt_then_kill(0.5)
            cl.interrupt_then_kill(0.5)
            reactor.callLater(1.0, reactor.stop)
        signal.signal(signal.SIGINT,shutdown)
        d = eset.start(args.n)
        return d
    def delay_start(cont_pid):
        # This is needed because the controller doesn't start listening
        # right when it starts and the controller needs to write
        # furl files for the engine to pick up
        reactor.callLater(1.0, start_engines, cont_pid)
    dstart.addCallback(delay_start)
    dstart.addErrback(lambda f: f.raiseException())

def main_mpirun(args):
    cont_args = []
    cont_args.append('--logfile=%s' % pjoin(args.logdir,'ipcontroller'))
    if args.x:
        cont_args.append('-x')
    if args.y:
        cont_args.append('-y')
    cl = ControllerLauncher(extra_args=cont_args)
    dstart = cl.start()
    def start_engines(cont_pid):
        raw_args = ['mpirun']
        raw_args.extend(['-n',str(args.n)])
        raw_args.append('ipengine')
        raw_args.append('-l')
        raw_args.append(pjoin(args.logdir,'ipengine%s-' % cont_pid))
        if args.mpi:
            raw_args.append('--mpi=%s' % args.mpi)
        eset = ProcessLauncher(raw_args)
        def shutdown(signum, frame):
            log.msg('Stopping local cluster')
            # We are still playing with the times here, but these seem
            # to be reliable in allowing everything to exit cleanly.
            eset.interrupt_then_kill(1.0)
            cl.interrupt_then_kill(1.0)
            reactor.callLater(2.0, reactor.stop)
        signal.signal(signal.SIGINT,shutdown)
        d = eset.start()
        return d
    def delay_start(cont_pid):
        # This is needed because the controller doesn't start listening
        # right when it starts and the controller needs to write
        # furl files for the engine to pick up
        reactor.callLater(1.0, start_engines, cont_pid)
    dstart.addCallback(delay_start)
    dstart.addErrback(lambda f: f.raiseException())

def main_pbs(args):
    cont_args = []
    cont_args.append('--logfile=%s' % pjoin(args.logdir,'ipcontroller'))
    if args.x:
	cont_args.append('-x')
    if args.y:
	cont_args.append('-y')
    cl = ControllerLauncher(extra_args=cont_args)
    dstart = cl.start()
    def start_engines(r):
        pbs_set =  PBSEngineSet(args.pbsscript)
        def shutdown(signum, frame):
            log.msg('Stopping pbs cluster')
            d = pbs_set.kill()
            d.addBoth(lambda _: cl.interrupt_then_kill(1.0))
            d.addBoth(lambda _: reactor.callLater(2.0, reactor.stop))
        signal.signal(signal.SIGINT,shutdown)
        d = pbs_set.start(args.n)
        return d
    dstart.addCallback(start_engines)
    dstart.addErrback(lambda f: f.raiseException())


def get_args():
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument(
        '-x',
        action='store_true',
        dest='x',
        help='turn off client security'
    )
    base_parser.add_argument(
        '-y',
        action='store_true',
        dest='y',
        help='turn off engine security'
    )
    base_parser.add_argument(
        "--logdir", 
        type=str,
        dest="logdir",
        help="directory to put log files (default=$IPYTHONDIR/log)",
        default=pjoin(get_ipython_dir(),'log')
    )
    base_parser.add_argument(
        "-n",
        "--num", 
        type=int,
        dest="n",
        default=2,
        help="the number of engines to start"
    )
    
    parser = argparse.ArgumentParser(
        description='IPython cluster startup.  This starts a controller and\
        engines using various approaches.  THIS IS A TECHNOLOGY PREVIEW AND\
        THE API WILL CHANGE SIGNIFICANTLY BEFORE THE FINAL RELEASE.'
    )
    subparsers = parser.add_subparsers(
        help='available cluster types.  For help, do "ipcluster TYPE --help"')
    
    parser_local = subparsers.add_parser(
        'local',
        help='run a local cluster',
        parents=[base_parser]
    )
    parser_local.set_defaults(func=main_local)
    
    parser_mpirun = subparsers.add_parser(
        'mpirun',
        help='run a cluster using mpirun',
        parents=[base_parser]
    )
    parser_mpirun.add_argument(
        "--mpi",
        type=str,
        dest="mpi", # Don't put a default here to allow no MPI support
        help="how to call MPI_Init (default=mpi4py)"
    )
    parser_mpirun.set_defaults(func=main_mpirun)
    
    parser_pbs = subparsers.add_parser(
        'pbs', 
        help='run a pbs cluster',
        parents=[base_parser]
    )
    parser_pbs.add_argument(
        '--pbs-script',
        type=str, 
        dest='pbsscript',
        help='PBS script template',
        default='pbs.template'
    )
    parser_pbs.set_defaults(func=main_pbs)
    args = parser.parse_args()
    return args

def main():
    args = get_args()
    reactor.callWhenRunning(args.func, args)
    log.startLogging(sys.stdout)
    reactor.run()

if __name__ == '__main__':
    main()
