#!/usr/bin/env python
# encoding: utf-8
"""
Facilities for launching IPython processes asynchronously.
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
import logging

from signal import SIGINT, SIGTERM
try:
    from signal import SIGKILL
except ImportError:
    SIGKILL=SIGTERM

from subprocess import Popen, PIPE, STDOUT
try:
    from subprocess import check_open
except ImportError:
    # pre-2.7:
    from StringIO import StringIO
    
    def check_open(*args, **kwargs):
        sio = StringIO()
        kwargs.update(dict(stdout=PIPE, stderr=STDOUT))
        p = Popen(*args, **kwargs)
        out,err = p.communicate()
        return out

from zmq.eventloop import ioloop

from IPython.external import Itpl
# from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Str, Int, List, Unicode, Instance
from IPython.utils.path import get_ipython_module_path
from IPython.utils.process import find_cmd, pycmd2argv, FindCmdError

from factory import LoggingFactory

# load winhpcjob from IPython.kernel
try:
    from IPython.kernel.winhpcjob import (
        IPControllerTask, IPEngineTask,
        IPControllerJob, IPEngineSetJob
    )
except ImportError:
    pass


#-----------------------------------------------------------------------------
# Paths to the kernel apps
#-----------------------------------------------------------------------------


ipcluster_cmd_argv = pycmd2argv(get_ipython_module_path(
    'IPython.zmq.parallel.ipclusterapp'
))

ipengine_cmd_argv = pycmd2argv(get_ipython_module_path(
    'IPython.zmq.parallel.ipengineapp'
))

ipcontroller_cmd_argv = pycmd2argv(get_ipython_module_path(
    'IPython.zmq.parallel.ipcontrollerapp'
))

#-----------------------------------------------------------------------------
# Base launchers and errors
#-----------------------------------------------------------------------------


class LauncherError(Exception):
    pass


class ProcessStateError(LauncherError):
    pass


class UnknownStatus(LauncherError):
    pass


class BaseLauncher(LoggingFactory):
    """An asbtraction for starting, stopping and signaling a process."""

    # In all of the launchers, the work_dir is where child processes will be
    # run. This will usually be the cluster_dir, but may not be. any work_dir
    # passed into the __init__ method will override the config value.
    # This should not be used to set the work_dir for the actual engine
    # and controller. Instead, use their own config files or the
    # controller_args, engine_args attributes of the launchers to add
    # the --work-dir option.
    work_dir = Unicode(u'.')
    loop = Instance('zmq.eventloop.ioloop.IOLoop')
    def _loop_default(self):
        return ioloop.IOLoop.instance()

    def __init__(self, work_dir=u'.', config=None, **kwargs):
        super(BaseLauncher, self).__init__(work_dir=work_dir, config=config, **kwargs)
        self.state = 'before' # can be before, running, after
        self.stop_callbacks = []
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
        raise NotImplementedError('start must be implemented in a subclass')

    def stop(self):
        """Stop the process and notify observers of stopping.

        This must return a deferred that fires with information about the
        processing stopping, like errors that occur while the process is
        attempting to be shut down. This deferred won't fire when the process
        actually stops. To observe the actual process stopping, see
        :func:`observe_stop`.
        """
        raise NotImplementedError('stop must be implemented in a subclass')

    def on_stop(self, f):
        """Get a deferred that will fire when the process stops.

        The deferred will fire with data that contains information about
        the exit status of the process.
        """
        if self.state=='after':
            return f(self.stop_data)
        else:
            self.stop_callbacks.append(f)

    def notify_start(self, data):
        """Call this to trigger startup actions.

        This logs the process startup and sets the state to 'running'.  It is
        a pass-through so it can be used as a callback.
        """

        self.log.info('Process %r started: %r' % (self.args[0], data))
        self.start_data = data
        self.state = 'running'
        return data

    def notify_stop(self, data):
        """Call this to trigger process stop actions.

        This logs the process stopping and sets the state to 'after'. Call
        this to trigger all the deferreds from :func:`observe_stop`."""

        self.log.info('Process %r stopped: %r' % (self.args[0], data))
        self.stop_data = data
        self.state = 'after'
        for i in range(len(self.stop_callbacks)):
            d = self.stop_callbacks.pop()
            d(data)
        return data

    def signal(self, sig):
        """Signal the process.

        Return a semi-meaningless deferred after signaling the process.

        Parameters
        ----------
        sig : str or int
            'KILL', 'INT', etc., or any signal number
        """
        raise NotImplementedError('signal must be implemented in a subclass')


#-----------------------------------------------------------------------------
# Local process launchers
#-----------------------------------------------------------------------------


class LocalProcessLauncher(BaseLauncher):
    """Start and stop an external process in an asynchronous manner.

    This will launch the external process with a working directory of
    ``self.work_dir``.
    """

    # This is used to to construct self.args, which is passed to 
    # spawnProcess.
    cmd_and_args = List([])
    poll_frequency = Int(100) # in ms

    def __init__(self, work_dir=u'.', config=None, **kwargs):
        super(LocalProcessLauncher, self).__init__(
            work_dir=work_dir, config=config, **kwargs
        )
        self.process = None
        self.start_deferred = None
        self.poller = None

    def find_args(self):
        return self.cmd_and_args

    def start(self):
        if self.state == 'before':
            self.process = Popen(self.args,
                stdout=PIPE,stderr=PIPE,stdin=PIPE,
                env=os.environ,
                cwd=self.work_dir
            )
            
            self.loop.add_handler(self.process.stdout.fileno(), self.handle_stdout, self.loop.READ)
            self.loop.add_handler(self.process.stderr.fileno(), self.handle_stderr, self.loop.READ)
            self.poller = ioloop.PeriodicCallback(self.poll, self.poll_frequency, self.loop)
            self.poller.start()
            self.notify_start(self.process.pid)
        else:
            s = 'The process was already started and has state: %r' % self.state
            raise ProcessStateError(s)

    def stop(self):
        return self.interrupt_then_kill()

    def signal(self, sig):
        if self.state == 'running':
            self.process.send_signal(sig)

    def interrupt_then_kill(self, delay=2.0):
        """Send INT, wait a delay and then send KILL."""
        self.signal(SIGINT)
        self.killer  = ioloop.DelayedCallback(lambda : self.signal(SIGKILL), delay*1000, self.loop)
        self.killer.start()

    # callbacks, etc:
    
    def handle_stdout(self, fd, events):
        line = self.process.stdout.readline()
        # a stopped process will be readable but return empty strings
        if line:
            self.log.info(line[:-1])
        else:
            self.poll()
    
    def handle_stderr(self, fd, events):
        line = self.process.stderr.readline()
        # a stopped process will be readable but return empty strings
        if line:
            self.log.error(line[:-1])
        else:
            self.poll()
    
    def poll(self):
        status = self.process.poll()
        if status is not None:
            self.poller.stop()
            self.loop.remove_handler(self.process.stdout.fileno())
            self.loop.remove_handler(self.process.stderr.fileno())
            self.notify_stop(dict(exit_code=status, pid=self.process.pid))
        return status

class LocalControllerLauncher(LocalProcessLauncher):
    """Launch a controller as a regular external process."""

    controller_cmd = List(ipcontroller_cmd_argv, config=True)
    # Command line arguments to ipcontroller.
    controller_args = List(['--log-to-file','--log-level', str(logging.INFO)], config=True)

    def find_args(self):
        return self.controller_cmd + self.controller_args

    def start(self, cluster_dir):
        """Start the controller by cluster_dir."""
        self.controller_args.extend(['--cluster-dir', cluster_dir])
        self.cluster_dir = unicode(cluster_dir)
        self.log.info("Starting LocalControllerLauncher: %r" % self.args)
        return super(LocalControllerLauncher, self).start()


class LocalEngineLauncher(LocalProcessLauncher):
    """Launch a single engine as a regular externall process."""

    engine_cmd = List(ipengine_cmd_argv, config=True)
    # Command line arguments for ipengine.
    engine_args = List(
        ['--log-to-file','--log-level', str(logging.INFO)], config=True
    )

    def find_args(self):
        return self.engine_cmd + self.engine_args

    def start(self, cluster_dir):
        """Start the engine by cluster_dir."""
        self.engine_args.extend(['--cluster-dir', cluster_dir])
        self.cluster_dir = unicode(cluster_dir)
        return super(LocalEngineLauncher, self).start()


class LocalEngineSetLauncher(BaseLauncher):
    """Launch a set of engines as regular external processes."""

    # Command line arguments for ipengine.
    engine_args = List(
        ['--log-to-file','--log-level', str(logging.INFO)], config=True
    )
    # launcher class
    launcher_class = LocalEngineLauncher
    
    def __init__(self, work_dir=u'.', config=None, **kwargs):
        super(LocalEngineSetLauncher, self).__init__(
            work_dir=work_dir, config=config, **kwargs
        )
        self.launchers = {}
        self.stop_data = {}

    def start(self, n, cluster_dir):
        """Start n engines by profile or cluster_dir."""
        self.cluster_dir = unicode(cluster_dir)
        dlist = []
        for i in range(n):
            el = self.launcher_class(work_dir=self.work_dir, config=self.config, logname=self.log.name)
            # Copy the engine args over to each engine launcher.
            import copy
            el.engine_args = copy.deepcopy(self.engine_args)
            el.on_stop(self._notice_engine_stopped)
            d = el.start(cluster_dir)
            if i==0:
                self.log.info("Starting LocalEngineSetLauncher: %r" % el.args)
            self.launchers[i] = el
            dlist.append(d)
        self.notify_start(dlist)
        # The consumeErrors here could be dangerous
        # dfinal = gatherBoth(dlist, consumeErrors=True)
        # dfinal.addCallback(self.notify_start)
        return dlist

    def find_args(self):
        return ['engine set']

    def signal(self, sig):
        dlist = []
        for el in self.launchers.itervalues():
            d = el.signal(sig)
            dlist.append(d)
        # dfinal = gatherBoth(dlist, consumeErrors=True)
        return dlist

    def interrupt_then_kill(self, delay=1.0):
        dlist = []
        for el in self.launchers.itervalues():
            d = el.interrupt_then_kill(delay)
            dlist.append(d)
        # dfinal = gatherBoth(dlist, consumeErrors=True)
        return dlist

    def stop(self):
        return self.interrupt_then_kill()
    
    def _notice_engine_stopped(self, data):
        print "notice", data
        pid = data['pid']
        for idx,el in self.launchers.iteritems():
            if el.process.pid == pid:
                break
        self.launchers.pop(idx)
        self.stop_data[idx] = data
        if not self.launchers:
            self.notify_stop(self.stop_data)


#-----------------------------------------------------------------------------
# MPIExec launchers
#-----------------------------------------------------------------------------


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


class MPIExecControllerLauncher(MPIExecLauncher):
    """Launch a controller using mpiexec."""

    controller_cmd = List(ipcontroller_cmd_argv, config=True)
    # Command line arguments to ipcontroller.
    controller_args = List(['--log-to-file','--log-level', str(logging.INFO)], config=True)
    n = Int(1, config=False)

    def start(self, cluster_dir):
        """Start the controller by cluster_dir."""
        self.controller_args.extend(['--cluster-dir', cluster_dir])
        self.cluster_dir = unicode(cluster_dir)
        self.log.info("Starting MPIExecControllerLauncher: %r" % self.args)
        return super(MPIExecControllerLauncher, self).start(1)

    def find_args(self):
        return self.mpi_cmd + ['-n', self.n] + self.mpi_args + \
               self.controller_cmd + self.controller_args


class MPIExecEngineSetLauncher(MPIExecLauncher):

    engine_cmd = List(ipengine_cmd_argv, config=True)
    # Command line arguments for ipengine.
    engine_args = List(
        ['--log-to-file','--log-level', str(logging.INFO)], config=True
    )
    n = Int(1, config=True)

    def start(self, n, cluster_dir):
        """Start n engines by profile or cluster_dir."""
        self.engine_args.extend(['--cluster-dir', cluster_dir])
        self.cluster_dir = unicode(cluster_dir)
        self.n = n
        self.log.info('Starting MPIExecEngineSetLauncher: %r' % self.args)
        return super(MPIExecEngineSetLauncher, self).start(n)

    def find_args(self):
        return self.mpi_cmd + ['-n', self.n] + self.mpi_args + \
               self.engine_cmd + self.engine_args


#-----------------------------------------------------------------------------
# SSH launchers
#-----------------------------------------------------------------------------

# TODO: Get SSH Launcher working again.

class SSHLauncher(LocalProcessLauncher):
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
    user = Str(os.environ.get('USER','username'), config=True)
    location = Str('')

    def _hostname_changed(self, name, old, new):
        self.location = '%s@%s' % (self.user, new)

    def _user_changed(self, name, old, new):
        self.location = '%s@%s' % (new, self.hostname)

    def find_args(self):
        return self.ssh_cmd + self.ssh_args + [self.location] + \
               self.program + self.program_args

    def start(self, cluster_dir, hostname=None, user=None):
        if hostname is not None:
            self.hostname = hostname
        if user is not None:
            self.user = user
        return super(SSHLauncher, self).start()


class SSHControllerLauncher(SSHLauncher):

    program = List(ipcontroller_cmd_argv, config=True)
    # Command line arguments to ipcontroller.
    program_args = List(['--log-to-file','--log-level', str(logging.INFO)], config=True)


class SSHEngineLauncher(SSHLauncher):
    program = List(ipengine_cmd_argv, config=True)
    # Command line arguments for ipengine.
    program_args = List(
        ['--log-to-file','--log-level', str(logging.INFO)], config=True
    )
    
class SSHEngineSetLauncher(LocalEngineSetLauncher):
    launcher_class = SSHEngineLauncher


#-----------------------------------------------------------------------------
# Windows HPC Server 2008 scheduler launchers
#-----------------------------------------------------------------------------


# This is only used on Windows.
def find_job_cmd():
    if os.name=='nt':
        try:
            return find_cmd('job')
        except FindCmdError:
            return 'job'
    else:
        return 'job'


class WindowsHPCLauncher(BaseLauncher):

    # A regular expression used to get the job id from the output of the 
    # submit_command.
    job_id_regexp = Str(r'\d+', config=True)
    # The filename of the instantiated job script.
    job_file_name = Unicode(u'ipython_job.xml', config=True)
    # The full path to the instantiated job script. This gets made dynamically
    # by combining the work_dir with the job_file_name.
    job_file = Unicode(u'')
    # The hostname of the scheduler to submit the job to
    scheduler = Str('', config=True)
    job_cmd = Str(find_job_cmd(), config=True)

    def __init__(self, work_dir=u'.', config=None):
        super(WindowsHPCLauncher, self).__init__(
            work_dir=work_dir, config=config
        )

    @property
    def job_file(self):
        return os.path.join(self.work_dir, self.job_file_name)

    def write_job_file(self, n):
        raise NotImplementedError("Implement write_job_file in a subclass.")

    def find_args(self):
        return ['job.exe']
        
    def parse_job_id(self, output):
        """Take the output of the submit command and return the job id."""
        m = re.search(self.job_id_regexp, output)
        if m is not None:
            job_id = m.group()
        else:
            raise LauncherError("Job id couldn't be determined: %s" % output)
        self.job_id = job_id
        self.log.info('Job started with job id: %r' % job_id)
        return job_id

    def start(self, n):
        """Start n copies of the process using the Win HPC job scheduler."""
        self.write_job_file(n)
        args = [
            'submit',
            '/jobfile:%s' % self.job_file,
            '/scheduler:%s' % self.scheduler
        ]
        self.log.info("Starting Win HPC Job: %s" % (self.job_cmd + ' ' + ' '.join(args),))
        # Twisted will raise DeprecationWarnings if we try to pass unicode to this
        output = check_output([self.job_cmd]+args,
            env=os.environ,
            cwd=self.work_dir,
            stderr=STDOUT
        )
        job_id = self.parse_job_id(output)
        # self.notify_start(job_id)
        return job_id

    def stop(self):
        args = [
            'cancel',
            self.job_id,
            '/scheduler:%s' % self.scheduler
        ]
        self.log.info("Stopping Win HPC Job: %s" % (self.job_cmd + ' ' + ' '.join(args),))
        try:
            output = check_output([self.job_cmd]+args,
                env=os.environ,
                cwd=self.work_dir,
                stderr=STDOUT
            )
        except:
            output = 'The job already appears to be stoppped: %r' % self.job_id
        self.notify_stop(output)  # Pass the output of the kill cmd
        return output


class WindowsHPCControllerLauncher(WindowsHPCLauncher):

    job_file_name = Unicode(u'ipcontroller_job.xml', config=True)
    extra_args = List([], config=False)

    def write_job_file(self, n):
        job = IPControllerJob(config=self.config)

        t = IPControllerTask(config=self.config)
        # The tasks work directory is *not* the actual work directory of 
        # the controller. It is used as the base path for the stdout/stderr
        # files that the scheduler redirects to.
        t.work_directory = self.cluster_dir
        # Add the --cluster-dir and from self.start().
        t.controller_args.extend(self.extra_args)
        job.add_task(t)

        self.log.info("Writing job description file: %s" % self.job_file)
        job.write(self.job_file)

    @property
    def job_file(self):
        return os.path.join(self.cluster_dir, self.job_file_name)

    def start(self, cluster_dir):
        """Start the controller by cluster_dir."""
        self.extra_args = ['--cluster-dir', cluster_dir]
        self.cluster_dir = unicode(cluster_dir)
        return super(WindowsHPCControllerLauncher, self).start(1)


class WindowsHPCEngineSetLauncher(WindowsHPCLauncher):

    job_file_name = Unicode(u'ipengineset_job.xml', config=True)
    extra_args = List([], config=False)

    def write_job_file(self, n):
        job = IPEngineSetJob(config=self.config)

        for i in range(n):
            t = IPEngineTask(config=self.config)
            # The tasks work directory is *not* the actual work directory of 
            # the engine. It is used as the base path for the stdout/stderr
            # files that the scheduler redirects to.
            t.work_directory = self.cluster_dir
            # Add the --cluster-dir and from self.start().
            t.engine_args.extend(self.extra_args)
            job.add_task(t)

        self.log.info("Writing job description file: %s" % self.job_file)
        job.write(self.job_file)

    @property
    def job_file(self):
        return os.path.join(self.cluster_dir, self.job_file_name)

    def start(self, n, cluster_dir):
        """Start the controller by cluster_dir."""
        self.extra_args = ['--cluster-dir', cluster_dir]
        self.cluster_dir = unicode(cluster_dir)
        return super(WindowsHPCEngineSetLauncher, self).start(n)


#-----------------------------------------------------------------------------
# Batch (PBS) system launchers
#-----------------------------------------------------------------------------

# TODO: Get PBS launcher working again.

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

    def __init__(self, work_dir=u'.', config=None):
        super(BatchSystemLauncher, self).__init__(
            work_dir=work_dir, config=config
        )
        self.batch_file = os.path.join(self.work_dir, self.batch_file_name)
        self.context = {}

    def parse_job_id(self, output):
        """Take the output of the submit command and return the job id."""
        m = re.match(self.job_id_regexp, output)
        if m is not None:
            job_id = m.group()
        else:
            raise LauncherError("Job id couldn't be determined: %s" % output)
        self.job_id = job_id
        self.log.info('Job started with job id: %r' % job_id)
        return job_id

    def write_batch_script(self, n):
        """Instantiate and write the batch script to the work_dir."""
        self.context['n'] = n
        script_as_string = Itpl.itplns(self.batch_template, self.context)
        self.log.info('Writing instantiated batch script: %s' % self.batch_file)
        f = open(self.batch_file, 'w')
        f.write(script_as_string)
        f.close()

    def start(self, n):
        """Start n copies of the process using a batch system."""
        self.write_batch_script(n)
        output = check_output([self.submit_command, self.batch_file], env=os.environ, stdout=STDOUT)
        job_id = self.parse_job_id(output)
        # self.notify_start(job_id)
        return job_id

    def stop(self):
        output = Popen([self.delete_command, self.job_id], env=os.environ, stderr=STDOUT)
        self.notify_stop(output)  # Pass the output of the kill cmd
        return output


class PBSLauncher(BatchSystemLauncher):
    """A BatchSystemLauncher subclass for PBS."""

    submit_command = Str('qsub', config=True)
    delete_command = Str('qdel', config=True)
    job_id_regexp = Str(r'\d+', config=True)
    batch_template = Str('', config=True)
    batch_file_name = Unicode(u'pbs_batch_script', config=True)
    batch_file = Unicode(u'')


class PBSControllerLauncher(PBSLauncher):
    """Launch a controller using PBS."""

    batch_file_name = Unicode(u'pbs_batch_script_controller', config=True)

    def start(self, cluster_dir):
        """Start the controller by profile or cluster_dir."""
        # Here we save profile and cluster_dir in the context so they
        # can be used in the batch script template as ${profile} and
        # ${cluster_dir}
        self.context['cluster_dir'] = cluster_dir
        self.cluster_dir = unicode(cluster_dir)
        self.log.info("Starting PBSControllerLauncher: %r" % self.args)
        return super(PBSControllerLauncher, self).start(1)


class PBSEngineSetLauncher(PBSLauncher):

    batch_file_name = Unicode(u'pbs_batch_script_engines', config=True)

    def start(self, n, cluster_dir):
        """Start n engines by profile or cluster_dir."""
        self.program_args.extend(['--cluster-dir', cluster_dir])
        self.cluster_dir = unicode(cluster_dir)
        self.log.info('Starting PBSEngineSetLauncher: %r' % self.args)
        return super(PBSEngineSetLauncher, self).start(n)


#-----------------------------------------------------------------------------
# A launcher for ipcluster itself!
#-----------------------------------------------------------------------------


class IPClusterLauncher(LocalProcessLauncher):
    """Launch the ipcluster program in an external process."""

    ipcluster_cmd = List(ipcluster_cmd_argv, config=True)
    # Command line arguments to pass to ipcluster.
    ipcluster_args = List(
        ['--clean-logs', '--log-to-file', '--log-level', str(logging.INFO)], config=True)
    ipcluster_subcommand = Str('start')
    ipcluster_n = Int(2)

    def find_args(self):
        return self.ipcluster_cmd + [self.ipcluster_subcommand] + \
            ['-n', repr(self.ipcluster_n)] + self.ipcluster_args

    def start(self):
        self.log.info("Starting ipcluster: %r" % self.args)
        return super(IPClusterLauncher, self).start()

