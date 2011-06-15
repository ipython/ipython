#!/usr/bin/env python
# encoding: utf-8
"""
The ipcluster application.

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

import errno
import logging
import os
import re
import signal

from subprocess import check_call, CalledProcessError, PIPE
import zmq
from zmq.eventloop import ioloop

from IPython.config.application import Application, boolean_flag
from IPython.config.loader import Config
from IPython.core.application import BaseIPythonApplication
from IPython.core.profiledir import ProfileDir
from IPython.utils.daemonize import daemonize
from IPython.utils.importstring import import_item
from IPython.utils.traitlets import Int, Unicode, Bool, CFloat, Dict, List

from IPython.parallel.apps.baseapp import (
    BaseParallelApplication,
    PIDFileError,
    base_flags, base_aliases
)


#-----------------------------------------------------------------------------
# Module level variables
#-----------------------------------------------------------------------------


default_config_file_name = u'ipcluster_config.py'


_description = """Start an IPython cluster for parallel computing.

An IPython cluster consists of 1 controller and 1 or more engines.
This command automates the startup of these processes using a wide
range of startup methods (SSH, local processes, PBS, mpiexec,
Windows HPC Server 2008). To start a cluster with 4 engines on your
local host simply do 'ipcluster start n=4'. For more complex usage
you will typically do 'ipcluster create profile=mycluster', then edit
configuration files, followed by 'ipcluster start profile=mycluster n=4'.
"""


# Exit codes for ipcluster

# This will be the exit code if the ipcluster appears to be running because
# a .pid file exists
ALREADY_STARTED = 10


# This will be the exit code if ipcluster stop is run, but there is not .pid
# file to be found.
ALREADY_STOPPED = 11

# This will be the exit code if ipcluster engines is run, but there is not .pid
# file to be found.
NO_CLUSTER = 12


#-----------------------------------------------------------------------------
# Main application
#-----------------------------------------------------------------------------
start_help = """Start an IPython cluster for parallel computing

Start an ipython cluster by its profile name or cluster
directory. Cluster directories contain configuration, log and
security related files and are named using the convention
'profile_<name>' and should be creating using the 'start'
subcommand of 'ipcluster'. If your cluster directory is in 
the cwd or the ipython directory, you can simply refer to it
using its profile name, 'ipcluster start n=4 profile=<profile>`,
otherwise use the 'profile_dir' option.
"""
stop_help = """Stop a running IPython cluster

Stop a running ipython cluster by its profile name or cluster
directory. Cluster directories are named using the convention
'profile_<name>'. If your cluster directory is in 
the cwd or the ipython directory, you can simply refer to it
using its profile name, 'ipcluster stop profile=<profile>`, otherwise
use the 'profile_dir' option.
"""
engines_help = """Start engines connected to an existing IPython cluster

