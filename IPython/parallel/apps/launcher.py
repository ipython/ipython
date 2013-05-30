# encoding: utf-8
"""
Facilities for launching IPython processes asynchronously.

Authors:

* Brian Granger
* MinRK
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import copy
import logging
import os
import pipes
import stat
import sys
import time

# signal imports, handling various platforms, versions

from signal import SIGINT, SIGTERM
try:
    from signal import SIGKILL
except ImportError:
    # Windows
    SIGKILL=SIGTERM

try:
    # Windows >= 2.7, 3.2
    from signal import CTRL_C_EVENT as SIGINT
except ImportError:
    pass

from subprocess import Popen, PIPE, STDOUT
try:
    from subprocess import check_output
except ImportError:
    # pre-2.7, define check_output with Popen
    def check_output(*args, **kwargs):
        kwargs.update(dict(stdout=PIPE))
        p = Popen(*args, **kwargs)
        out,err = p.communicate()
        return out

from zmq.eventloop import ioloop

from IPython.config.application import Application
from IPython.config.configurable import LoggingConfigurable
from IPython.utils.text import EvalFormatter
from IPython.utils.traitlets import (
    Any, Integer, CFloat, List, Unicode, Dict, Instance, HasTraits, CRegExp
)
from IPython.utils.encoding import DEFAULT_ENCODING
from IPython.utils.path import get_home_dir
from IPython.utils.process import find_cmd, FindCmdError

from .win32support import forward_read_events

from .winhpcjob import IPControllerTask, IPEngineTask, IPControllerJob, IPEngineSetJob

WINDOWS = os.name == 'nt'

#-----------------------------------------------------------------------------
# Paths to the kernel apps
#-----------------------------------------------------------------------------

cmd = "from IPython.parallel.apps.%s import launch_new_instance; launch_new_instance()"

ipcluster_cmd_argv = [sys.executable, "-c", cmd % "ipclusterapp"]

ipengine_cmd_argv = [sys.executable, "-c", cmd % "ipengineapp"]

ipcontroller_cmd_argv = [sys.executable, "-c", cmd % "ipcontrollerapp"]

#-----------------------------------------------------------------------------
# Base launchers and errors
#-----------------------------------------------------------------------------

class LauncherError(Exception):
    pass


class ProcessStateError(LauncherError):
    pass


class UnknownStatus(LauncherError):
    pass


class BaseLauncher(LoggingConfigurable):
    """An asbtraction for starting, stopping and signaling a process."""

    # In all of the launchers, the work_dir is where child processes will be
    # run. This will usually be the profile_dir, but may not be. any work_dir
    # passed into the __init__ method will override the config value.
    # This should not be used to set the work_dir for the actual engine
    # and controller. Instead, use their own config files or the
    # controller_args, engine_args attributes of the launchers to add
    # the work_dir option.
    work_dir = Unicode(u'.')
    loop = Instance('zmq.eventloop.ioloop.IOLoop')

    start_data = Any()
    stop_data = Any()

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
        """Start the process."""
        raise NotImplementedError('start must be implemented in a subclass')

    def stop(self):
        """Stop the process and notify observers of stopping.

        This method will return None immediately.
        To observe the actual process stopping, see :meth:`on_stop`.
        """
        raise NotImplementedError('stop must be implemented in a subclass')

    def on_stop(self, f):
        """Register a callback to be called with this Launcher's stop_data
        when the process actually finishes.
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

        self.log.debug('Process %r started: %r', self.args[0], data)
        self.start_data = data
        self.state = 'running'
        return data

    def notify_stop(self, data):
        """Call this to trigger process stop actions.

        This logs the process stopping and sets the state to 'after'. Call
        this to trigger callbacks registered via :meth:`on_stop`."""

        self.log.debug('Process %r stopped: %r', self.args[0], data)
        self.stop_data = data
        self.state = 'after'
        for i in range(len(self.stop_callbacks)):
            d = self.stop_callbacks.pop()
            d(data)
        return data

    def signal(self, sig):
        """Signal the process.

        Parameters
        ----------
        sig : str or int
            'KILL', 'INT', etc., or any signal number
        """
        raise NotImplementedError('signal must be implemented in a subclass')

class ClusterAppMixin(HasTraits):
    """MixIn for cluster args as traits"""
    profile_dir=Unicode('')
    cluster_id=Unicode('')

    @property
    def cluster_args(self):
        return ['--profile-dir', self.profile_dir, '--cluster-id', self.cluster_id]

class ControllerMixin(ClusterAppMixin):
    controller_cmd = List(ipcontroller_cmd_argv, config=True,
        help="""Popen command to launch ipcontroller.""")
    # Command line arguments to ipcontroller.
    controller_args = List(['--log-to-file','--log-level=%i' % logging.INFO], config=True,
        help="""command-line args to pass to ipcontroller""")

