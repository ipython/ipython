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

import logging
import os
import signal

if os.name=='posix':
    from twisted.scripts._twistd_unix import daemonize

from twisted.internet import reactor, defer
from twisted.python import log, failure


from IPython.external.argparse import ArgumentParser, SUPPRESS
from IPython.utils.importstring import import_item
from IPython.kernel.clusterdir import (
    ApplicationWithClusterDir, ClusterDirConfigLoader,
    ClusterDirError, PIDFileError
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
local host simply do 'ipcluster start -n 4'. For more complex usage 
you will typically do 'ipcluster create -p mycluster', then edit
configuration files, followed by 'ipcluster start -p mycluster -n 4'.
"""


# Exit codes for ipcluster

# This will be the exit code if the ipcluster appears to be running because
# a .pid file exists
ALREADY_STARTED = 10


# This will be the exit code if ipcluster stop is run, but there is not .pid
# file to be found.
ALREADY_STOPPED = 11


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
            running ipcluster is 'ipcluster <cmd> [options]'. To get help
            on a particular subcommand do 'ipcluster <cmd> -h'."""
            # help="For more help, type 'ipcluster <cmd> -h'",
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
            'cluster_<profile>'."""
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
            using the convention 'cluster_<profile>'. By default they are
            located in your ipython directory. Once created, you will
            probably need to edit the configuration files in the cluster
            directory to configure your cluster. Most users will create a
            cluster directory by profile name, 
            'ipcluster create -p mycluster', which will put the directory
            in '<ipython_dir>/cluster_mycluster'. 
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
            'cluster_<profile>' and should be creating using the 'start'
            subcommand of 'ipcluster'. If your cluster directory is in 
            the cwd or the ipython directory, you can simply refer to it
            using its profile name, 'ipcluster start -n 4 -p <profile>`,
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

        # The "stop" subcommand parser
        parser_stop = subparsers.add_parser(
            'stop',
            parents=[parent_parser1, parent_parser2],
            argument_default=SUPPRESS,
            help="Stop a running cluster.",
            description=
            """Stop a running ipython cluster by its profile name or cluster 
            directory. Cluster directories are named using the convention
            'cluster_<profile>'. If your cluster directory is in 
            the cwd or the ipython directory, you can simply refer to it
            using its profile name, 'ipcluster stop -p <profile>`, otherwise
            use the '--cluster-dir' option.
            """
        )
        paa = parser_stop.add_argument
        paa('--signal',
            dest='Global.signal', type=int,
            help="The signal number to use in stopping the cluster (default=2).",
            metavar="Global.signal")


#-----------------------------------------------------------------------------
# Main application
#-----------------------------------------------------------------------------


class IPClusterApp(ApplicationWithClusterDir):

    name = u'ipcluster'
    description = _description
    usage = None
    command_line_loader = IPClusterAppConfigLoader
    default_config_file_name = default_config_file_name
    default_log_level = logging.INFO
    auto_create_cluster_dir = False

    def create_default_config(self):
        super(IPClusterApp, self).create_default_config()
        self.default_config.Global.controller_launcher = \
            'IPython.kernel.launcher.LocalControllerLauncher'
        self.default_config.Global.engine_launcher = \
            'IPython.kernel.launcher.LocalEngineSetLauncher'
        self.default_config.Global.n = 2
        self.default_config.Global.reset_config = False
        self.default_config.Global.clean_logs = True
        self.default_config.Global.signal = 2
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
                if os.path.isdir(full_path) and f.startswith('cluster_'):
                    profile = full_path.split('_')[-1]
                    start_cmd = 'ipcluster start -p %s -n 4' % profile
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
            reactor.callWhenRunning(self.start_launchers)

    def start_launchers(self):
        config = self.master_config

        # Create the launchers. In both bases, we set the work_dir of
        # the launcher to the cluster_dir. This is where the launcher's
        # subprocesses will be launched. It is not where the controller
        # and engine will be launched.
        el_class = import_item(config.Global.engine_launcher)
        self.engine_launcher = el_class(
            work_dir=self.cluster_dir, config=config
        )
        cl_class = import_item(config.Global.controller_launcher)
        self.controller_launcher = cl_class(
            work_dir=self.cluster_dir, config=config
        )

        # Setup signals
        signal.signal(signal.SIGINT, self.sigint_handler)

        # Setup the observing of stopping. If the controller dies, shut
        # everything down as that will be completely fatal for the engines.
        d1 = self.controller_launcher.observe_stop()
        d1.addCallback(self.stop_launchers)
        # But, we don't monitor the stopping of engines. An engine dying
        # is just fine and in principle a user could start a new engine.
        # Also, if we did monitor engine stopping, it is difficult to
        # know what to do when only some engines die. Currently, the
        # observing of engine stopping is inconsistent. Some launchers
        # might trigger on a single engine stopping, other wait until
        # all stop.  TODO: think more about how to handle this.
        
        # Start the controller and engines
        self._stopping = False  # Make sure stop_launchers is not called 2x.
        d = self.start_controller()
        d.addCallback(self.start_engines)
        d.addCallback(self.startup_message)
        # If the controller or engines fail to start, stop everything
        d.addErrback(self.stop_launchers)
        return d

    def startup_message(self, r=None):
        log.msg("IPython cluster: started")
        return r
        
    def start_controller(self, r=None):
        # log.msg("In start_controller")
        config = self.master_config
        d = self.controller_launcher.start(
            cluster_dir=config.Global.cluster_dir
        )
        return d
            
    def start_engines(self, r=None):
        # log.msg("In start_engines")
        config = self.master_config
        d = self.engine_launcher.start(
            config.Global.n,
            cluster_dir=config.Global.cluster_dir
        )
        return d

    def stop_controller(self, r=None):
        # log.msg("In stop_controller")
        if self.controller_launcher.running:
            d = self.controller_launcher.stop()
            d.addErrback(self.log_err)
            return d
        else:
            return defer.succeed(None)

    def stop_engines(self, r=None):
        # log.msg("In stop_engines")
        if self.engine_launcher.running:
            d = self.engine_launcher.stop()
            d.addErrback(self.log_err)
            return d
        else:
            return defer.succeed(None)

    def log_err(self, f):
        log.msg(f.getTraceback())
        return None
        
    def stop_launchers(self, r=None):
        if not self._stopping:
            self._stopping = True
            if isinstance(r, failure.Failure):
                log.msg('Unexpected error in ipcluster:')
                log.msg(r.getTraceback())
            log.msg("IPython cluster: stopping")
            # These return deferreds. We are not doing anything with them
            # but we are holding refs to them as a reminder that they 
            # do return deferreds.
            d1 = self.stop_engines()
            d2 = self.stop_controller()
            # Wait a few seconds to let things shut down.
            reactor.callLater(4.0, reactor.stop)

    def sigint_handler(self, signum, frame):
        self.stop_launchers()
        
    def start_logging(self):
        # Remove old log files of the controller and engine
        if self.master_config.Global.clean_logs:
            log_dir = self.master_config.Global.log_dir
            for f in os.listdir(log_dir):
                if f.startswith('ipengine' + '-'):
                    if f.endswith('.log') or f.endswith('.out') or f.endswith('.err'):
                        os.remove(os.path.join(log_dir, f))
                if f.startswith('ipcontroller' + '-'):
                    if f.endswith('.log') or f.endswith('.out') or f.endswith('.err'):
                        os.remove(os.path.join(log_dir, f))
        # This will remote old log files for ipcluster itself
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
                'use "ipcluster stop" to stop the cluster.' % pid
            )
            # Here I exit with a unusual exit status that other processes
            # can watch for to learn how I existed.
            self.exit(ALREADY_STARTED)

        # Now log and daemonize
        self.log.info(
            'Starting ipcluster with [daemon=%r]' % config.Global.daemonize
        )
        # TODO: Get daemonize working on Windows or as a Windows Server.
        if config.Global.daemonize:
            if os.name=='posix':
                daemonize()

        # Now write the new pid file AFTER our new forked pid is active.
        self.write_pid_file()
        reactor.addSystemEventTrigger('during','shutdown', self.remove_pid_file)
        reactor.run()

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

