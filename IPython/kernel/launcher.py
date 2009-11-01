#!/usr/bin/env python
# encoding: utf-8
"""
Facilities for launching processing asynchronously.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
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

from IPython.core.component import Component
from IPython.external import Itpl
from IPython.utils.traitlets import Str, Int, List, Unicode
from IPython.kernel.twistedutil import gatherBoth, make_deferred, sleep_deferred

from twisted.internet import reactor, defer
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import ProcessProtocol
from twisted.internet.utils import getProcessOutput
from twisted.internet.error import ProcessDone, ProcessTerminated
from twisted.python import log
from twisted.python.failure import Failure

#-----------------------------------------------------------------------------
# Generic launchers
#-----------------------------------------------------------------------------


class LauncherError(Exception):
    pass


class ProcessStateError(LauncherError):
    pass


class UnknownStatus(LauncherError):
    pass


class BaseLauncher(Component):
    """An asbtraction for starting, stopping and signaling a process."""

    # A directory for files related to the process. But, we don't cd to 
    # this directory, 
    working_dir = Unicode(u'')

    def __init__(self, working_dir, parent=None, name=None, config=None):
        super(BaseLauncher, self).__init__(parent, name, config)
        self.working_dir = working_dir
        self.state = 'before' # can be before, running, after
        self.stop_deferreds = []
        self.start_data = None
        self.stop_data = None

    @property
    def args(self):
        """A list of cmd and args that will be used to start the process.

        This is what is passed to :func:`spawnProcess` and the first element
        will be the process name.
        """
        return self.find_args()

    def find_args(self):
        """The ``.args`` property calls this to find the args list.

        Subcommand should implement this to construct the cmd and args.
        """
        raise NotImplementedError('find_args must be implemented in a subclass')

    @property
    def arg_str(self):
        """The string form of the program arguments."""
        return ' '.join(self.args)

    @property
    def running(self):
        """Am I running."""
        if self.state == 'running':
            return True
        else:
            return False

    def start(self):
        """Start the process.

        This must return a deferred that fires with information about the
        process starting (like a pid, job id, etc.).
        """
        return defer.fail(
            Failure(NotImplementedError(
                'start must be implemented in a subclass')
            )
        )

    def stop(self):
        """Stop the process and notify observers of stopping.

        This must return a deferred that fires with information about the
        processing stopping, like errors that occur while the process is
        attempting to be shut down. This deferred won't fire when the process
        actually stops. To observe the actual process stopping, see
        :func:`observe_stop`.
        """
        return defer.fail(
            Failure(NotImplementedError(
                'stop must be implemented in a subclass')
            )
        )

    def observe_stop(self):
        """Get a deferred that will fire when the process stops.

        The deferred will fire with data that contains information about
        the exit status of the process.
        """
        if self.state=='after':
            return defer.succeed(self.stop_data)
        else:
            d = defer.Deferred()
            self.stop_deferreds.append(d)
            return d

    def notify_start(self, data):
        """Call this to trigger startup actions.

        This logs the process startup and sets the state to 'running'.  It is
        a pass-through so it can be used as a callback.
        """

        log.msg('Process %r started: %r' % (self.args[0], data))
        self.start_data = data
        self.state = 'running'
        return data

    def notify_stop(self, data):
        """Call this to trigger process stop actions.

        This logs the process stopping and sets the state to 'after'. Call
        this to trigger all the deferreds from :func:`observe_stop`."""

        log.msg('Process %r stopped: %r' % (self.args[0], data))
        self.stop_data = data
        self.state = 'after'
        for i in range(len(self.stop_deferreds)):
            d = self.stop_deferreds.pop()
            d.callback(data)
        return data

    def signal(self, sig):
        """Signal the process.

        Return a semi-meaningless deferred after signaling the process.

        Parameters
        ----------
        sig : str or int
            'KILL', 'INT', etc., or any signal number
        """
        return defer.fail(
            Failure(NotImplementedError(
                'signal must be implemented in a subclass')
            )
        )


class LocalProcessLauncherProtocol(ProcessProtocol):
    """A ProcessProtocol to go with the LocalProcessLauncher."""

    def __init__(self, process_launcher):
        self.process_launcher = process_launcher
        self.pid = None

    def connectionMade(self):
        self.pid = self.transport.pid
        self.process_launcher.notify_start(self.transport.pid)

    def processEnded(self, status):
        value = status.value
        if isinstance(value, ProcessDone):
            self.process_launcher.notify_stop(
                {'exit_code':0,
                 'signal':None,
                 'status':None,
                 'pid':self.pid
                }
            )
        elif isinstance(value, ProcessTerminated):
            self.process_launcher.notify_stop(
                {'exit_code':value.exitCode,
                 'signal':value.signal,
                 'status':value.status,
                 'pid':self.pid
                }
            )
        else:
            raise UnknownStatus("Unknown exit status, this is probably a "
                                "bug in Twisted")

    def outReceived(self, data):
        log.msg(data)

    def errReceived(self, data):
        log.err(data)


class LocalProcessLauncher(BaseLauncher):
    """Start and stop an external process in an asynchronous manner."""

    # This is used to to construct self.args, which is passed to 
    # spawnProcess.
    cmd_and_args = List([])

    def __init__(self, working_dir, parent=None, name=None, config=None):
        super(LocalProcessLauncher, self).__init__(
            working_dir, parent, name, config
        )
        self.process_protocol = None
        self.start_deferred = None

    def find_args(self):
        return self.cmd_and_args

    def start(self):
        if self.state == 'before':
            self.process_protocol = LocalProcessLauncherProtocol(self)
            self.start_deferred = defer.Deferred()
            self.process_transport = reactor.spawnProcess(
                self.process_protocol,
                str(self.args[0]),
                [str(a) for a in self.args],
                env=os.environ
            )
            return self.start_deferred
        else:
            s = 'The process was already started and has state: %r' % self.state
            return defer.fail(ProcessStateError(s))

    def notify_start(self, data):
        super(LocalProcessLauncher, self).notify_start(data)
        self.start_deferred.callback(data)

    def stop(self):
        return self.interrupt_then_kill()

    @make_deferred
    def signal(self, sig):
        if self.state == 'running':
            self.process_transport.signalProcess(sig)

    @inlineCallbacks
    def interrupt_then_kill(self, delay=2.0):
        """Send INT, wait a delay and then send KILL."""
        yield self.signal('INT')
        yield sleep_deferred(delay)
        yield self.signal('KILL')


class MPIExecLauncher(LocalProcessLauncher):
    """Launch an external process using mpiexec."""

    # The mpiexec command to use in starting the process.
    mpi_cmd = List(['mpiexec'], config=True)
    # The command line arguments to pass to mpiexec.
    mpi_args = List([], config=True)
    # The program to start using mpiexec.
    program = List(['date'], config=True)
    # The command line argument to the program.
    program_args = List([], config=True)
    # The number of instances of the program to start.
    n = Int(1, config=True)

    def find_args(self):
        """Build self.args using all the fields."""
        return self.mpi_cmd + ['-n', self.n] + self.mpi_args + \
               self.program + self.program_args

    def start(self, n):
        """Start n instances of the program using mpiexec."""
        self.n = n
        return super(MPIExecLauncher, self).start()


class SSHLauncher(BaseLauncher):
    """A minimal launcher for ssh.

    To be useful this will probably have to be extended to use the ``sshx``
    idea for environment variables.  There could be other things this needs
    as well.
    """

    ssh_cmd = List(['ssh'], config=True)
    ssh_args = List([], config=True)
    program = List(['date'], config=True)
    program_args = List([], config=True)
    hostname = Str('', config=True)
    user = Str(os.environ['USER'], config=True)
    location = Str('')

    def _hostname_changed(self, name, old, new):
        self.location = '%s@%s' % (self.user, new)

    def _user_changed(self, name, old, new):
        self.location = '%s@%s' % (new, self.hostname)

    def find_args(self):
        return self.ssh_cmd + self.ssh_args + [self.location] + \
               self.program + self.program_args

    def start(self, n, hostname=None, user=None):
        if hostname is not None:
            self.hostname = hostname
        if user is not None:
            self.user = user
        return super(SSHLauncher, self).start()


class WindowsHPCLauncher(BaseLauncher):
    pass


class BatchSystemLauncher(BaseLauncher):
    """Launch an external process using a batch system.

    This class is designed to work with UNIX batch systems like PBS, LSF,
    GridEngine, etc.  The overall model is that there are different commands
    like qsub, qdel, etc. that handle the starting and stopping of the process.

    This class also has the notion of a batch script. The ``batch_template``
    attribute can be set to a string that is a template for the batch script.
    This template is instantiated using Itpl. Thus the template can use
    ${n} fot the number of instances. Subclasses can add additional variables
    to the template dict.
    """

    # Subclasses must fill these in.  See PBSEngineSet
    # The name of the command line program used to submit jobs.
    submit_command = Str('', config=True)
    # The name of the command line program used to delete jobs.
    delete_command = Str('', config=True)
    # A regular expression used to get the job id from the output of the 
    # submit_command.
    job_id_regexp = Str('', config=True)
    # The string that is the batch script template itself.
    batch_template = Str('', config=True)
    # The filename of the instantiated batch script.
    batch_file_name = Unicode(u'batch_script', config=True)
    # The full path to the instantiated batch script.
    batch_file = Unicode(u'')

    def __init__(self, working_dir, parent=None, name=None, config=None):
        super(BatchSystemLauncher, self).__init__(
            working_dir, parent, name, config
        )
        self.batch_file = os.path.join(self.working_dir, self.batch_file_name)
        self.context = {}

    def parse_job_id(self, output):
        """Take the output of the submit command and return the job id."""
        m = re.match(self.job_id_regexp, output)
        if m is not None:
            job_id = m.group()
        else:
            raise LauncherError("Job id couldn't be determined: %s" % output)
        self.job_id = job_id
        log.msg('Job started with job id: %r' % job_id)
        return job_id

    def write_batch_script(self, n):
        """Instantiate and write the batch script to the working_dir."""
        self.context['n'] = n
        script_as_string = Itpl.itplns(self.batch_template, self.context)
        log.msg('Writing instantiated batch script: %s' % self.batch_file)
        f = open(self.batch_file, 'w')
        f.write(script_as_string)
        f.close()

    @inlineCallbacks
    def start(self, n):
        """Start n copies of the process using a batch system."""
        self.write_batch_script(n)
        output = yield getProcessOutput(self.submit_command,
            [self.batch_file], env=os.environ)
        job_id = self.parse_job_id(output)
        self.notify_start(job_id)
        defer.returnValue(job_id)

    @inlineCallbacks
    def stop(self):
        output = yield getProcessOutput(self.delete_command,
            [self.job_id], env=os.environ
        )
        self.notify_stop(output)  # Pass the output of the kill cmd
        defer.returnValue(output)


class PBSLauncher(BatchSystemLauncher):
    """A BatchSystemLauncher subclass for PBS."""

    submit_command = Str('qsub', config=True)
    delete_command = Str('qdel', config=True)
    job_id_regexp = Str('\d+', config=True)
    batch_template = Str('', config=True)
    batch_file_name = Unicode(u'pbs_batch_script', config=True)
    batch_file = Unicode(u'')


#-----------------------------------------------------------------------------
# Controller launchers
#-----------------------------------------------------------------------------

def find_controller_cmd():
    """Find the command line ipcontroller program in a cross platform way."""
    if sys.platform == 'win32':
        # This logic is needed because the ipcontroller script doesn't
        # always get installed in the same way or in the same location.
        from IPython.kernel import ipcontrollerapp
        script_location = ipcontrollerapp.__file__.replace('.pyc', '.py')
        # The -u option here turns on unbuffered output, which is required
        # on Win32 to prevent wierd conflict and problems with Twisted.
        # Also, use sys.executable to make sure we are picking up the 
        # right python exe.
        cmd = [sys.executable, '-u', script_location]
    else:
        # ipcontroller has to be on the PATH in this case.
        cmd = ['ipcontroller']
    return cmd


class LocalControllerLauncher(LocalProcessLauncher):
    """Launch a controller as a regular external process."""

    controller_cmd = List(find_controller_cmd())
    # Command line arguments to ipcontroller.
    controller_args = List(['--log-to-file','--log-level', '40'], config=True)

    def find_args(self):
        return self.controller_cmd + self.controller_args

    def start(self, profile=None, cluster_dir=None):
        """Start the controller by profile or cluster_dir."""
        if cluster_dir is not None:
            self.controller_args.extend(['--cluster-dir', cluster_dir])
        if profile is not None:
            self.controller_args.extend(['--profile', profile])
        log.msg("Starting LocalControllerLauncher: %r" % self.args)
        return super(LocalControllerLauncher, self).start()


class WindowsHPCControllerLauncher(WindowsHPCLauncher):
    pass


class MPIExecControllerLauncher(MPIExecLauncher):
    """Launch a controller using mpiexec."""

    controller_cmd = List(find_controller_cmd(), config=False)
    # Command line arguments to ipcontroller.
    controller_args = List(['--log-to-file','--log-level', '40'], config=True)
    n = Int(1, config=False)

    def start(self, profile=None, cluster_dir=None):
        """Start the controller by profile or cluster_dir."""
        if cluster_dir is not None:
            self.controller_args.extend(['--cluster-dir', cluster_dir])
        if profile is not None:
            self.controller_args.extend(['--profile', profile])
        log.msg("Starting MPIExecControllerLauncher: %r" % self.args)
        return super(MPIExecControllerLauncher, self).start(1)

    def find_args(self):
        return self.mpi_cmd + ['-n', self.n] + self.mpi_args + \
               self.controller_cmd + self.controller_args


class PBSControllerLauncher(PBSLauncher):
    """Launch a controller using PBS."""

    batch_file_name = Unicode(u'pbs_batch_script_controller', config=True)

    def start(self, profile=None, cluster_dir=None):
        """Start the controller by profile or cluster_dir."""
        # Here we save profile and cluster_dir in the context so they
        # can be used in the batch script template as ${profile} and
        # ${cluster_dir}
        if cluster_dir is not None:
            self.context['cluster_dir'] = cluster_dir
        if profile is not None:
            self.context['profile'] = profile
        log.msg("Starting PBSControllerLauncher: %r" % self.args)
        return super(PBSControllerLauncher, self).start(1)


class SSHControllerLauncher(SSHLauncher):
    pass


#-----------------------------------------------------------------------------
# Engine launchers
#-----------------------------------------------------------------------------


def find_engine_cmd():
    """Find the command line ipengine program in a cross platform way."""
    if sys.platform == 'win32':
        # This logic is needed because the ipengine script doesn't
        # always get installed in the same way or in the same location.
        from IPython.kernel import ipengineapp
        script_location = ipengineapp.__file__.replace('.pyc', '.py')
        # The -u option here turns on unbuffered output, which is required
        # on Win32 to prevent wierd conflict and problems with Twisted.
        # Also, use sys.executable to make sure we are picking up the 
        # right python exe.
        cmd = [sys.executable, '-u', script_location]
    else:
        # ipcontroller has to be on the PATH in this case.
        cmd = ['ipengine']
    return cmd


class LocalEngineLauncher(LocalProcessLauncher):
    """Launch a single engine as a regular externall process."""

    engine_cmd = List(find_engine_cmd())
    # Command line arguments for ipengine.
    engine_args = List(
        ['--log-to-file','--log-level', '40'], config=True
    )

    def find_args(self):
        return self.engine_cmd + self.engine_args

    def start(self, profile=None, cluster_dir=None):
        """Start the engine by profile or cluster_dir."""
        if cluster_dir is not None:
            self.engine_args.extend(['--cluster-dir', cluster_dir])
        if profile is not None:
            self.engine_args.extend(['--profile', profile])
        return super(LocalEngineLauncher, self).start()


class LocalEngineSetLauncher(BaseLauncher):
    """Launch a set of engines as regular external processes."""

    # Command line arguments for ipengine.
    engine_args = List(
        ['--log-to-file','--log-level', '40'], config=True
    )

    def __init__(self, working_dir, parent=None, name=None, config=None):
        super(LocalEngineSetLauncher, self).__init__(
            working_dir, parent, name, config
        )
        self.launchers = []

    def start(self, n, profile=None, cluster_dir=None):
        """Start n engines by profile or cluster_dir."""
        dlist = []
        for i in range(n):
            el = LocalEngineLauncher(self.working_dir, self)
            # Copy the engine args over to each engine launcher.
            import copy
            el.engine_args = copy.deepcopy(self.engine_args)
            d = el.start(profile, cluster_dir)
            if i==0:
                log.msg("Starting LocalEngineSetLauncher: %r" % el.args)
            self.launchers.append(el)
            dlist.append(d)
        # The consumeErrors here could be dangerous
        dfinal = gatherBoth(dlist, consumeErrors=True)
        dfinal.addCallback(self.notify_start)
        return dfinal

    def find_args(self):
        return ['engine set']

    def signal(self, sig):
        dlist = []
        for el in self.launchers:
            d = el.signal(sig)
            dlist.append(d)
        dfinal = gatherBoth(dlist, consumeErrors=True)
        return dfinal

    def interrupt_then_kill(self, delay=1.0):
        dlist = []
        for el in self.launchers:
            d = el.interrupt_then_kill(delay)
            dlist.append(d)
        dfinal = gatherBoth(dlist, consumeErrors=True)
        return dfinal

    def stop(self):
        return self.interrupt_then_kill()

    def observe_stop(self):
        dlist = [el.observe_stop() for el in self.launchers]
        dfinal = gatherBoth(dlist, consumeErrors=False)
        dfinal.addCallback(self.notify_stop)
        return dfinal


class MPIExecEngineSetLauncher(MPIExecLauncher):

    engine_cmd = List(find_engine_cmd(), config=False)
    # Command line arguments for ipengine.
    engine_args = List(
        ['--log-to-file','--log-level', '40'], config=True
    )    
    n = Int(1, config=True)

    def start(self, n, profile=None, cluster_dir=None):
        """Start n engines by profile or cluster_dir."""
        if cluster_dir is not None:
            self.engine_args.extend(['--cluster-dir', cluster_dir])
        if profile is not None:
            self.engine_args.extend(['--profile', profile])
        log.msg('Starting MPIExecEngineSetLauncher: %r' % self.args)
        return super(MPIExecEngineSetLauncher, self).start(n)

    def find_args(self):
        return self.mpi_cmd + ['-n', self.n] + self.mpi_args + \
               self.engine_cmd + self.engine_args


class WindowsHPCEngineSetLauncher(WindowsHPCLauncher):
    pass


class PBSEngineSetLauncher(PBSLauncher):

    batch_file_name = Unicode(u'pbs_batch_script_engines', config=True)

    def start(self, n, profile=None, cluster_dir=None):
        """Start n engines by profile or cluster_dir."""
        if cluster_dir is not None:
            self.program_args.extend(['--cluster-dir', cluster_dir])
        if profile is not None:
            self.program_args.extend(['-p', profile])
        log.msg('Starting PBSEngineSetLauncher: %r' % self.args)
        return super(PBSEngineSetLauncher, self).start(n)


class SSHEngineSetLauncher(BaseLauncher):
    pass


#-----------------------------------------------------------------------------
# A launcher for ipcluster itself!
#-----------------------------------------------------------------------------


def find_ipcluster_cmd():
    """Find the command line ipcluster program in a cross platform way."""
    if sys.platform == 'win32':
        # This logic is needed because the ipcluster script doesn't
        # always get installed in the same way or in the same location.
        from IPython.kernel import ipclusterapp
        script_location = ipclusterapp.__file__.replace('.pyc', '.py')
        # The -u option here turns on unbuffered output, which is required
        # on Win32 to prevent wierd conflict and problems with Twisted.
        # Also, use sys.executable to make sure we are picking up the 
        # right python exe.
        cmd = [sys.executable, '-u', script_location]
    else:
        # ipcontroller has to be on the PATH in this case.
        cmd = ['ipcluster']
    return cmd


class IPClusterLauncher(LocalProcessLauncher):
    """Launch the ipcluster program in an external process."""

    ipcluster_cmd = List(find_ipcluster_cmd())
    # Command line arguments to pass to ipcluster.
    ipcluster_args = List(
        ['--clean-logs', '--log-to-file', '--log-level', '40'], config=True)
    ipcluster_subcommand = Str('start')
    ipcluster_n = Int(2)

    def find_args(self):
        return self.ipcluster_cmd + [self.ipcluster_subcommand] + \
            ['-n', repr(self.ipcluster_n)] + self.ipcluster_args

    def start(self):
        log.msg("Starting ipcluster: %r" % self.args)
        return super(IPClusterLauncher, self).start()

