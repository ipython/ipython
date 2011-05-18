#!/usr/bin/env python
# encoding: utf-8
"""
The ipcluster application.
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

import errno
import logging
import os
import re
import signal

from subprocess import check_call, CalledProcessError, PIPE
import zmq
from zmq.eventloop import ioloop

from IPython.config.loader import Config
from IPython.utils.importstring import import_item
from IPython.utils.traitlets import Int, CStr, CUnicode, Str, Bool, CFloat, Dict, List

from IPython.parallel.apps.clusterdir import (
    ClusterDirApplication, ClusterDirError,
    PIDFileError,
    base_flags,
)


#-----------------------------------------------------------------------------
# Module level variables
#-----------------------------------------------------------------------------


default_config_file_name = u'ipcluster_config.py'


_description = """\
Start an IPython cluster for parallel computing.\n\n

An IPython cluster consists of 1 controller and 1 or more engines.
This command automates the startup of these processes using a wide
range of startup methods (SSH, local processes, PBS, mpiexec,
Windows HPC Server 2008). To start a cluster with 4 engines on your
local host simply do 'ipcluster start n=4'. For more complex usage
you will typically do 'ipcluster --create profile=mycluster', then edit
configuration files, followed by 'ipcluster --start -p mycluster -n 4'.
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
start_help = """Start an ipython cluster by its profile name or cluster
            directory. Cluster directories contain configuration, log and
            security related files and are named using the convention
            'cluster_<profile>' and should be creating using the 'start'
            subcommand of 'ipcluster'. If your cluster directory is in 
            the cwd or the ipython directory, you can simply refer to it
            using its profile name, 'ipcluster start -n 4 -p <profile>`,
            otherwise use the '--cluster-dir' option.
            """
stop_help = """Stop a running ipython cluster by its profile name or cluster
            directory. Cluster directories are named using the convention
            'cluster_<profile>'. If your cluster directory is in 
            the cwd or the ipython directory, you can simply refer to it
            using its profile name, 'ipcluster stop -p <profile>`, otherwise
            use the '--cluster-dir' option.
            """
engines_help = """Start one or more engines to connect to an existing Cluster
            by profile name or cluster directory.
            Cluster directories contain configuration, log and
            security related files and are named using the convention
            'cluster_<profile>' and should be creating using the 'start'
            subcommand of 'ipcluster'. If your cluster directory is in 
            the cwd or the ipython directory, you can simply refer to it
            using its profile name, 'ipcluster --engines -n 4 -p <profile>`,
            otherwise use the 'cluster_dir' option.
            """
create_help = """Create an ipython cluster directory by its profile name or
            cluster directory path. Cluster directories contain
            configuration, log and security related files and are named
            using the convention 'cluster_<profile>'. By default they are
            located in your ipython directory. Once created, you will
            probably need to edit the configuration files in the cluster
            directory to configure your cluster. Most users will create a
            cluster directory by profile name,
            'ipcluster create -p mycluster', which will put the directory
            in '<ipython_dir>/cluster_mycluster'.
            """
list_help = """List all available clusters, by cluster directory, that can
            be found in the current working directly or in the ipython
            directory. Cluster directories are named using the convention
            'cluster_<profile>'."""


flags = {}
flags.update(base_flags)
flags.update({
    'start' : ({ 'IPClusterApp': Config({'subcommand' : 'start'})} , start_help),
    'stop' : ({ 'IPClusterApp': Config({'subcommand' : 'stop'})} , stop_help),
    'create' : ({ 'IPClusterApp': Config({'subcommand' : 'create'})} , create_help),
    'engines' : ({ 'IPClusterApp': Config({'subcommand' : 'engines'})} , engines_help),
    'list' : ({ 'IPClusterApp': Config({'subcommand' : 'list'})} , list_help),

})