class EngineMixin(ClusterAppMixin):
    engine_cmd = List(ipengine_cmd_argv, config=True,
        help="""command to launch the Engine.""")
    # Command line arguments for ipengine.
    engine_args = List(['--log-to-file','--log-level=%i' % logging.INFO], config=True,
        help="command-line arguments to pass to ipengine"
    )


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
    poll_frequency = Integer(100) # in ms

    def __init__(self, work_dir=u'.', config=None, **kwargs):
        super(LocalProcessLauncher, self).__init__(
            work_dir=work_dir, config=config, **kwargs
        )
        self.process = None
        self.poller = None

    def find_args(self):
        return self.cmd_and_args

    def start(self):
        self.log.debug("Starting %s: %r", self.__class__.__name__, self.args)
        if self.state == 'before':
            self.process = Popen(self.args,
                stdout=PIPE,stderr=PIPE,stdin=PIPE,
                env=os.environ,
                cwd=self.work_dir
            )
            if WINDOWS:
                self.stdout = forward_read_events(self.process.stdout)
                self.stderr = forward_read_events(self.process.stderr)
            else:
                self.stdout = self.process.stdout.fileno()
                self.stderr = self.process.stderr.fileno()
            self.loop.add_handler(self.stdout, self.handle_stdout, self.loop.READ)
            self.loop.add_handler(self.stderr, self.handle_stderr, self.loop.READ)
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
            if WINDOWS and sig != SIGINT:
                # use Windows tree-kill for better child cleanup
                check_output(['taskkill', '-pid', str(self.process.pid), '-t', '-f'])
            else:
                self.process.send_signal(sig)

    def interrupt_then_kill(self, delay=2.0):
        """Send INT, wait a delay and then send KILL."""
        try:
            self.signal(SIGINT)
        except Exception:
            self.log.debug("interrupt failed")
            pass
        self.killer  = ioloop.DelayedCallback(lambda : self.signal(SIGKILL), delay*1000, self.loop)
        self.killer.start()

    # callbacks, etc:

    def handle_stdout(self, fd, events):
        if WINDOWS:
            line = self.stdout.recv()
        else:
            line = self.process.stdout.readline()
        # a stopped process will be readable but return empty strings
        if line:
            self.log.debug(line[:-1])
        else:
            self.poll()

    def handle_stderr(self, fd, events):
        if WINDOWS:
            line = self.stderr.recv()
        else:
            line = self.process.stderr.readline()
        # a stopped process will be readable but return empty strings
        if line:
            self.log.debug(line[:-1])
        else:
            self.poll()

    def poll(self):
        status = self.process.poll()
        if status is not None:
            self.poller.stop()
            self.loop.remove_handler(self.stdout)
            self.loop.remove_handler(self.stderr)
            self.notify_stop(dict(exit_code=status, pid=self.process.pid))
        return status

class LocalControllerLauncher(LocalProcessLauncher, ControllerMixin):
    """Launch a controller as a regular external process."""

    def find_args(self):
        return self.controller_cmd + self.cluster_args + self.controller_args

    def start(self):
        """Start the controller by profile_dir."""
        return super(LocalControllerLauncher, self).start()


class LocalEngineLauncher(LocalProcessLauncher, EngineMixin):
    """Launch a single engine as a regular externall process."""

    def find_args(self):
        return self.engine_cmd + self.cluster_args + self.engine_args


class LocalEngineSetLauncher(LocalEngineLauncher):
    """Launch a set of engines as regular external processes."""

    delay = CFloat(0.1, config=True,
        help="""delay (in seconds) between starting each engine after the first.
        This can help force the engines to get their ids in order, or limit
        process flood when starting many engines."""
    )

    # launcher class
    launcher_class = LocalEngineLauncher

    launchers = Dict()
    stop_data = Dict()

    def __init__(self, work_dir=u'.', config=None, **kwargs):
        super(LocalEngineSetLauncher, self).__init__(
            work_dir=work_dir, config=config, **kwargs
        )
        self.stop_data = {}

    def start(self, n):
        """Start n engines by profile or profile_dir."""
        dlist = []
        for i in range(n):
            if i > 0:
                time.sleep(self.delay)
            el = self.launcher_class(work_dir=self.work_dir, config=self.config, log=self.log,
                                    profile_dir=self.profile_dir, cluster_id=self.cluster_id,
            )

            # Copy the engine args over to each engine launcher.
            el.engine_cmd = copy.deepcopy(self.engine_cmd)
            el.engine_args = copy.deepcopy(self.engine_args)
            el.on_stop(self._notice_engine_stopped)
            d = el.start()
            self.launchers[i] = el
            dlist.append(d)
        self.notify_start(dlist)
        return dlist

    def find_args(self):
        return ['engine set']

    def signal(self, sig):
        dlist = []
        for el in self.launchers.itervalues():
            d = el.signal(sig)
            dlist.append(d)
        return dlist

    def interrupt_then_kill(self, delay=1.0):
        dlist = []
        for el in self.launchers.itervalues():
            d = el.interrupt_then_kill(delay)
            dlist.append(d)
        return dlist

    def stop(self):
        return self.interrupt_then_kill()

    def _notice_engine_stopped(self, data):
        pid = data['pid']
        for idx,el in self.launchers.iteritems():
            if el.process.pid == pid:
                break
        self.launchers.pop(idx)
        self.stop_data[idx] = data
        if not self.launchers:
            self.notify_stop(self.stop_data)


#-----------------------------------------------------------------------------
# MPI launchers
#-----------------------------------------------------------------------------