Start one or more engines to connect to an existing Cluster
by profile name or cluster directory.
Cluster directories contain configuration, log and
security related files and are named using the convention
'profile_<name>' and should be creating using the 'start'
subcommand of 'ipcluster'. If your cluster directory is in 
the cwd or the ipython directory, you can simply refer to it
using its profile name, 'ipcluster engines n=4 profile=<profile>`,
otherwise use the 'profile_dir' option.
"""
stop_aliases = dict(
    signal='IPClusterStop.signal',
    profile='BaseIPythonApplication.profile',
    profile_dir='ProfileDir.location',
)

class IPClusterStop(BaseParallelApplication):
    name = u'ipcluster'
    description = stop_help
    config_file_name = Unicode(default_config_file_name)
    
    signal = Int(signal.SIGINT, config=True,
        help="signal to use for stopping processes.")
        
    aliases = Dict(stop_aliases)
    
    def start(self):
        """Start the app for the stop subcommand."""
        try:
            pid = self.get_pid_from_file()
        except PIDFileError:
            self.log.critical(
                'Could not read pid file, cluster is probably not running.'
            )
            # Here I exit with a unusual exit status that other processes
            # can watch for to learn how I existed.
            self.remove_pid_file()
            self.exit(ALREADY_STOPPED)
        
        if not self.check_pid(pid):
            self.log.critical(
                'Cluster [pid=%r] is not running.' % pid
            )
            self.remove_pid_file()
            # Here I exit with a unusual exit status that other processes
            # can watch for to learn how I existed.
            self.exit(ALREADY_STOPPED)
            
        elif os.name=='posix':
            sig = self.signal
            self.log.info(
                "Stopping cluster [pid=%r] with [signal=%r]" % (pid, sig)
            )
            try:
                os.kill(pid, sig)
            except OSError:
                self.log.error("Stopping cluster failed, assuming already dead.",
                    exc_info=True)
                self.remove_pid_file()
        elif os.name=='nt':
            try:
                # kill the whole tree
                p = check_call(['taskkill', '-pid', str(pid), '-t', '-f'], stdout=PIPE,stderr=PIPE)
            except (CalledProcessError, OSError):
                self.log.error("Stopping cluster failed, assuming already dead.",
                    exc_info=True)
            self.remove_pid_file()
    
engine_aliases = {}
engine_aliases.update(base_aliases)
engine_aliases.update(dict(
    n='IPClusterEngines.n',
    elauncher = 'IPClusterEngines.engine_launcher_class',
))
class IPClusterEngines(BaseParallelApplication):

    name = u'ipcluster'
    description = engines_help
    usage = None
    config_file_name = Unicode(default_config_file_name)
    default_log_level = logging.INFO
    classes = List()
    def _classes_default(self):
        from IPython.parallel.apps import launcher
        launchers = launcher.all_launchers
        eslaunchers = [ l for l in launchers if 'EngineSet' in l.__name__]
        return [ProfileDir]+eslaunchers
    
    n = Int(2, config=True,
        help="The number of engines to start.")

    engine_launcher_class = Unicode('LocalEngineSetLauncher',
        config=True,
        help="The class for launching a set of Engines."
        )
    daemonize = Bool(False, config=True,
        help='Daemonize the ipcluster program. This implies --log-to-file')

    def _daemonize_changed(self, name, old, new):
        if new:
            self.log_to_file = True

    aliases = Dict(engine_aliases)
    # flags = Dict(flags)
    _stopping = False

    def initialize(self, argv=None):
        super(IPClusterEngines, self).initialize(argv)
        self.init_signal()
        self.init_launchers()
    
    def init_launchers(self):
        self.engine_launcher = self.build_launcher(self.engine_launcher_class)
        self.engine_launcher.on_stop(lambda r: self.loop.stop())
    
    def init_signal(self):
        # Setup signals
        signal.signal(signal.SIGINT, self.sigint_handler)
    
    def build_launcher(self, clsname):
        """import and instantiate a Launcher based on importstring"""
        if '.' not in clsname:
            # not a module, presume it's the raw name in apps.launcher
            clsname = 'IPython.parallel.apps.launcher.'+clsname
        # print repr(clsname)
        klass = import_item(clsname)

        launcher = klass(
            work_dir=self.profile_dir.location, config=self.config, log=self.log
        )
        return launcher
    
    def start_engines(self):
        self.log.info("Starting %i engines"%self.n)
        self.engine_launcher.start(
            self.n,
            self.profile_dir.location
        )

    def stop_engines(self):
        self.log.info("Stopping Engines...")
        if self.engine_launcher.running:
            d = self.engine_launcher.stop()
            return d
        else:
            return None

    def stop_launchers(self, r=None):
        if not self._stopping:
            self._stopping = True
            self.log.error("IPython cluster: stopping")
            self.stop_engines()
            # Wait a few seconds to let things shut down.
            dc = ioloop.DelayedCallback(self.loop.stop, 4000, self.loop)
            dc.start()

    def sigint_handler(self, signum, frame):
        self.log.debug("SIGINT received, stopping launchers...")
        self.stop_launchers()
        
    def start_logging(self):
        # Remove old log files of the controller and engine
        if self.clean_logs:
            log_dir = self.profile_dir.log_dir
            for f in os.listdir(log_dir):
                if re.match(r'ip(engine|controller)z-\d+\.(log|err|out)',f):
                    os.remove(os.path.join(log_dir, f))
        # This will remove old log files for ipcluster itself
        # super(IPBaseParallelApplication, self).start_logging()

    def start(self):
        """Start the app for the engines subcommand."""
        self.log.info("IPython cluster: started")
        # First see if the cluster is already running
        
        # Now log and daemonize
        self.log.info(
            'Starting engines with [daemon=%r]' % self.daemonize
        )
        # TODO: Get daemonize working on Windows or as a Windows Server.
        if self.daemonize:
            if os.name=='posix':
                daemonize()

        dc = ioloop.DelayedCallback(self.start_engines, 0, self.loop)
        dc.start()
        # Now write the new pid file AFTER our new forked pid is active.
        # self.write_pid_file()
        try:
            self.loop.start()
        except KeyboardInterrupt:
            pass
        except zmq.ZMQError as e:
            if e.errno == errno.EINTR:
                pass
            else:
                raise

start_aliases = {}
start_aliases.update(engine_aliases)
start_aliases.update(dict(
    delay='IPClusterStart.delay',
    clean_logs='IPClusterStart.clean_logs',
))

class IPClusterStart(IPClusterEngines):

    name = u'ipcluster'
    description = start_help
    default_log_level = logging.INFO
    auto_create = Bool(True, config=True,
        help="whether to create the profile_dir if it doesn't exist")
    classes = List()
    def _classes_default(self,):
        from IPython.parallel.apps import launcher
        return [ProfileDir] + [IPClusterEngines] + launcher.all_launchers
    
    clean_logs = Bool(True, config=True, 
        help="whether to cleanup old logs before starting")

    delay = CFloat(1., config=True,
        help="delay (in s) between starting the controller and the engines")

    controller_launcher_class = Unicode('LocalControllerLauncher',
        config=True,
        help="The class for launching a Controller."
        )
    reset = Bool(False, config=True,
        help="Whether to reset config files as part of '--create'."
        )
    
    # flags = Dict(flags)
    aliases = Dict(start_aliases)

    def init_launchers(self):
        self.controller_launcher = self.build_launcher(self.controller_launcher_class)
        self.engine_launcher = self.build_launcher(self.engine_launcher_class)
        self.controller_launcher.on_stop(self.stop_launchers)
    
    def start_controller(self):
        self.controller_launcher.start(
            self.profile_dir.location
        )
        
    def stop_controller(self):
        # self.log.info("In stop_controller")
        if self.controller_launcher and self.controller_launcher.running:
            return self.controller_launcher.stop()

    def stop_launchers(self, r=None):
        if not self._stopping:
            self.stop_controller()
            super(IPClusterStart, self).stop_launchers()

    def start(self):
        """Start the app for the start subcommand."""
        # First see if the cluster is already running
        try:
            pid = self.get_pid_from_file()
        except PIDFileError:
            pass
        else:
            if self.check_pid(pid):
                self.log.critical(
                    'Cluster is already running with [pid=%s]. '
                    'use "ipcluster stop" to stop the cluster.' % pid
                )
                # Here I exit with a unusual exit status that other processes
                # can watch for to learn how I existed.
                self.exit(ALREADY_STARTED)
            else:
                self.remove_pid_file()
                

        # Now log and daemonize
        self.log.info(
            'Starting ipcluster with [daemon=%r]' % self.daemonize
        )
        # TODO: Get daemonize working on Windows or as a Windows Server.
        if self.daemonize:
            if os.name=='posix':
                daemonize()

        dc = ioloop.DelayedCallback(self.start_controller, 0, self.loop)
        dc.start()
        dc = ioloop.DelayedCallback(self.start_engines, 1000*self.delay, self.loop)
        dc.start()
        # Now write the new pid file AFTER our new forked pid is active.
        self.write_pid_file()
        try:
            self.loop.start()
        except KeyboardInterrupt:
            pass
        except zmq.ZMQError as e:
            if e.errno == errno.EINTR:
                pass
            else:
                raise
        finally:
            self.remove_pid_file()

base='IPython.parallel.apps.ipclusterapp.IPCluster'

class IPClusterApp(Application):
    name = u'ipcluster'
    description = _description
    
    subcommands = {
                'start' : (base+'Start', start_help),
                'stop' : (base+'Stop', stop_help),
                'engines' : (base+'Engines', engines_help),
    }
    
    # no aliases or flags for parent App
    aliases = Dict()
    flags = Dict()
    
    def start(self):
        if self.subapp is None:
            print "No subcommand specified! Must specify one of: %s"%(self.subcommands.keys())
            print
            self.print_subcommands()
            self.exit(1)
        else:
            return self.subapp.start()

def launch_new_instance():
    """Create and run the IPython cluster."""
    app = IPBaseParallelApplication.instance()
    app.initialize()
    app.start()


if __name__ == '__main__':
    launch_new_instance()

