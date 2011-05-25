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

from IPython.utils.traitlets import Bool, Dict, Unicode

from IPython.parallel.apps.clusterdir import (
    ClusterApplication,
    ClusterDir,
    base_aliases
)
from IPython.parallel.apps.logwatcher import LogWatcher

#-----------------------------------------------------------------------------
# Module level variables
#-----------------------------------------------------------------------------

#: The default config file name for this application
default_config_file_name = u'iplogger_config.py'

_description = """Start an IPython logger for parallel computing.

IPython controllers and engines (and your own processes) can broadcast log messages
by registering a `zmq.log.handlers.PUBHandler` with the `logging` module. The
logger can be configured using command line options or using a cluster
directory. Cluster directories contain config, log and security files and are
usually located in your ipython directory and named as "cluster_<profile>".
See the `profile` and `cluster_dir` options for details.
"""


#-----------------------------------------------------------------------------
# Main application
#-----------------------------------------------------------------------------
aliases = {}
aliases.update(base_aliases)
aliases.update(dict(url='LogWatcher.url', topics='LogWatcher.topics'))

class IPLoggerApp(ClusterApplication):

    name = u'iploggerz'
    description = _description
    config_file_name = Unicode(default_config_file_name)
    auto_create_cluster_dir = Bool(False)
    
    classes = [LogWatcher, ClusterDir]
    aliases = Dict(aliases)

    def initialize(self, argv=None):
        super(IPLoggerApp, self).initialize(argv)
        self.init_watcher()
    
    def init_watcher(self):
        try:
            self.watcher = LogWatcher(config=self.config, logname=self.log.name)
        except:
            self.log.error("Couldn't start the LogWatcher", exc_info=True)
            self.exit(1)
        self.log.info("Listening for log messages on %r"%self.watcher.url)
        

    def start(self):
        self.watcher.start()
        try:
            self.watcher.loop.start()
        except KeyboardInterrupt:
            self.log.critical("Logging Interrupted, shutting down...\n")


def launch_new_instance():
    """Create and run the IPython LogWatcher"""
    app = IPLoggerApp()
    app.initialize()
    app.start()


if __name__ == '__main__':
    launch_new_instance()