class MPILauncher(LocalProcessLauncher):
    """Launch an external process using mpiexec."""

    mpi_cmd = List(['mpiexec'], config=True,
        help="The mpiexec command to use in starting the process."
    )
    mpi_args = List([], config=True,
        help="The command line arguments to pass to mpiexec."
    )
    program = List(['date'],
        help="The program to start via mpiexec.")
    program_args = List([],
        help="The command line argument to the program."
    )
    n = Integer(1)
    
    def __init__(self, *args, **kwargs):
        # deprecation for old MPIExec names:
        config = kwargs.get('config', {})
        for oldname in ('MPIExecLauncher', 'MPIExecControllerLauncher', 'MPIExecEngineSetLauncher'):
            deprecated = config.get(oldname)
            if deprecated:
                newname = oldname.replace('MPIExec', 'MPI')
                config[newname].update(deprecated)
                self.log.warn("WARNING: %s name has been deprecated, use %s", oldname, newname)

        super(MPILauncher, self).__init__(*args, **kwargs)

    def find_args(self):
        """Build self.args using all the fields."""
        return self.mpi_cmd + ['-n', str(self.n)] + self.mpi_args + \
               self.program + self.program_args

    def start(self, n):
        """Start n instances of the program using mpiexec."""
        self.n = n
        return super(MPILauncher, self).start()


class MPIControllerLauncher(MPILauncher, ControllerMixin):
    """Launch a controller using mpiexec."""

    # alias back to *non-configurable* program[_args] for use in find_args()
    # this way all Controller/EngineSetLaunchers have the same form, rather
    # than *some* having `program_args` and others `controller_args`
    @property
    def program(self):
        return self.controller_cmd

    @property
    def program_args(self):
        return self.cluster_args + self.controller_args

    def start(self):
        """Start the controller by profile_dir."""
        return super(MPIControllerLauncher, self).start(1)


class MPIEngineSetLauncher(MPILauncher, EngineMixin):
    """Launch engines using mpiexec"""

    # alias back to *non-configurable* program[_args] for use in find_args()
    # this way all Controller/EngineSetLaunchers have the same form, rather
    # than *some* having `program_args` and others `controller_args`
    @property
    def program(self):
        return self.engine_cmd

    @property
    def program_args(self):
        return self.cluster_args + self.engine_args

    def start(self, n):
        """Start n engines by profile or profile_dir."""
        self.n = n
        return super(MPIEngineSetLauncher, self).start(n)

# deprecated MPIExec names
class DeprecatedMPILauncher(object):
    def warn(self):
        oldname = self.__class__.__name__
        newname = oldname.replace('MPIExec', 'MPI')
        self.log.warn("WARNING: %s name is deprecated, use %s", oldname, newname)
    
class MPIExecLauncher(MPILauncher, DeprecatedMPILauncher):
    """Deprecated, use MPILauncher"""
    def __init__(self, *args, **kwargs):
        super(MPIExecLauncher, self).__init__(*args, **kwargs)
        self.warn()

class MPIExecControllerLauncher(MPIControllerLauncher, DeprecatedMPILauncher):
    """Deprecated, use MPIControllerLauncher"""
    def __init__(self, *args, **kwargs):
        super(MPIExecControllerLauncher, self).__init__(*args, **kwargs)
        self.warn()

class MPIExecEngineSetLauncher(MPIEngineSetLauncher, DeprecatedMPILauncher):
    """Deprecated, use MPIEngineSetLauncher"""
    def __init__(self, *args, **kwargs):
        super(MPIExecEngineSetLauncher, self).__init__(*args, **kwargs)
        self.warn()


#-----------------------------------------------------------------------------
# SSH launchers
#-----------------------------------------------------------------------------

# TODO: Get SSH Launcher back to level of sshx in 0.10.2

