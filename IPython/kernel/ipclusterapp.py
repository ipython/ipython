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
import sys

if os.name=='posix':
    from twisted.scripts._twistd_unix import daemonize

from IPython.core import release
from IPython.external import argparse
from IPython.config.loader import ArgParseConfigLoader, NoConfigDefault
from IPython.utils.importstring import import_item

from IPython.kernel.clusterdir import (
    ApplicationWithClusterDir, ClusterDirError, PIDFileError
)

from twisted.internet import reactor
from twisted.python import log


#-----------------------------------------------------------------------------
# The ipcluster application
#-----------------------------------------------------------------------------


# Exit codes for ipcluster

# This will be the exit code if the ipcluster appears to be running because
# a .pid file exists
ALREADY_STARTED = 10

# This will be the exit code if ipcluster stop is run, but there is not .pid
# file to be found.
ALREADY_STOPPED = 11


class IPClusterCLLoader(ArgParseConfigLoader):

    def _add_arguments(self):
        # This has all the common options that all subcommands use
        parent_parser1 = argparse.ArgumentParser(add_help=False)
        parent_parser1.add_argument('--ipython-dir', 
            dest='Global.ipython_dir',type=unicode,
            help='Set to override default location of Global.ipython_dir.',
            default=NoConfigDefault,
            metavar='Global.ipython_dir')
        parent_parser1.add_argument('--log-level',
            dest="Global.log_level",type=int,
            help='Set the log level (0,10,20,30,40,50).  Default is 30.',
            default=NoConfigDefault,
            metavar='Global.log_level')

        # This has all the common options that other subcommands use
        parent_parser2 = argparse.ArgumentParser(add_help=False)
        parent_parser2.add_argument('-p','--profile',
            dest='Global.profile',type=unicode,
            default=NoConfigDefault,
            help='The string name of the profile to be used. This determines '
            'the name of the cluster dir as: cluster_<profile>. The default profile '
            'is named "default".  The cluster directory is resolve this way '
            'if the --cluster-dir option is not used.',
            default=NoConfigDefault,
            metavar='Global.profile')
        parent_parser2.add_argument('--cluster-dir',
            dest='Global.cluster_dir',type=unicode,
            default=NoConfigDefault,
            help='Set the cluster dir. This overrides the logic used by the '
            '--profile option.',
            default=NoConfigDefault,
            metavar='Global.cluster_dir'),
        parent_parser2.add_argument('--working-dir',
            dest='Global.working_dir',type=unicode,
            help='Set the working dir for the process.',
            default=NoConfigDefault,
            metavar='Global.working_dir')
        parent_parser2.add_argument('--log-to-file',
            action='store_true', dest='Global.log_to_file', 
            default=NoConfigDefault,
            help='Log to a file in the log directory (default is stdout)'
        )

        subparsers = self.parser.add_subparsers(
            dest='Global.subcommand',
            title='ipcluster subcommands',
            description='ipcluster has a variety of subcommands. '
            'The general way of running ipcluster is "ipcluster <cmd> '
            ' [options]""',
            help='For more help, type "ipcluster <cmd> -h"')

        parser_list = subparsers.add_parser(
            'list',
            help='List all clusters in cwd and ipython_dir.',
            parents=[parent_parser1]
        )

        parser_create = subparsers.add_parser(
            'create',
            help='Create a new cluster directory.',
            parents=[parent_parser1, parent_parser2] 
        )
        parser_create.add_argument(
            '--reset-config',
            dest='Global.reset_config', action='store_true',
            default=NoConfigDefault,
            help='Recopy the default config files to the cluster directory. '
            'You will loose any modifications you have made to these files.'
        )

        parser_start = subparsers.add_parser(
            'start',
            help='Start a cluster.',
            parents=[parent_parser1, parent_parser2]
        )
        parser_start.add_argument(
            '-n', '--number',
            type=int, dest='Global.n',
            default=NoConfigDefault,
            help='The number of engines to start.',
            metavar='Global.n'
        )
        parser_start.add_argument('--clean-logs',
            dest='Global.clean_logs', action='store_true',
            help='Delete old log flies before starting.',
            default=NoConfigDefault
        )
        parser_start.add_argument('--no-clean-logs',
            dest='Global.clean_logs', action='store_false',
            help="Don't delete old log flies before starting.",
            default=NoConfigDefault
        )
        parser_start.add_argument('--daemon',
            dest='Global.daemonize', action='store_true',
            help='Daemonize the ipcluster program. This implies --log-to-file',
            default=NoConfigDefault
        )
        parser_start.add_argument('--no-daemon',
            dest='Global.daemonize', action='store_false',
            help="Dont't daemonize the ipcluster program.",
            default=NoConfigDefault
        )

        parser_start = subparsers.add_parser(
            'stop',
            help='Stop a cluster.',
            parents=[parent_parser1, parent_parser2]
        )
        parser_start.add_argument('--signal',
            dest='Global.signal', type=int,
            help="The signal number to use in stopping the cluster (default=2).",
            metavar="Global.signal",
            default=NoConfigDefault
        )


