#!/usr/bin/env python
# encoding: utf-8
"""
A simple IPython logger application
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import sys

import zmq

from IPython.zmq.parallel.clusterdir import (
    ApplicationWithClusterDir,
    ClusterDirConfigLoader
)
from IPython.zmq.parallel.logwatcher import LogWatcher

#-----------------------------------------------------------------------------
# Module level variables
#-----------------------------------------------------------------------------

#: The default config file name for this application
default_config_file_name = u'iplogger_config.py'

_description = """Start an IPython logger for parallel computing.\n\n

IPython controllers and engines (and your own processes) can broadcast log messages
by registering a `zmq.log.handlers.PUBHandler` with the `logging` module. The
logger can be configured using command line options or using a cluster
directory. Cluster directories contain config, log and security files and are
usually located in your ipython directory and named as "cluster_<profile>".
See the --profile and --cluster-dir options for details.
"""

#-----------------------------------------------------------------------------
# Command line options
#-----------------------------------------------------------------------------


class IPLoggerAppConfigLoader(ClusterDirConfigLoader):

    def _add_arguments(self):
        super(IPLoggerAppConfigLoader, self)._add_arguments()
        paa = self.parser.add_argument
        # Controller config
        paa('--url',
            type=str, dest='LogWatcher.url',
            help='The url the LogWatcher will listen on',
            )
        # MPI
        paa('--topics',
            type=str, dest='LogWatcher.topics', nargs='+',
            help='What topics to subscribe to',
            metavar='topics')
        # Global config
        paa('--log-to-file',
            action='store_true', dest='Global.log_to_file',
            help='Log to a file in the log directory (default is stdout)')
        

#-----------------------------------------------------------------------------
# Main application
#-----------------------------------------------------------------------------


class IPLoggerApp(ApplicationWithClusterDir):

    name = u'iploggerz'
    description = _description
    command_line_loader = IPLoggerAppConfigLoader
    default_config_file_name = default_config_file_name
    auto_create_cluster_dir = True

    def create_default_config(self):
        super(IPLoggerApp, self).create_default_config()

        # The engine should not clean logs as we don't want to remove the
        # active log files of other running engines.
        self.default_config.Global.clean_logs = False

        # If given, this is the actual location of the logger's URL file.
        # If not, this is computed using the profile, app_dir and furl_file_name
        self.default_config.Global.url_file_name = u'iplogger.url'
        self.default_config.Global.url_file = u''

    def post_load_command_line_config(self):
        pass

    def pre_construct(self):
        super(IPLoggerApp, self).pre_construct()

    def construct(self):
        # This is the working dir by now.
        sys.path.insert(0, '')

        self.start_logging()

        try:
            self.watcher = LogWatcher(config=self.master_config, logname=self.log.name)
        except:
            self.log.error("Couldn't start the LogWatcher", exc_info=True)
            self.exit(1)
        

    def start_app(self):
        try:
            self.watcher.start()
            self.watcher.loop.start()
        except KeyboardInterrupt:
            self.log.critical("Logging Interrupted, shutting down...\n")


def launch_new_instance():
    """Create and run the IPython LogWatcher"""
    app = IPLoggerApp()
    app.start()


if __name__ == '__main__':
    launch_new_instance()