class SSHLauncher(LocalProcessLauncher):
    """A minimal launcher for ssh.

    To be useful this will probably have to be extended to use the ``sshx``
    idea for environment variables.  There could be other things this needs
    as well.
    """

    ssh_cmd = List(['ssh'], config=True,
        help="command for starting ssh")
    ssh_args = List(['-tt'], config=True,
        help="args to pass to ssh")
    scp_cmd = List(['scp'], config=True,
        help="command for sending files")
    program = List(['date'],
        help="Program to launch via ssh")
    program_args = List([],
        help="args to pass to remote program")
    hostname = Unicode('', config=True,
        help="hostname on which to launch the program")
    user = Unicode('', config=True,
        help="username for ssh")
    location = Unicode('', config=True,
        help="user@hostname location for ssh in one setting")
    to_fetch = List([], config=True,
        help="List of (remote, local) files to fetch after starting")
    to_send = List([], config=True,
        help="List of (local, remote) files to send before starting")

    def _hostname_changed(self, name, old, new):
        if self.user:
            self.location = u'%s@%s' % (self.user, new)
        else:
            self.location = new

    def _user_changed(self, name, old, new):
        self.location = u'%s@%s' % (new, self.hostname)

    def find_args(self):
        return self.ssh_cmd + self.ssh_args + [self.location] + \
               list(map(pipes.quote, self.program + self.program_args))
    
    def _send_file(self, local, remote):
        """send a single file"""
        remote = "%s:%s" % (self.location, remote)
        for i in range(10):
            if not os.path.exists(local):
                self.log.debug("waiting for %s" % local)
                time.sleep(1)
            else:
                break
        self.log.info("sending %s to %s", local, remote)
        check_output(self.scp_cmd + [local, remote])
    
    def send_files(self):
        """send our files (called before start)"""
        if not self.to_send:
            return
        for local_file, remote_file in self.to_send:
            self._send_file(local_file, remote_file)

    def _fetch_file(self, remote, local):
        """fetch a single file"""
        full_remote = "%s:%s" % (self.location, remote)
        self.log.info("fetching %s from %s", local, full_remote)
        for i in range(10):
            # wait up to 10s for remote file to exist
            check = check_output(self.ssh_cmd + self.ssh_args + \
                [self.location, 'test -e', remote, "&& echo 'yes' || echo 'no'"])
            check = check.decode(DEFAULT_ENCODING, 'replace').strip()
            if check == u'no':
                time.sleep(1)
            elif check == u'yes':
                break
        check_output(self.scp_cmd + [full_remote, local])
    
    def fetch_files(self):
        """fetch remote files (called after start)"""
        if not self.to_fetch:
            return
        for remote_file, local_file in self.to_fetch:
            self._fetch_file(remote_file, local_file)

    def start(self, hostname=None, user=None):
        if hostname is not None:
            self.hostname = hostname
        if user is not None:
            self.user = user
        
        self.send_files()
        super(SSHLauncher, self).start()
        self.fetch_files()

    def signal(self, sig):
        if self.state == 'running':
            # send escaped ssh connection-closer
            self.process.stdin.write('~.')
            self.process.stdin.flush()

class SSHClusterLauncher(SSHLauncher, ClusterAppMixin):
    
    remote_profile_dir = Unicode('', config=True,
        help="""The remote profile_dir to use.  
        
        If not specified, use calling profile, stripping out possible leading homedir.
        """)
    
    def _profile_dir_changed(self, name, old, new):
        if not self.remote_profile_dir:
            # trigger remote_profile_dir_default logic again,
            # in case it was already triggered before profile_dir was set
            self.remote_profile_dir = self._strip_home(new)
    
    @staticmethod
    def _strip_home(path):
        """turns /home/you/.ipython/profile_foo into .ipython/profile_foo"""
        home = get_home_dir()
        if not home.endswith('/'):
            home = home+'/'
        
        if path.startswith(home):
            return path[len(home):]
        else:
            return path

    def _remote_profile_dir_default(self):
        return self._strip_home(self.profile_dir)
    
    def _cluster_id_changed(self, name, old, new):
        if new:
            raise ValueError("cluster id not supported by SSH launchers")
    
    @property
    def cluster_args(self):
        return ['--profile-dir', self.remote_profile_dir]

class SSHControllerLauncher(SSHClusterLauncher, ControllerMixin):

    # alias back to *non-configurable* program[_args] for use in find_args()
    # this way all Controller/EngineSetLaunchers have the same form, rather
    # than *some* having `program_args` and others `controller_args`

    def _controller_cmd_default(self):
        return ['ipcontroller']
    
    @property
    def program(self):
        return self.controller_cmd
    
    @property
    def program_args(self):
        return self.cluster_args + self.controller_args

    def _to_fetch_default(self):
        return [
            (os.path.join(self.remote_profile_dir, 'security', cf),
             os.path.join(self.profile_dir, 'security', cf),)
            for cf in ('ipcontroller-client.json', 'ipcontroller-engine.json')
        ]

class SSHEngineLauncher(SSHClusterLauncher, EngineMixin):

    # alias back to *non-configurable* program[_args] for use in find_args()
    # this way all Controller/EngineSetLaunchers have the same form, rather
    # than *some* having `program_args` and others `controller_args`
    
    def _engine_cmd_default(self):
        return ['ipengine']
    
    @property
    def program(self):
        return self.engine_cmd

    @property
    def program_args(self):
        return self.cluster_args + self.engine_args
    
    def _to_send_default(self):
        return [
            (os.path.join(self.profile_dir, 'security', cf), 
             os.path.join(self.remote_profile_dir, 'security', cf))
            for cf in ('ipcontroller-client.json', 'ipcontroller-engine.json')
        ]


class SSHEngineSetLauncher(LocalEngineSetLauncher):
    launcher_class = SSHEngineLauncher
    engines = Dict(config=True,
        help="""dict of engines to launch.  This is a dict by hostname of ints,
        corresponding to the number of engines to start on that host.""")
    
    def _engine_cmd_default(self):
        return ['ipengine']
    
    @property
    def engine_count(self):
        """determine engine count from `engines` dict"""
        count = 0
        for n in self.engines.itervalues():
            if isinstance(n, (tuple,list)):
                n,args = n
            count += n
        return count
    
    def start(self, n):
        """Start engines by profile or profile_dir.
        `n` is ignored, and the `engines` config property is used instead.
        """

        dlist = []
        for host, n in self.engines.iteritems():
            if isinstance(n, (tuple, list)):
                n, args = n
            else:
                args = copy.deepcopy(self.engine_args)

            if '@' in host:
                user,host = host.split('@',1)
            else:
                user=None
            for i in range(n):
                if i > 0:
                    time.sleep(self.delay)
                el = self.launcher_class(work_dir=self.work_dir, config=self.config, log=self.log,
                                        profile_dir=self.profile_dir, cluster_id=self.cluster_id,
                )
                if i > 0:
                    # only send files for the first engine on each host
                    el.to_send = []

                # Copy the engine args over to each engine launcher.
                el.engine_cmd = self.engine_cmd
                el.engine_args = args
                el.on_stop(self._notice_engine_stopped)
                d = el.start(user=user, hostname=host)
                self.launchers[ "%s/%i" % (host,i) ] = el
                dlist.append(d)
        self.notify_start(dlist)
        return dlist


