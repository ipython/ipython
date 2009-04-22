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
import tempfile
pjoin = os.path.join

from twisted.internet import reactor, defer
from twisted.internet.protocol import ProcessProtocol
from twisted.internet.error import ProcessDone, ProcessTerminated
from twisted.internet.utils import getProcessOutput
from twisted.python import failure, log

from IPython.external import argparse
from IPython.external import Itpl
from IPython.genutils import (
    get_ipython_dir, 
    get_log_dir, 
    get_security_dir, 
    num_cpus
)
from IPython.kernel.fcutil import have_crypto

# Create various ipython directories if they don't exist.
# This must be done before IPython.kernel.config is imported.
from IPython.iplib import user_setup
if os.name == 'posix':
    rc_suffix = ''
else:
    rc_suffix = '.ini'
user_setup(get_ipython_dir(), rc_suffix, mode='install', interactive=False)
get_log_dir()
get_security_dir()

from IPython.kernel.config import config_manager as kernel_config_manager
from IPython.kernel.error import SecurityError, FileTimeoutError
from IPython.kernel.fcutil import have_crypto
from IPython.kernel.twistedutil import gatherBoth, wait_for_file
from IPython.kernel.util import printer


#-----------------------------------------------------------------------------
# General process handling code
#-----------------------------------------------------------------------------

def find_exe(cmd):
    try:
        import win32api
    except ImportError:
        raise ImportError('you need to have pywin32 installed for this to work')
    else:
        try:
            (path, offest) = win32api.SearchPath(os.environ['PATH'],cmd + '.exe')
        except:
            (path, offset) = win32api.SearchPath(os.environ['PATH'],cmd + '.bat')
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
            # This logic is needed because the ipcontroller script doesn't
            # always get installed in the same way or in the same location.
            from IPython.kernel.scripts import ipcontroller
            script_location = ipcontroller.__file__.replace('.pyc', '.py')
            # The -u option here turns on unbuffered output, which is required
            # on Win32 to prevent wierd conflict and problems with Twisted.
            # Also, use sys.executable to make sure we are picking up the 
            # right python exe.
            args = [sys.executable, '-u', script_location]
        else:
            args = ['ipcontroller']
        self.extra_args = extra_args
        if extra_args is not None:
            args.extend(extra_args)
        
        ProcessLauncher.__init__(self, args)


class EngineLauncher(ProcessLauncher):
    
    def __init__(self, extra_args=None):
        if sys.platform == 'win32':
            # This logic is needed because the ipcontroller script doesn't
            # always get installed in the same way or in the same location.
            from IPython.kernel.scripts import ipengine
            script_location = ipengine.__file__.replace('.pyc', '.py')
            # The -u option here turns on unbuffered output, which is required
            # on Win32 to prevent wierd conflict and problems with Twisted.
            # Also, use sys.executable to make sure we are picking up the 
            # right python exe.
            args = [sys.executable, '-u', script_location]
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


sshx_template="""#!/bin/sh
"$@" &> /dev/null &
echo $!
"""

engine_killer_template="""#!/bin/sh
ps -fu `whoami` | grep '[i]pengine' | awk '{print $2}' | xargs kill -TERM
"""