class IPClusterApp(ClusterDirApplication):

    name = u'ipcluster'
    description = _description
    usage = None
    default_config_file_name = default_config_file_name
    default_log_level = logging.INFO
    auto_create_cluster_dir = False
    classes = List()
    def _classes_default(self,):
        from IPython.parallel.apps import launcher
        return launcher.all_launchers

    n = Int(0, config=True,
        help="The number of engines to start.")
    signal = Int(signal.SIGINT, config=True,
        help="signal to use for stopping. [default: SIGINT]")
    delay = CFloat(1., config=True,
        help="delay (in s) between starting the controller and the engines")

    subcommand = Str('', config=True,
        help="""ipcluster has a variety of subcommands. The general way of
        running ipcluster is 'ipcluster --<cmd> [options]'."""
        )

    controller_launcher_class = Str('IPython.parallel.apps.launcher.LocalControllerLauncher',
        config=True,
        help="The class for launching a Controller."
        )
    engine_launcher_class = Str('IPython.parallel.apps.launcher.LocalEngineSetLauncher',
        config=True,
        help="The class for launching Engines."
        )
    reset = Bool(False, config=True,
        help="Whether to reset config files as part of '--create'."
        )
    daemonize = Bool(False, config=True,
        help='Daemonize the ipcluster program. This implies --log-to-file')

    def _daemonize_changed(self, name, old, new):
        if new:
            self.log_to_file = True

    def _n_changed(self, name, old, new):
        # propagate n all over the place...
        # TODO make this clean
        # ensure all classes are covered.
        self.config.LocalEngineSetLauncher.n=new
        self.config.MPIExecEngineSetLauncher.n=new
        self.config.SSHEngineSetLauncher.n=new
        self.config.PBSEngineSetLauncher.n=new
        self.config.SGEEngineSetLauncher.n=new
        self.config.WinHPEngineSetLauncher.n=new

    aliases = Dict(dict(
        n='IPClusterApp.n',
        signal = 'IPClusterApp.signal',
        delay = 'IPClusterApp.delay',
        clauncher = 'IPClusterApp.controller_launcher_class',
        elauncher = 'IPClusterApp.engine_launcher_class',
    ))
    flags = Dict(flags)

    def init_clusterdir(self):
        subcommand = self.subcommand
        if subcommand=='list':
            self.list_cluster_dirs()
            self.exit(0)
        if subcommand=='create':
            reset = self.reset_config
            self.auto_create_cluster_dir = True
            super(IPClusterApp, self).init_clusterdir()
            self.log.info('Copying default config files to cluster directory '
            '[overwrite=%r]' % (reset,))
            self.cluster_dir.copy_all_config_files(overwrite=reset)
        elif subcommand=='start' or subcommand=='stop':
            self.auto_create_cluster_dir = True
            try:
                super(IPClusterApp, self).init_clusterdir()
            except ClusterDirError:
                raise ClusterDirError(
                    "Could not find a cluster directory. A cluster dir must "
                    "be created before running 'ipcluster start'.  Do "
                    "'ipcluster create -h' or 'ipcluster list -h' for more "
                    "information about creating and listing cluster dirs."
                )
        elif subcommand=='engines':
            self.auto_create_cluster_dir = False
            try:
                super(IPClusterApp, self).init_clusterdir()
            except ClusterDirError:
                raise ClusterDirError(
                    "Could not find a cluster directory. A cluster dir must "
                    "be created before running 'ipcluster start'.  Do "
                    "'ipcluster create -h' or 'ipcluster list -h' for more "
                    "information about creating and listing cluster dirs."
                )

    def list_cluster_dirs(self):
        # Find the search paths
        cluster_dir_paths = os.environ.get('IPCLUSTER_DIR_PATH','')
        if cluster_dir_paths:
            cluster_dir_paths = cluster_dir_paths.split(':')
        else:
            cluster_dir_paths = []
        try:
            ipython_dir = self.ipython_dir
        except AttributeError:
            ipython_dir = self.ipython_dir
        paths = [os.getcwd(), ipython_dir] + \
            cluster_dir_paths
        paths = list(set(paths))

        self.log.info('Searching for cluster dirs in paths: %r' % paths)
        for path in paths:
            files = os.listdir(path)
            for f in files:
                full_path = os.path.join(path, f)
                if os.path.isdir(full_path) and f.startswith('cluster_'):
                    profile = full_path.split('_')[-1]
                    start_cmd = 'ipcluster --start profile=%s n=4' % profile
                    print start_cmd + " ==> " + full_path

    def init_launchers(self):
        config = self.config
        subcmd = self.subcommand
        if subcmd =='start':
            self.start_logging()
            self.loop = ioloop.IOLoop.instance()
            # reactor.callWhenRunning(self.start_launchers)
            dc = ioloop.DelayedCallback(self.start_launchers, 0, self.loop)
            dc.start()
        if subcmd == 'engines':
            self.start_logging()
            self.loop = ioloop.IOLoop.instance()
            # reactor.callWhenRunning(self.start_launchers)
            engine_only = lambda : self.start_launchers(controller=False)
            dc = ioloop.DelayedCallback(engine_only, 0, self.loop)
            dc.start()

    def start_launchers(self, controller=True):
        config = self.config

        # Create the launchers. In both bases, we set the work_dir of
        # the launcher to the cluster_dir. This is where the launcher's
        # subprocesses will be launched. It is not where the controller
        # and engine will be launched.
        if controller:
            clsname = self.controller_launcher_class
            if '.' not in clsname:
                clsname = 'IPython.parallel.apps.launcher.'+clsname
            cl_class = import_item(clsname)
            self.controller_launcher = cl_class(
                work_dir=self.cluster_dir.location, config=config,
                logname=self.log.name
            )
            # Setup the observing of stopping. If the controller dies, shut
            # everything down as that will be completely fatal for the engines.
            self.controller_launcher.on_stop(self.stop_launchers)
            # But, we don't monitor the stopping of engines. An engine dying
            # is just fine and in principle a user could start a new engine.
            # Also, if we did monitor engine stopping, it is difficult to
            # know what to do when only some engines die. Currently, the
            # observing of engine stopping is inconsistent. Some launchers
            # might trigger on a single engine stopping, other wait until
            # all stop.  TODO: think more about how to handle this.
        else:
            self.controller_launcher = None
        
        clsname = self.engine_launcher_class
        if '.' not in clsname:
            # not a module, presume it's the raw name in apps.launcher
            clsname = 'IPython.parallel.apps.launcher.'+clsname
        print repr(clsname)
        el_class = import_item(clsname)

        self.engine_launcher = el_class(
            work_dir=self.cluster_dir.location, config=config, logname=self.log.name
        )

        # Setup signals
        signal.signal(signal.SIGINT, self.sigint_handler)

        # Start the controller and engines
        self._stopping = False  # Make sure stop_launchers is not called 2x.
        if controller:
            self.start_controller()
        dc = ioloop.DelayedCallback(self.start_engines, 1000*self.delay*controller, self.loop)
        dc.start()
        self.startup_message()

    def startup_message(self, r=None):
        self.log.info("IPython cluster: started")
        return r
        
    def start_controller(self, r=None):
        # self.log.info("In start_controller")
        config = self.config
        d = self.controller_launcher.start(
            cluster_dir=self.cluster_dir.location
        )
        return d
            
    def start_engines(self, r=None):
        # self.log.info("In start_engines")
        config = self.config
        
        d = self.engine_launcher.start(
            self.n,
            cluster_dir=self.cluster_dir.location
        )
        return d

    def stop_controller(self, r=None):
        # self.log.info("In stop_controller")
        if self.controller_launcher and self.controller_launcher.running:
            return self.controller_launcher.stop()

    def stop_engines(self, r=None):
        # self.log.info("In stop_engines")
        if self.engine_launcher.running:
            d = self.engine_launcher.stop()
            # d.addErrback(self.log_err)
            return d
        else:
            return None

    def log_err(self, f):
        self.log.error(f.getTraceback())
        return None
        
    def stop_launchers(self, r=None):
        if not self._stopping:
            self._stopping = True
            # if isinstance(r, failure.Failure):
            #     self.log.error('Unexpected error in ipcluster:')
            #     self.log.info(r.getTraceback())
            self.log.error("IPython cluster: stopping")
            # These return deferreds. We are not doing anything with them
            # but we are holding refs to them as a reminder that they 
            # do return deferreds.
            d1 = self.stop_engines()
            d2 = self.stop_controller()
            # Wait a few seconds to let things shut down.
            dc = ioloop.DelayedCallback(self.loop.stop, 4000, self.loop)
            dc.start()
            # reactor.callLater(4.0, reactor.stop)

    def sigint_handler(self, signum, frame):
        self.stop_launchers()
        
    def start_logging(self):
        # Remove old log files of the controller and engine
        if self.clean_logs:
            log_dir = self.cluster_dir.log_dir
            for f in os.listdir(log_dir):
                if re.match(r'ip(engine|controller)z-\d+\.(log|err|out)',f):
                    os.remove(os.path.join(log_dir, f))
        # This will remove old log files for ipcluster itself
        # super(IPClusterApp, self).start_logging()

    def start(self):
        """Start the application, depending on what subcommand is used."""
        subcmd = self.subcommand
        if subcmd=='create':
            # init_clusterdir step completed create action
            return
        elif subcmd=='start':
            self.start_app_start()
        elif subcmd=='stop':
            self.start_app_stop()
        elif subcmd=='engines':
            self.start_app_engines()
        else:
            self.log.fatal("one command of '--start', '--stop', '--list', '--create', '--engines'"
            " must be specified")
            self.exit(-1)

    def start_app_start(self):
        """Start the app for the start subcommand."""
        config = self.config
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
                from twisted.scripts._twistd_unix import daemonize
                daemonize()

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

    def start_app_engines(self):
        """Start the app for the start subcommand."""
        config = self.config
        # First see if the cluster is already running
        
        # Now log and daemonize
        self.log.info(
            'Starting engines with [daemon=%r]' % self.daemonize
        )
        # TODO: Get daemonize working on Windows or as a Windows Server.
        if self.daemonize:
            if os.name=='posix':
                from twisted.scripts._twistd_unix import daemonize
                daemonize()

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
        # self.remove_pid_file()
    
    def start_app_stop(self):
        """Start the app for the stop subcommand."""
        config = self.config
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


def launch_new_instance():
    """Create and run the IPython cluster."""
    app = IPClusterApp()
    app.parse_command_line()
    cl_config = app.config
    app.init_clusterdir()
    if app.config_file:
        app.load_config_file(app.config_file)
    else:
        app.load_config_file(app.default_config_file_name, path=app.cluster_dir.location)
    # command-line should *override* config file, but command-line is necessary
    # to determine clusterdir, etc.
    app.update_config(cl_config)

    app.to_work_dir()
    app.init_launchers()

    app.start()


if __name__ == '__main__':
    launch_new_instance()