class SSHProxyEngineSetLauncher(SSHClusterLauncher):
    """Launcher for calling
    `ipcluster engines` on a remote machine.
    
    Requires that remote profile is already configured.
    """
    
    n = Integer()
    ipcluster_cmd = List(['ipcluster'], config=True)
    
    @property
    def program(self):
        return self.ipcluster_cmd + ['engines']
    
    @property
    def program_args(self):
        return ['-n', str(self.n), '--profile-dir', self.remote_profile_dir]
    
    def _to_send_default(self):
        return [
            (os.path.join(self.profile_dir, 'security', cf), 
             os.path.join(self.remote_profile_dir, 'security', cf))
            for cf in ('ipcontroller-client.json', 'ipcontroller-engine.json')
    ]
    
    def start(self, n):
        self.n = n
        super(SSHProxyEngineSetLauncher, self).start()


#-----------------------------------------------------------------------------
# Windows HPC Server 2008 scheduler launchers
#-----------------------------------------------------------------------------


# This is only used on Windows.
def find_job_cmd():
    if WINDOWS:
        try:
            return find_cmd('job')
        except (FindCmdError, ImportError):
            # ImportError will be raised if win32api is not installed
            return 'job'
    else:
        return 'job'


class WindowsHPCLauncher(BaseLauncher):

    job_id_regexp = CRegExp(r'\d+', config=True,
        help="""A regular expression used to get the job id from the output of the
        submit_command. """
        )
    job_file_name = Unicode(u'ipython_job.xml', config=True,
        help="The filename of the instantiated job script.")
    # The full path to the instantiated job script. This gets made dynamically
    # by combining the work_dir with the job_file_name.
    job_file = Unicode(u'')
    scheduler = Unicode('', config=True,
        help="The hostname of the scheduler to submit the job to.")
    job_cmd = Unicode(find_job_cmd(), config=True,
        help="The command for submitting jobs.")

    def __init__(self, work_dir=u'.', config=None, **kwargs):
        super(WindowsHPCLauncher, self).__init__(
            work_dir=work_dir, config=config, **kwargs
        )

    @property
    def job_file(self):
        return os.path.join(self.work_dir, self.job_file_name)

    def write_job_file(self, n):
        raise NotImplementedError("Implement write_job_file in a subclass.")

    def find_args(self):
        return [u'job.exe']

    def parse_job_id(self, output):
        """Take the output of the submit command and return the job id."""
        m = self.job_id_regexp.search(output)
        if m is not None:
            job_id = m.group()
        else:
            raise LauncherError("Job id couldn't be determined: %s" % output)
        self.job_id = job_id
        self.log.info('Job started with id: %r', job_id)
        return job_id

    def start(self, n):
        """Start n copies of the process using the Win HPC job scheduler."""
        self.write_job_file(n)
        args = [
            'submit',
            '/jobfile:%s' % self.job_file,
            '/scheduler:%s' % self.scheduler
        ]
        self.log.debug("Starting Win HPC Job: %s" % (self.job_cmd + ' ' + ' '.join(args),))

        output = check_output([self.job_cmd]+args,
            env=os.environ,
            cwd=self.work_dir,
            stderr=STDOUT
        )
        output = output.decode(DEFAULT_ENCODING, 'replace')
        job_id = self.parse_job_id(output)
        self.notify_start(job_id)
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
            output = output.decode(DEFAULT_ENCODING, 'replace')
        except:
            output = u'The job already appears to be stopped: %r' % self.job_id
        self.notify_stop(dict(job_id=self.job_id, output=output))  # Pass the output of the kill cmd
        return output


class WindowsHPCControllerLauncher(WindowsHPCLauncher, ClusterAppMixin):

    job_file_name = Unicode(u'ipcontroller_job.xml', config=True,
        help="WinHPC xml job file.")
    controller_args = List([], config=False,
        help="extra args to pass to ipcontroller")

    def write_job_file(self, n):
        job = IPControllerJob(config=self.config)

        t = IPControllerTask(config=self.config)
        # The tasks work directory is *not* the actual work directory of
        # the controller. It is used as the base path for the stdout/stderr
        # files that the scheduler redirects to.
        t.work_directory = self.profile_dir
        # Add the profile_dir and from self.start().
        t.controller_args.extend(self.cluster_args)
        t.controller_args.extend(self.controller_args)
        job.add_task(t)

        self.log.debug("Writing job description file: %s", self.job_file)
        job.write(self.job_file)

    @property
    def job_file(self):
        return os.path.join(self.profile_dir, self.job_file_name)

    def start(self):
        """Start the controller by profile_dir."""
        return super(WindowsHPCControllerLauncher, self).start(1)


