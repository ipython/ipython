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

1. Can we limit ourselves to 1 config file or do we want to have a sequence
   of them like IPYTHONDIR->RUNTIMEDIR->CWD?
2. Do we need a debug mode that has custom exception handling and can drop
   into pdb upno startup?
3. Do we need to use an OutputTrap to capture output and then present it
   to a user if startup fails?
4. Do we want the location of the config file(s) to be independent of the
   ipython/runtime dir or coupled to it.  In other words, can the user select
   a config file that is outside their runtime/ipython dir.  One model is 
   that we could have a very strict model of IPYTHONDIR=runtimed dir=
   dir used for all config.
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

    def find_runtime_dir(self):
        """Find the runtime directory for this application.

        This should set self.runtime_dir.
        """
        pass

    def create_runtime_dirs(self):
        """Create the runtime dirs if they dont exist."""
        pass

    def find_config_file(self):
        """Find the config file for this application."""
        pass

    def create_config(self):
        self.config = deepcopy(self.default_config)

        self.pre_file_config()
        self.file_config = self.create_file_config()
        self.post_file_config()

        self.pre_command_line_config()
        self.command_line_config = create_command_line_config()
        self.post_command_line_config()

        master_config = self.merge_configs(config, file_config, cl_config)
        self.master_config = master_config
        return master_config

    def pre_file_config(self):
        pass

    def create_file_config(self):
        """Read the config file and return its config object."""
        return Struct()

    def post_file_config(self):
        pass

    def pre_command_line_config(self):
        pass

    def create_command_line_config(self):
        """Read the command line args and return its config object."""
        return Struct()

    def post_command_line_config(self):
        pass

    def merge_configs(self, config, file_config, cl_config):
        config.update(file_config)
        config.update(cl_config)
        return config

    def start(self):
        """Start the application."""
        self.attempt(self.find_runtime_dir)
        self.attempt(self.find_runtime_dir)
        self.attempt(self.create_runtime_dirs)
        self.attempt(self.find_config_file)
        self.attempt(self.create_config)
        self.attempt(self.construct)
        self.attempt(self.start_logging)
        self.attempt(self.start_app)

    def construct(self, config):
        """Construct the main components that make up this app."""
        pass

    def start_logging(self):
        """Start logging, if needed, at the last possible moment."""
        pass

    def start_app(self):
        """Actually start the app."""
        pass

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
     
        