default_config_file_name = u'ipcluster_config.py'


class IPClusterApp(ApplicationWithClusterDir):

    name = u'ipcluster'
    description = 'Start an IPython cluster (controller and engines).'
    config_file_name = default_config_file_name
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

    def create_command_line_config(self):
        """Create and return a command line config loader."""
        return IPClusterCLLoader(
            description=self.description, 
            version=release.version
        )

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
            self.auto_create_cluster_dir = False
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
                    start_cmd = '"ipcluster start -n 4 -p %s"' % profile
                    print start_cmd + " ==> " + full_path

    def pre_construct(self):
        # This is where we cd to the working directory.
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
        if config.Global.subcommand=='list':
            pass
        elif config.Global.subcommand=='create':
            self.log.info('Copying default config files to cluster directory '
            '[overwrite=%r]' % (config.Global.reset_config,))
            self.cluster_dir_obj.copy_all_config_files(overwrite=config.Global.reset_config)
        elif config.Global.subcommand=='start':
            self.start_logging()
            reactor.callWhenRunning(self.start_launchers)

    def start_launchers(self):
        config = self.master_config

        # Create the launchers
        el_class = import_item(config.Global.engine_launcher)
        self.engine_launcher = el_class(
            self.cluster_dir, config=config
        )
        cl_class = import_item(config.Global.controller_launcher)
        self.controller_launcher = cl_class(
            self.cluster_dir, config=config
        )

        # Setup signals
        signal.signal(signal.SIGINT, self.stop_launchers)

        # Setup the observing of stopping
        d1 = self.controller_launcher.observe_stop()
        d1.addCallback(self.stop_engines)
        d1.addErrback(self.err_and_stop)
        # If this triggers, just let them die
        # d2 = self.engine_launcher.observe_stop()
        
        # Start the controller and engines
        d = self.controller_launcher.start(
            profile=None, cluster_dir=config.Global.cluster_dir
        )
        d.addCallback(lambda _: self.start_engines())
        d.addErrback(self.err_and_stop)

    def err_and_stop(self, f):
        log.msg('Unexpected error in ipcluster:')
        log.err(f)
        reactor.stop()

    def stop_engines(self, r):
        return self.engine_launcher.stop()

    def start_engines(self):
        config = self.master_config
        d = self.engine_launcher.start(
            config.Global.n,
            profile=None, cluster_dir=config.Global.cluster_dir
        )
        return d

    def stop_launchers(self, signum, frame):
        log.msg("Stopping cluster")
        d1 = self.engine_launcher.stop()
        d2 = self.controller_launcher.stop()
        # d1.addCallback(lambda _: self.controller_launcher.stop)
        d1.addErrback(self.err_and_stop)
        d2.addErrback(self.err_and_stop)
        reactor.callLater(2.0, reactor.stop)

    def start_logging(self):
        # Remove old log files
        if self.master_config.Global.clean_logs:
            log_dir = self.master_config.Global.log_dir
            for f in os.listdir(log_dir):
                if f.startswith('ipengine' + '-') and f.endswith('.log'):
                    os.remove(os.path.join(log_dir, f))
            for f in os.listdir(log_dir):
                if f.startswith('ipcontroller' + '-') and f.endswith('.log'):
                    os.remove(os.path.join(log_dir, f))
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
        sig = config.Global.signal
        self.log.info(
            "Stopping cluster [pid=%r] with [signal=%r]" % (pid, sig)
        )
        os.kill(pid, sig)


def launch_new_instance():
    """Create and run the IPython cluster."""
    app = IPClusterApp()
    app.start()


if __name__ == '__main__':
    launch_new_instance()