class WindowsHPCEngineSetLauncher(WindowsHPCLauncher, ClusterAppMixin):

    job_file_name = Unicode(u'ipengineset_job.xml', config=True,
        help="jobfile for ipengines job")
    engine_args = List([], config=False,
        help="extra args to pas to ipengine")

    def write_job_file(self, n):
        job = IPEngineSetJob(config=self.config)

        for i in range(n):
            t = IPEngineTask(config=self.config)
            # The tasks work directory is *not* the actual work directory of
            # the engine. It is used as the base path for the stdout/stderr
            # files that the scheduler redirects to.
            t.work_directory = self.profile_dir
            # Add the profile_dir and from self.start().
            t.engine_args.extend(self.cluster_args)
            t.engine_args.extend(self.engine_args)
            job.add_task(t)

        self.log.debug("Writing job description file: %s", self.job_file)
        job.write(self.job_file)

    @property
    def job_file(self):
        return os.path.join(self.profile_dir, self.job_file_name)

    def start(self, n):
        """Start the controller by profile_dir."""
        return super(WindowsHPCEngineSetLauncher, self).start(n)


#-----------------------------------------------------------------------------
# Batch (PBS) system launchers
#-----------------------------------------------------------------------------

class BatchClusterAppMixin(ClusterAppMixin):
    """ClusterApp mixin that updates the self.context dict, rather than cl-args."""
    def _profile_dir_changed(self, name, old, new):
        self.context[name] = new
    _cluster_id_changed = _profile_dir_changed

    def _profile_dir_default(self):
        self.context['profile_dir'] = ''
        return ''
    def _cluster_id_default(self):
        self.context['cluster_id'] = ''
        return ''