class SSHEngineSet(object):
    sshx_template=sshx_template
    engine_killer_template=engine_killer_template
    
    def __init__(self, engine_hosts, sshx=None, ipengine="ipengine"):
        """Start a controller on localhost and engines using ssh.
        
        The engine_hosts argument is a dict with hostnames as keys and
        the number of engine (int) as values.  sshx is the name of a local
        file that will be used to run remote commands.  This file is used
        to setup the environment properly.
        """
        
        self.temp_dir = tempfile.gettempdir()
        if sshx is not None:
            self.sshx = sshx
        else:
            # Write the sshx.sh file locally from our template.
            self.sshx = os.path.join(
                self.temp_dir,
                '%s-main-sshx.sh' % os.environ['USER']
            )
            f = open(self.sshx, 'w')
            f.writelines(self.sshx_template)
            f.close()
        self.engine_command = ipengine
        self.engine_hosts = engine_hosts
        # Write the engine killer script file locally from our template.
        self.engine_killer = os.path.join(
            self.temp_dir,  
            '%s-local-engine_killer.sh' % os.environ['USER']
        )
        f = open(self.engine_killer, 'w')
        f.writelines(self.engine_killer_template)
        f.close()
    
    def start(self, send_furl=False):
        dlist = []
        for host in self.engine_hosts.keys():
            count = self.engine_hosts[host]
            d = self._start(host, count, send_furl)
            dlist.append(d)
        return gatherBoth(dlist, consumeErrors=True)
    
    def _start(self, hostname, count=1, send_furl=False):
        if send_furl:
            d = self._scp_furl(hostname)
        else:
            d = defer.succeed(None)
        d.addCallback(lambda r: self._scp_sshx(hostname))
        d.addCallback(lambda r: self._ssh_engine(hostname, count))
        return d
        
    def _scp_furl(self, hostname):
        scp_cmd = "scp ~/.ipython/security/ipcontroller-engine.furl %s:.ipython/security/" % (hostname)
        cmd_list = scp_cmd.split()
        cmd_list[1] = os.path.expanduser(cmd_list[1])
        log.msg('Copying furl file: %s' % scp_cmd)
        d = getProcessOutput(cmd_list[0], cmd_list[1:], env=os.environ) 
        return d
    
    def _scp_sshx(self, hostname):
        scp_cmd = "scp %s %s:%s/%s-sshx.sh" % (
            self.sshx, hostname, 
            self.temp_dir, os.environ['USER']
        )
        print
        log.msg("Copying sshx: %s" % scp_cmd)
        sshx_scp = scp_cmd.split()
        d = getProcessOutput(sshx_scp[0], sshx_scp[1:], env=os.environ)
        return d
    
    def _ssh_engine(self, hostname, count):
        exec_engine = "ssh %s sh %s/%s-sshx.sh %s" % (
            hostname, self.temp_dir, 
            os.environ['USER'], self.engine_command
        )
        cmds = exec_engine.split()
        dlist = []
        log.msg("about to start engines...")
        for i in range(count):
            log.msg('Starting engines: %s' % exec_engine)
            d = getProcessOutput(cmds[0], cmds[1:], env=os.environ)
            dlist.append(d)
        return gatherBoth(dlist, consumeErrors=True)
    
    def kill(self):
        dlist = []
        for host in self.engine_hosts.keys():
            d = self._killall(host)
            dlist.append(d)
        return gatherBoth(dlist, consumeErrors=True)
    
    def _killall(self, hostname):
        d = self._scp_engine_killer(hostname)
        d.addCallback(lambda r: self._ssh_kill(hostname))
        # d.addErrback(self._exec_err)
        return d

    def _scp_engine_killer(self, hostname):
        scp_cmd = "scp %s %s:%s/%s-engine_killer.sh" % (
            self.engine_killer, 
            hostname, 
            self.temp_dir, 
            os.environ['USER']
        )
        cmds = scp_cmd.split()
        log.msg('Copying engine_killer: %s' % scp_cmd)
        d = getProcessOutput(cmds[0], cmds[1:], env=os.environ)
        return d
    
    def _ssh_kill(self, hostname):
        kill_cmd = "ssh %s sh %s/%s-engine_killer.sh" % (
            hostname,
            self.temp_dir, 
            os.environ['USER']
        )
        log.msg('Killing engine: %s' % kill_cmd)
        kill_cmd = kill_cmd.split()
        d = getProcessOutput(kill_cmd[0], kill_cmd[1:], env=os.environ)
        return d

    def _exec_err(self, r):
        log.msg(r)

#-----------------------------------------------------------------------------
# Main functions for the different types of clusters
#-----------------------------------------------------------------------------

# TODO:
# The logic in these codes should be moved into classes like LocalCluster
# MpirunCluster, PBSCluster, etc.  This would remove alot of the duplications.
# The main functions should then just parse the command line arguments, create
# the appropriate class and call a 'start' method.


def check_security(args, cont_args):
    """Check to see if we should run with SSL support."""
    if (not args.x or not args.y) and not have_crypto:
        log.err("""
OpenSSL/pyOpenSSL is not available, so we can't run in secure mode.
Try running ipcluster with the -xy flags:  ipcluster local -xy -n 4""")
        reactor.stop()
        return False
    if args.x:
        cont_args.append('-x')
    if args.y:
        cont_args.append('-y')
    return True


def check_reuse(args, cont_args):
    """Check to see if we should try to resuse FURL files."""
    if args.r:
        cont_args.append('-r')
        if args.client_port == 0 or args.engine_port == 0:
            log.err("""
To reuse FURL files, you must also set the client and engine ports using
the --client-port and --engine-port options.""")
            reactor.stop()
            return False
        cont_args.append('--client-port=%i' % args.client_port)
        cont_args.append('--engine-port=%i' % args.engine_port)
    return True


def _err_and_stop(f):
    """Errback to log a failure and halt the reactor on a fatal error."""
    log.err(f)
    reactor.stop()


def _delay_start(cont_pid, start_engines, furl_file, reuse):
    """Wait for controller to create FURL files and the start the engines."""
    if not reuse:
        if os.path.isfile(furl_file):
            os.unlink(furl_file)
    log.msg('Waiting for controller to finish starting...')
    d = wait_for_file(furl_file, delay=0.2, max_tries=50)
    d.addCallback(lambda _: log.msg('Controller started'))
    d.addCallback(lambda _: start_engines(cont_pid))
    return d


def main_local(args):
    cont_args = []
    cont_args.append('--logfile=%s' % pjoin(args.logdir,'ipcontroller'))
    
    # Check security settings before proceeding
    if not check_security(args, cont_args):
        return
    
    # See if we are reusing FURL files
    if not check_reuse(args, cont_args):
        return
    
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
    config = kernel_config_manager.get_config_obj()
    furl_file = config['controller']['engine_furl_file']
    dstart.addCallback(_delay_start, start_engines, furl_file, args.r)
    dstart.addErrback(_err_and_stop)


