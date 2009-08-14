#!/usr/bin/env python
# encoding: utf-8
"""
An application for IPython

Authors:

* Brian Granger
* Fernando Perez

Notes
-----

The following directories are relevant in the startup of an app:

* The ipythondir.  This has a default, but can be set by IPYTHONDIR or at
  the command line.
* The current working directory.
* Another runtime directory.  With some applications (engine, controller) we
  need the ability to have different cluster configs.  Each of these needs
  to have its own config, security dir and log dir.  We could simply treat
  these as regular ipython dirs.  

There are number of ways in which these directories are used:

* For config files.
* For other assets and resources needed to run.  These include 
  plugins, magics, furls files.
* For writing various things created at runtime like logs, furl files, etc.

Questions:


* Can we limit ourselves to 1 config file or do we want to have a sequence
  of them like IPYTHONDIR->RUNTIMEDIR->CWD? [1]
* Do we need a debug mode that has custom exception handling and can drop
  into pdb upno startup? N
* Do we need to use an OutputTrap to capture output and then present it
  to a user if startup fails? N
* Do we want the location of the config file(s) to be independent of the
  ipython/runtime dir or coupled to it.  In other words, can the user select
  a config file that is outside their runtime/ipython dir.  One model is 
  that we could have a very strict model of IPYTHONDIR=runtimed dir=
  dir used for all config.
* Do we install default config files or not? N

* attempt needs to either clash or to die
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

import sys
from copy import deepcopy
from IPython.utils.ipstruct import Struct

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------


class ApplicationError(Exception):
    pass


class Application(object):

    runtime_dirs = []
    default_config = Struct()
    runtime_dir = ''
    config_file = ''
    name = ''

    def __init__(self):
        pass

    def start(self):
        """Start the application."""
        self.attempt(self.create_command_line_config)
        self.attempt(self.find_runtime_dirs)
        self.attempt(self.create_runtime_dirs)
        self.attempt(self.find_config_files)
        self.attempt(self.create_file_configs)
        self.attempt(self.merge_configs)
        self.attempt(self.construct)
        self.attempt(self.start_logging)
        self.attempt(self.start_app)

    #-------------------------------------------------------------------------
    # Various stages of Application creation
    #-------------------------------------------------------------------------

    def create_command_line_config(self):
        """Read the command line args and return its config object."""
        self.command_line_config = Struct()

    def find_runtime_dirs(self):
        """Find the runtime directory for this application.

        This should set self.runtime_dir.
        """
        pass

    def create_runtime_dirs(self):
        """Create the runtime dirs if they don't exist."""
        pass

    def find_config_files(self):
        """Find the config file for this application."""
        pass

    def create_file_configs(self):
        self.file_configs = [Struct()]

    def merge_configs(self):
        config = Struct()
        all_configs = self.file_configs + self.command_line_config
        for c in all_configs:
            config.update(c)
        self.master_config = config

    def construct(self, config):
        """Construct the main components that make up this app."""
        pass

    def start_logging(self):
        """Start logging, if needed, at the last possible moment."""
        pass

    def start_app(self):
        """Actually start the app."""
        pass

    #-------------------------------------------------------------------------
    # Utility methods
    #-------------------------------------------------------------------------

    def abort(self):
        """Abort the starting of the application."""
        print "Aborting application: ", self.name
        sys.exit(1)

    def attempt(self, func):
        try:
            func()
        except:
            self.handle_error()
            self.abort()

    def handle_error(self):
        print "I am dying!"
     
        