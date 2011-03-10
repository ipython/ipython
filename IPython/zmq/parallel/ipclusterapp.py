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

import zmq
from zmq.eventloop import ioloop

from IPython.external.argparse import ArgumentParser, SUPPRESS
from IPython.utils.importstring import import_item
from IPython.zmq.parallel.clusterdir import (
    ApplicationWithClusterDir, ClusterDirConfigLoader,
    ClusterDirError, PIDFileError
)


#-----------------------------------------------------------------------------
# Module level variables
#-----------------------------------------------------------------------------


default_config_file_name = u'ipclusterz_config.py'


_description = """\
Start an IPython cluster for parallel computing.\n\n

An IPython cluster consists of 1 controller and 1 or more engines.
This command automates the startup of these processes using a wide
range of startup methods (SSH, local processes, PBS, mpiexec,
Windows HPC Server 2008). To start a cluster with 4 engines on your
local host simply do 'ipclusterz start -n 4'. For more complex usage 
you will typically do 'ipclusterz create -p mycluster', then edit
configuration files, followed by 'ipclusterz start -p mycluster -n 4'.
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
# Command line options
#-----------------------------------------------------------------------------


class IPClusterAppConfigLoader(ClusterDirConfigLoader):

    def _add_arguments(self):
        # Don't call ClusterDirConfigLoader._add_arguments as we don't want
        # its defaults on self.parser. Instead, we will put those on
        # default options on our subparsers.
        
        # This has all the common options that all subcommands use
        parent_parser1 = ArgumentParser(
            add_help=False,
            argument_default=SUPPRESS
        )
        self._add_ipython_dir(parent_parser1)
        self._add_log_level(parent_parser1)

        # This has all the common options that other subcommands use
        parent_parser2 = ArgumentParser(
            add_help=False,
            argument_default=SUPPRESS
        )
        self._add_cluster_profile(parent_parser2)
        self._add_cluster_dir(parent_parser2)
        self._add_work_dir(parent_parser2)
        paa = parent_parser2.add_argument
        paa('--log-to-file',
            action='store_true', dest='Global.log_to_file', 
            help='Log to a file in the log directory (default is stdout)')

        # Create the object used to create the subparsers.
        subparsers = self.parser.add_subparsers(
            dest='Global.subcommand',
            title='ipcluster subcommands',
            description=
            """ipcluster has a variety of subcommands. The general way of 
            running ipcluster is 'ipclusterz <cmd> [options]'. To get help
            on a particular subcommand do 'ipclusterz <cmd> -h'."""
            # help="For more help, type 'ipclusterz <cmd> -h'",
        )

        # The "list" subcommand parser
        parser_list = subparsers.add_parser(
            'list',
            parents=[parent_parser1],
            argument_default=SUPPRESS,
            help="List all clusters in cwd and ipython_dir.",
            description=
            """List all available clusters, by cluster directory, that can
            be found in the current working directly or in the ipython
            directory. Cluster directories are named using the convention
            'clusterz_<profile>'."""
        )

        # The "create" subcommand parser
        parser_create = subparsers.add_parser(
            'create',
            parents=[parent_parser1, parent_parser2],
            argument_default=SUPPRESS,
            help="Create a new cluster directory.",
            description=
            """Create an ipython cluster directory by its profile name or 
            cluster directory path. Cluster directories contain 
            configuration, log and security related files and are named 
            using the convention 'clusterz_<profile>'. By default they are
            located in your ipython directory. Once created, you will
            probably need to edit the configuration files in the cluster
            directory to configure your cluster. Most users will create a
            cluster directory by profile name, 
            'ipclusterz create -p mycluster', which will put the directory
            in '<ipython_dir>/clusterz_mycluster'. 
            """
        )
        paa = parser_create.add_argument
        paa('--reset-config',
            dest='Global.reset_config', action='store_true',
            help=
            """Recopy the default config files to the cluster directory.
            You will loose any modifications you have made to these files.""")

        # The "start" subcommand parser
        parser_start = subparsers.add_parser(
            'start',
            parents=[parent_parser1, parent_parser2],
            argument_default=SUPPRESS,
            help="Start a cluster.",
            description=
            """Start an ipython cluster by its profile name or cluster 
            directory. Cluster directories contain configuration, log and
            security related files and are named using the convention
            'clusterz_<profile>' and should be creating using the 'start'
            subcommand of 'ipcluster'. If your cluster directory is in 
            the cwd or the ipython directory, you can simply refer to it
            using its profile name, 'ipclusterz start -n 4 -p <profile>`,
            otherwise use the '--cluster-dir' option.
            """
        )
        
        paa = parser_start.add_argument
        paa('-n', '--number',
            type=int, dest='Global.n',
            help='The number of engines to start.',
            metavar='Global.n')
        paa('--clean-logs',
            dest='Global.clean_logs', action='store_true',
            help='Delete old log flies before starting.')
        paa('--no-clean-logs',
            dest='Global.clean_logs', action='store_false',
            help="Don't delete old log flies before starting.")
        paa('--daemon',
            dest='Global.daemonize', action='store_true',
            help='Daemonize the ipcluster program. This implies --log-to-file')
        paa('--no-daemon',
            dest='Global.daemonize', action='store_false',
            help="Dont't daemonize the ipcluster program.")
        paa('--delay',
            type=float, dest='Global.delay',
            help="Specify the delay (in seconds) between starting the controller and starting the engine(s).")

        # The "stop" subcommand parser
        parser_stop = subparsers.add_parser(
            'stop',
            parents=[parent_parser1, parent_parser2],
            argument_default=SUPPRESS,
            help="Stop a running cluster.",
            description=
            """Stop a running ipython cluster by its profile name or cluster 
            directory. Cluster directories are named using the convention
            'clusterz_<profile>'. If your cluster directory is in 
            the cwd or the ipython directory, you can simply refer to it
            using its profile name, 'ipclusterz stop -p <profile>`, otherwise
            use the '--cluster-dir' option.
            """
        )
        paa = parser_stop.add_argument
        paa('--signal',
            dest='Global.signal', type=int,
            help="The signal number to use in stopping the cluster (default=2).",
            metavar="Global.signal")
        
        # the "engines" subcommand parser
        parser_engines = subparsers.add_parser(
            'engines',
            parents=[parent_parser1, parent_parser2],
            argument_default=SUPPRESS,
            help="Attach some engines to an existing controller or cluster.",
            description=
            """Start one or more engines to connect to an existing Cluster
            by profile name or cluster directory.
            Cluster directories contain configuration, log and
            security related files and are named using the convention
            'clusterz_<profile>' and should be creating using the 'start'
            subcommand of 'ipcluster'. If your cluster directory is in 
            the cwd or the ipython directory, you can simply refer to it
            using its profile name, 'ipclusterz engines -n 4 -p <profile>`,
            otherwise use the '--cluster-dir' option.
            """
        )
        paa = parser_engines.add_argument
        paa('-n', '--number',
            type=int, dest='Global.n',
            help='The number of engines to start.',
            metavar='Global.n')
        paa('--daemon',
            dest='Global.daemonize', action='store_true',
            help='Daemonize the ipcluster program. This implies --log-to-file')
        paa('--no-daemon',
            dest='Global.daemonize', action='store_false',
            help="Dont't daemonize the ipcluster program.")

#-----------------------------------------------------------------------------
# Main application
#-----------------------------------------------------------------------------


class IPClusterApp(ApplicationWithClusterDir):

    name = u'ipclusterz'
    description = _description
    usage = None
    command_line_loader = IPClusterAppConfigLoader
    default_config_file_name = default_config_file_name
    default_log_level = logging.INFO
    auto_create_cluster_dir = False

    def create_default_config(self):
        super(IPClusterApp, self).create_default_config()
        self.default_config.Global.controller_launcher = \
            'IPython.zmq.parallel.launcher.LocalControllerLauncher'
        self.default_config.Global.engine_launcher = \
            'IPython.zmq.parallel.launcher.LocalEngineSetLauncher'
        self.default_config.Global.n = 2
        self.default_config.Global.delay = 2
        self.default_config.Global.reset_config = False
        self.default_config.Global.clean_logs = True
        self.default_config.Global.signal = signal.SIGINT
        self.default_config.Global.daemonize = False

    def find_resources(self):
        subcommand = self.command_line_config.Global.subcommand
        if subcommand=='list':
            self.list_cluster_dirs()
            # Exit immediately because there is nothing left to do.
            self.exit()
        elif subcommand=='create':
            self.auto_create_cluster_dir = True
            super(IPClusterApp, self).find_resources()
        elif subcommand=='start' or subcommand=='stop':
            self.auto_create_cluster_dir = True
            try:
                super(IPClusterApp, self).find_resources()
            except ClusterDirError:
                raise ClusterDirError(
                    "Could not find a cluster directory. A cluster dir must "
                    "be created before running 'ipclusterz start'.  Do "
                    "'ipclusterz create -h' or 'ipclusterz list -h' for more "
                    "information about creating and listing cluster dirs."
                )
        elif subcommand=='engines':
            self.auto_create_cluster_dir = False
            try:
                super(IPClusterApp, self).find_resources()
            except ClusterDirError:
                raise ClusterDirError(
                    "Could not find a cluster directory. A cluster dir must "
                    "be created before running 'ipclusterz start'.  Do "
                    "'ipclusterz create -h' or 'ipclusterz list -h' for more "
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
            ipython_dir = self.command_line_config.Global.ipython_dir
        except AttributeError:
            ipython_dir = self.default_config.Global.ipython_dir
        paths = [os.getcwd(), ipython_dir] + \
            cluster_dir_paths
        paths = list(set(paths))

        self.log.info('Searching for cluster dirs in paths: %r' % paths)
        for path in paths:
            files = os.listdir(path)
            for f in files:
                full_path = os.path.join(path, f)
                if os.path.isdir(full_path) and f.startswith('clusterz_'):
                    profile = full_path.split('_')[-1]
                    start_cmd = 'ipclusterz start -p %s -n 4' % profile
                    print start_cmd + " ==> " + full_path

    def pre_construct(self):
        # IPClusterApp.pre_construct() is where we cd to the working directory.
        super(IPClusterApp, self).pre_construct()
        config = self.master_config
        try:
            daemon = config.Global.daemonize
            if daemon:
                config.Global.log_to_file = True
        except AttributeError:
            pass

    def construct(self):
        config = self.master_config
        subcmd = config.Global.subcommand
        reset = config.Global.reset_config
        if subcmd == 'list':
            return
        if subcmd == 'create':
            self.log.info('Copying default config files to cluster directory '
            '[overwrite=%r]' % (reset,))
            self.cluster_dir_obj.copy_all_config_files(overwrite=reset)
        if subcmd =='start':
            self.cluster_dir_obj.copy_all_config_files(overwrite=False)
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
        config = self.master_config

        # Create the launchers. In both bases, we set the work_dir of
        # the launcher to the cluster_dir. This is where the launcher's
        # subprocesses will be launched. It is not where the controller
        # and engine will be launched.
        if controller:
            cl_class = import_item(config.Global.controller_launcher)
            self.controller_launcher = cl_class(
                work_dir=self.cluster_dir, config=config,
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
        
        el_class = import_item(config.Global.engine_launcher)
        self.engine_launcher = el_class(
            work_dir=self.cluster_dir, config=config, logname=self.log.name
        )

        # Setup signals
        signal.signal(signal.SIGINT, self.sigint_handler)

        # Start the controller and engines
        self._stopping = False  # Make sure stop_launchers is not called 2x.
        if controller:
            self.start_controller()
        dc = ioloop.DelayedCallback(self.start_engines, 1000*config.Global.delay*controller, self.loop)
        dc.start()
        self.startup_message()

    def startup_message(self, r=None):
        self.log.info("IPython cluster: started")
        return r
        
    def start_controller(self, r=None):
        # self.log.info("In start_controller")
        config = self.master_config
        d = self.controller_launcher.start(
            cluster_dir=config.Global.cluster_dir
        )
        return d
            
    def start_engines(self, r=None):
        # self.log.info("In start_engines")
        config = self.master_config
        
        d = self.engine_launcher.start(
            config.Global.n,
            cluster_dir=config.Global.cluster_dir
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
        if self.master_config.Global.clean_logs:
            log_dir = self.master_config.Global.log_dir
            for f in os.listdir(log_dir):
                if re.match(r'ip(engine|controller)z-\d+\.(log|err|out)',f):
                    os.remove(os.path.join(log_dir, f))
        # This will remove old log files for ipcluster itself
        super(IPClusterApp, self).start_logging()

    def start_app(self):
        """Start the application, depending on what subcommand is used."""
        subcmd = self.master_config.Global.subcommand
        if subcmd=='create' or subcmd=='list':
            return
        elif subcmd=='start':
            self.start_app_start()
        elif subcmd=='stop':
            self.start_app_stop()
        elif subcmd=='engines':
            self.start_app_engines()

    def start_app_start(self):
        """Start the app for the start subcommand."""
        config = self.master_config
        # First see if the cluster is already running
        try:
            pid = self.get_pid_from_file()
        except PIDFileError:
            pass
        else:
            self.log.critical(
                'Cluster is already running with [pid=%s]. '
                'use "ipclusterz stop" to stop the cluster.' % pid
            )
            # Here I exit with a unusual exit status that other processes
            # can watch for to learn how I existed.
            self.exit(ALREADY_STARTED)

        # Now log and daemonize
        self.log.info(
            'Starting ipclusterz with [daemon=%r]' % config.Global.daemonize
        )
        # TODO: Get daemonize working on Windows or as a Windows Server.
        if config.Global.daemonize:
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
        self.remove_pid_file()

    def start_app_engines(self):
        """Start the app for the start subcommand."""
        config = self.master_config
        # First see if the cluster is already running
        
        # Now log and daemonize
        self.log.info(
            'Starting engines with [daemon=%r]' % config.Global.daemonize
        )
        # TODO: Get daemonize working on Windows or as a Windows Server.
        if config.Global.daemonize:
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
        config = self.master_config
        try:
            pid = self.get_pid_from_file()
        except PIDFileError:
            self.log.critical(
                'Problem reading pid file, cluster is probably not running.'
            )
            # Here I exit with a unusual exit status that other processes
            # can watch for to learn how I existed.
            self.exit(ALREADY_STOPPED)
        else:
            if os.name=='posix':
                sig = config.Global.signal
                self.log.info(
                    "Stopping cluster [pid=%r] with [signal=%r]" % (pid, sig)
                )
                os.kill(pid, sig)
            elif os.name=='nt':
                # As of right now, we don't support daemonize on Windows, so
                # stop will not do anything. Minimally, it should clean up the
                # old .pid files.
                self.remove_pid_file()


def launch_new_instance():
    """Create and run the IPython cluster."""
    app = IPClusterApp()
    app.start()


if __name__ == '__main__':
    launch_new_instance()