def main_mpi(args):
    cont_args = []
    cont_args.append('--logfile=%s' % pjoin(args.logdir,'ipcontroller'))
    
    # Check security settings before proceeding
    if not check_security(args, cont_args):
        return
    
    # See if we are reusing FURL files
    if not check_reuse(args, cont_args):
        return
    
    cl = ControllerLauncher(extra_args=cont_args)
    dstart = cl.start()
    def start_engines(cont_pid):
        raw_args = [args.cmd]
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
    config = kernel_config_manager.get_config_obj()
    furl_file = config['controller']['engine_furl_file']
    dstart.addCallback(_delay_start, start_engines, furl_file, args.r)
    dstart.addErrback(_err_and_stop)


def main_pbs(args):
    cont_args = []
    cont_args.append('--logfile=%s' % pjoin(args.logdir,'ipcontroller'))
    
    # Check security settings before proceeding
    if not check_security(args, cont_args):
        return
    
    # See if we are reusing FURL files
    if not check_reuse(args, cont_args):
        return
    
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
    config = kernel_config_manager.get_config_obj()
    furl_file = config['controller']['engine_furl_file']
    dstart.addCallback(_delay_start, start_engines, furl_file, args.r)
    dstart.addErrback(_err_and_stop)


def main_ssh(args):
    """Start a controller on localhost and engines using ssh.
    
    Your clusterfile should look like::
    
        send_furl = False # True, if you want 
        engines = {
            'engine_host1' : engine_count, 
            'engine_host2' : engine_count2
        } 
    """
    clusterfile = {}
    execfile(args.clusterfile, clusterfile)
    if not clusterfile.has_key('send_furl'):
        clusterfile['send_furl'] = False
        
    cont_args = []
    cont_args.append('--logfile=%s' % pjoin(args.logdir,'ipcontroller'))
    
    # Check security settings before proceeding
    if not check_security(args, cont_args):
        return
    
    # See if we are reusing FURL files
    if not check_reuse(args, cont_args):
        return
    
    cl = ControllerLauncher(extra_args=cont_args)
    dstart = cl.start()
    def start_engines(cont_pid):
        ssh_set = SSHEngineSet(clusterfile['engines'], sshx=args.sshx)
        def shutdown(signum, frame):
            d = ssh_set.kill()
            cl.interrupt_then_kill(1.0)
            reactor.callLater(2.0, reactor.stop)
        signal.signal(signal.SIGINT,shutdown)
        d = ssh_set.start(clusterfile['send_furl'])
        return d
    config = kernel_config_manager.get_config_obj()
    furl_file = config['controller']['engine_furl_file']
    dstart.addCallback(_delay_start, start_engines, furl_file, args.r)
    dstart.addErrback(_err_and_stop)


def get_args():
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument(
        '-r',
        action='store_true',
        dest='r',
        help='try to reuse FURL files.  Use with --client-port and --engine-port'
    )
    base_parser.add_argument(
        '--client-port',
        type=int,
        dest='client_port',
        help='the port the controller will listen on for client connections',
        default=0
    )
    base_parser.add_argument(
        '--engine-port',
        type=int,
        dest='engine_port',
        help='the port the controller will listen on for engine connections',
        default=0
    )
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
        help='run a cluster using mpirun (mpiexec also works)',
        parents=[base_parser]
    )
    parser_mpirun.add_argument(
        "--mpi",
        type=str,
        dest="mpi", # Don't put a default here to allow no MPI support
        help="how to call MPI_Init (default=mpi4py)"
    )
    parser_mpirun.set_defaults(func=main_mpi, cmd='mpirun')

    parser_mpiexec = subparsers.add_parser(
        'mpiexec',
        help='run a cluster using mpiexec (mpirun also works)',
        parents=[base_parser]
    )
    parser_mpiexec.add_argument(
        "--mpi",
        type=str,
        dest="mpi", # Don't put a default here to allow no MPI support
        help="how to call MPI_Init (default=mpi4py)"
    )
    parser_mpiexec.set_defaults(func=main_mpi, cmd='mpiexec')
    
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
    
    parser_ssh = subparsers.add_parser(
        'ssh',
        help='run a cluster using ssh, should have ssh-keys setup',
        parents=[base_parser]
    )
    parser_ssh.add_argument(
        '--clusterfile', 
        type=str,
        dest='clusterfile',
        help='python file describing the cluster',
        default='clusterfile.py',
    )
    parser_ssh.add_argument(
        '--sshx', 
        type=str,
        dest='sshx',
        help='sshx launcher helper'
    )
    parser_ssh.set_defaults(func=main_ssh)
    
    args = parser.parse_args()
    return args

def main():
    args = get_args()
    reactor.callWhenRunning(args.func, args)
    log.startLogging(sys.stdout)
    reactor.run()

if __name__ == '__main__':
    main()
