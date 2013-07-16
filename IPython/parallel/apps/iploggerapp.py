#!/usr/bin/env python
# encoding: utf-8
"""
A simple IPython logger application

Authors:

* MinRK

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

from IPython.core.profiledir import ProfileDir
from IPython.utils.traitlets import Bool, Dict, Unicode

from IPython.parallel.apps.baseapp import (
    BaseParallelApplication,
    base_aliases,
    catch_config_error,
)
from IPython.parallel.apps.logwatcher import LogWatcher

#-----------------------------------------------------------------------------
# Module level variables
#-----------------------------------------------------------------------------

#: The default config file name for this application
_description = """Start an IPython logger for parallel computing.

IPython controllers and engines (and your own processes) can broadcast log messages
by registering a `zmq.log.handlers.PUBHandler` with the `logging` module. The
logger can be configured using command line options or using a cluster
directory. Cluster directories contain config, log and security files and are
usually located in your ipython directory and named as "profile_name".
See the `profile` and `profile-dir` options for details.
"""


#-----------------------------------------------------------------------------
# Main application
#-----------------------------------------------------------------------------
aliases = {}
aliases.update(base_aliases)
aliases.update(dict(url='LogWatcher.url', topics='LogWatcher.topics'))

class IPLoggerApp(BaseParallelApplication):

    name = u'iplogger'
    description = _description
    classes = [LogWatcher, ProfileDir]
    aliases = Dict(aliases)

    @catch_config_error
    def initialize(self, argv=None):
        super(IPLoggerApp, self).initialize(argv)
        self.init_watcher()
    
    def init_watcher(self):
        try:
            self.watcher = LogWatcher(parent=self, log=self.log)
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


launch_new_instance = IPLoggerApp.launch_instance


if __name__ == '__main__':
    launch_new_instance()