class BatchSystemLauncher(BaseLauncher):
    """Launch an external process using a batch system.

    This class is designed to work with UNIX batch systems like PBS, LSF,
    GridEngine, etc.  The overall model is that there are different commands
    like qsub, qdel, etc. that handle the starting and stopping of the process.

    This class also has the notion of a batch script. The ``batch_template``
    attribute can be set to a string that is a template for the batch script.
    This template is instantiated using string formatting. Thus the template can
    use {n} fot the number of instances. Subclasses can add additional variables
    to the template dict.
    """

    # Subclasses must fill these in.  See PBSEngineSet
    submit_command = List([''], config=True,
        help="The name of the command line program used to submit jobs.")
    delete_command = List([''], config=True,
        help="The name of the command line program used to delete jobs.")
    job_id_regexp = CRegExp('', config=True,
        help="""A regular expression used to get the job id from the output of the
        submit_command.""")
    batch_template = Unicode('', config=True,
        help="The string that is the batch script template itself.")
    batch_template_file = Unicode(u'', config=True,
        help="The file that contains the batch template.")
    batch_file_name = Unicode(u'batch_script', config=True,
        help="The filename of the instantiated batch script.")
    queue = Unicode(u'', config=True,
        help="The PBS Queue.")

    def _queue_changed(self, name, old, new):
        self.context[name] = new

    n = Integer(1)
    _n_changed = _queue_changed

    # not configurable, override in subclasses
    # PBS Job Array regex
    job_array_regexp = CRegExp('')
    job_array_template = Unicode('')
    # PBS Queue regex
    queue_regexp = CRegExp('')
    queue_template = Unicode('')
    # The default batch template, override in subclasses
    default_template = Unicode('')
    # The full path to the instantiated batch script.
    batch_file = Unicode(u'')
    # the format dict used with batch_template:
    context = Dict()
    def _context_default(self):
        """load the default context with the default values for the basic keys

        because the _trait_changed methods only load the context if they
        are set to something other than the default value.
        """
        return dict(n=1, queue=u'', profile_dir=u'', cluster_id=u'')
    
    # the Formatter instance for rendering the templates:
    formatter = Instance(EvalFormatter, (), {})


    def find_args(self):
        return self.submit_command + [self.batch_file]

    def __init__(self, work_dir=u'.', config=None, **kwargs):
        super(BatchSystemLauncher, self).__init__(
            work_dir=work_dir, config=config, **kwargs
        )
        self.batch_file = os.path.join(self.work_dir, self.batch_file_name)

    def parse_job_id(self, output):
        """Take the output of the submit command and return the job id."""
        m = self.job_id_regexp.search(output)
        if m is not None:
            job_id = m.group()
        else:
            raise LauncherError("Job id couldn't be determined: %s" % output)
        self.job_id = job_id
        self.log.info('Job submitted with job id: %r', job_id)
        return job_id

    def write_batch_script(self, n):
        """Instantiate and write the batch script to the work_dir."""
        self.n = n
        # first priority is batch_template if set
        if self.batch_template_file and not self.batch_template:
            # second priority is batch_template_file
            with open(self.batch_template_file) as f:
                self.batch_template = f.read()
        if not self.batch_template:
            # third (last) priority is default_template
            self.batch_template = self.default_template

            # add jobarray or queue lines to user-specified template
            # note that this is *only* when user did not specify a template.
            # print self.job_array_regexp.search(self.batch_template)
            if not self.job_array_regexp.search(self.batch_template):
                self.log.debug("adding job array settings to batch script")
                firstline, rest = self.batch_template.split('\n',1)
                self.batch_template = u'\n'.join([firstline, self.job_array_template, rest])

            # print self.queue_regexp.search(self.batch_template)
            if self.queue and not self.queue_regexp.search(self.batch_template):
                self.log.debug("adding PBS queue settings to batch script")
                firstline, rest = self.batch_template.split('\n',1)
                self.batch_template = u'\n'.join([firstline, self.queue_template, rest])

        script_as_string = self.formatter.format(self.batch_template, **self.context)
        self.log.debug('Writing batch script: %s', self.batch_file)

        with open(self.batch_file, 'w') as f:
            f.write(script_as_string)
        os.chmod(self.batch_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    def start(self, n):
        """Start n copies of the process using a batch system."""
        self.log.debug("Starting %s: %r", self.__class__.__name__, self.args)
        # Here we save profile_dir in the context so they
        # can be used in the batch script template as {profile_dir}
        self.write_batch_script(n)
        output = check_output(self.args, env=os.environ)
        output = output.decode(DEFAULT_ENCODING, 'replace')

        job_id = self.parse_job_id(output)
        self.notify_start(job_id)
        return job_id

    def stop(self):
        output = check_output(self.delete_command+[self.job_id], env=os.environ)
        output = output.decode(DEFAULT_ENCODING, 'replace')
        self.notify_stop(dict(job_id=self.job_id, output=output)) # Pass the output of the kill cmd
        return output


class PBSLauncher(BatchSystemLauncher):
    """A BatchSystemLauncher subclass for PBS."""

    submit_command = List(['qsub'], config=True,
        help="The PBS submit command ['qsub']")
    delete_command = List(['qdel'], config=True,
        help="The PBS delete command ['qsub']")
    job_id_regexp = CRegExp(r'\d+', config=True,
        help="Regular expresion for identifying the job ID [r'\d+']")

    batch_file = Unicode(u'')
    job_array_regexp = CRegExp('#PBS\W+-t\W+[\w\d\-\$]+')
    job_array_template = Unicode('#PBS -t 1-{n}')
    queue_regexp = CRegExp('#PBS\W+-q\W+\$?\w+')
    queue_template = Unicode('#PBS -q {queue}')


class PBSControllerLauncher(PBSLauncher, BatchClusterAppMixin):
    """Launch a controller using PBS."""

    batch_file_name = Unicode(u'pbs_controller', config=True,
        help="batch file name for the controller job.")
    default_template= Unicode("""#!/bin/sh
#PBS -V
#PBS -N ipcontroller
%s --log-to-file --profile-dir="{profile_dir}" --cluster-id="{cluster_id}"
"""%(' '.join(map(pipes.quote, ipcontroller_cmd_argv))))


    def start(self):
        """Start the controller by profile or profile_dir."""
        return super(PBSControllerLauncher, self).start(1)


class PBSEngineSetLauncher(PBSLauncher, BatchClusterAppMixin):
    """Launch Engines using PBS"""
    batch_file_name = Unicode(u'pbs_engines', config=True,
        help="batch file name for the engine(s) job.")
    default_template= Unicode(u"""#!/bin/sh
#PBS -V
#PBS -N ipengine
%s --profile-dir="{profile_dir}" --cluster-id="{cluster_id}"
"""%(' '.join(map(pipes.quote,ipengine_cmd_argv))))

    def start(self, n):
        """Start n engines by profile or profile_dir."""
        return super(PBSEngineSetLauncher, self).start(n)

#SGE is very similar to PBS

class SGELauncher(PBSLauncher):
    """Sun GridEngine is a PBS clone with slightly different syntax"""
    job_array_regexp = CRegExp('#\$\W+\-t')
    job_array_template = Unicode('#$ -t 1-{n}')
    queue_regexp = CRegExp('#\$\W+-q\W+\$?\w+')
    queue_template = Unicode('#$ -q {queue}')

class SGEControllerLauncher(SGELauncher, BatchClusterAppMixin):
    """Launch a controller using SGE."""

    batch_file_name = Unicode(u'sge_controller', config=True,
        help="batch file name for the ipontroller job.")
    default_template= Unicode(u"""#$ -V
#$ -S /bin/sh
#$ -N ipcontroller
%s --log-to-file --profile-dir="{profile_dir}" --cluster-id="{cluster_id}"
"""%(' '.join(map(pipes.quote, ipcontroller_cmd_argv))))

    def start(self):
        """Start the controller by profile or profile_dir."""
        return super(SGEControllerLauncher, self).start(1)

class SGEEngineSetLauncher(SGELauncher, BatchClusterAppMixin):
    """Launch Engines with SGE"""
    batch_file_name = Unicode(u'sge_engines', config=True,
        help="batch file name for the engine(s) job.")
    default_template = Unicode("""#$ -V
#$ -S /bin/sh
#$ -N ipengine
%s --profile-dir="{profile_dir}" --cluster-id="{cluster_id}"
"""%(' '.join(map(pipes.quote, ipengine_cmd_argv))))

    def start(self, n):
        """Start n engines by profile or profile_dir."""
        return super(SGEEngineSetLauncher, self).start(n)


# LSF launchers

class LSFLauncher(BatchSystemLauncher):
    """A BatchSystemLauncher subclass for LSF."""

    submit_command = List(['bsub'], config=True,
                          help="The PBS submit command ['bsub']")
    delete_command = List(['bkill'], config=True,
                          help="The PBS delete command ['bkill']")
    job_id_regexp = CRegExp(r'\d+', config=True,
                            help="Regular expresion for identifying the job ID [r'\d+']")

    batch_file = Unicode(u'')
    job_array_regexp = CRegExp('#BSUB[ \t]-J+\w+\[\d+-\d+\]')
    job_array_template = Unicode('#BSUB -J ipengine[1-{n}]')
    queue_regexp = CRegExp('#BSUB[ \t]+-q[ \t]+\w+')
    queue_template = Unicode('#BSUB -q {queue}')

    def start(self, n):
        """Start n copies of the process using LSF batch system.
        This cant inherit from the base class because bsub expects
        to be piped a shell script in order to honor the #BSUB directives :
        bsub < script
        """
        # Here we save profile_dir in the context so they
        # can be used in the batch script template as {profile_dir}
        self.write_batch_script(n)
        piped_cmd = self.args[0]+'<\"'+self.args[1]+'\"'
        self.log.debug("Starting %s: %s", self.__class__.__name__, piped_cmd)
        p = Popen(piped_cmd, shell=True,env=os.environ,stdout=PIPE)
        output,err = p.communicate()
        output = output.decode(DEFAULT_ENCODING, 'replace')
        job_id = self.parse_job_id(output)
        self.notify_start(job_id)
        return job_id


class LSFControllerLauncher(LSFLauncher, BatchClusterAppMixin):
    """Launch a controller using LSF."""

    batch_file_name = Unicode(u'lsf_controller', config=True,
                              help="batch file name for the controller job.")
    default_template= Unicode("""#!/bin/sh
    #BSUB -J ipcontroller
    #BSUB -oo ipcontroller.o.%%J
    #BSUB -eo ipcontroller.e.%%J
    %s --log-to-file --profile-dir="{profile_dir}" --cluster-id="{cluster_id}"
    """%(' '.join(map(pipes.quote,ipcontroller_cmd_argv))))

    def start(self):
        """Start the controller by profile or profile_dir."""
        return super(LSFControllerLauncher, self).start(1)


class LSFEngineSetLauncher(LSFLauncher, BatchClusterAppMixin):
    """Launch Engines using LSF"""
    batch_file_name = Unicode(u'lsf_engines', config=True,
                              help="batch file name for the engine(s) job.")
    default_template= Unicode(u"""#!/bin/sh
    #BSUB -oo ipengine.o.%%J
    #BSUB -eo ipengine.e.%%J
    %s --profile-dir="{profile_dir}" --cluster-id="{cluster_id}"
    """%(' '.join(map(pipes.quote, ipengine_cmd_argv))))

    def start(self, n):
        """Start n engines by profile or profile_dir."""
        return super(LSFEngineSetLauncher, self).start(n)


#-----------------------------------------------------------------------------
# A launcher for ipcluster itself!
#-----------------------------------------------------------------------------


class IPClusterLauncher(LocalProcessLauncher):
    """Launch the ipcluster program in an external process."""

    ipcluster_cmd = List(ipcluster_cmd_argv, config=True,
        help="Popen command for ipcluster")
    ipcluster_args = List(
        ['--clean-logs=True', '--log-to-file', '--log-level=%i'%logging.INFO], config=True,
        help="Command line arguments to pass to ipcluster.")
    ipcluster_subcommand = Unicode('start')
    profile = Unicode('default')
    n = Integer(2)

    def find_args(self):
        return self.ipcluster_cmd + [self.ipcluster_subcommand] + \
            ['--n=%i'%self.n, '--profile=%s'%self.profile] + \
            self.ipcluster_args

    def start(self):
        return super(IPClusterLauncher, self).start()

#-----------------------------------------------------------------------------
# Collections of launchers
#-----------------------------------------------------------------------------

local_launchers = [
    LocalControllerLauncher,
    LocalEngineLauncher,
    LocalEngineSetLauncher,
]
mpi_launchers = [
    MPILauncher,
    MPIControllerLauncher,
    MPIEngineSetLauncher,
]
ssh_launchers = [
    SSHLauncher,
    SSHControllerLauncher,
    SSHEngineLauncher,
    SSHEngineSetLauncher,
    SSHProxyEngineSetLauncher,
]
winhpc_launchers = [
    WindowsHPCLauncher,
    WindowsHPCControllerLauncher,
    WindowsHPCEngineSetLauncher,
]
pbs_launchers = [
    PBSLauncher,
    PBSControllerLauncher,
    PBSEngineSetLauncher,
]
sge_launchers = [
    SGELauncher,
    SGEControllerLauncher,
    SGEEngineSetLauncher,
]
lsf_launchers = [
    LSFLauncher,
    LSFControllerLauncher,
    LSFEngineSetLauncher,
]
all_launchers = local_launchers + mpi_launchers + ssh_launchers + winhpc_launchers\
                + pbs_launchers + sge_launchers + lsf_launchers

