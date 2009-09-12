#!/usr/bin/env python
# encoding: utf-8
"""
An application for IPython

Authors:

* Brian Granger
* Fernando Perez

Notes
-----
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

import os
import sys
import traceback
from copy import deepcopy

from IPython.utils.genutils import get_ipython_dir, filefind
from IPython.config.loader import (
    PyFileConfigLoader,
    ArgParseConfigLoader,
    Config,
    NoConfigDefault
)

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------


class IPythonArgParseConfigLoader(ArgParseConfigLoader):
    """Default command line options for IPython based applications."""

    def _add_other_arguments(self):
        self.parser.add_argument('-ipythondir',dest='Global.ipythondir',type=str,
            help='Set to override default location of Global.ipythondir.',
            default=NoConfigDefault,
            metavar='Global.ipythondir')
        self.parser.add_argument('-p','-profile',dest='Global.profile',type=str,
            help='The string name of the ipython profile to be used.',
            default=NoConfigDefault,
            metavar='Global.profile')
        self.parser.add_argument('-debug',dest="Global.debug",action='store_true',
            help='Debug the application startup process.',
            default=NoConfigDefault)
        self.parser.add_argument('-config_file',dest='Global.config_file',type=str,
            help='Set the config file name to override default.',
            default=NoConfigDefault,
            metavar='Global.config_file')


class ApplicationError(Exception):
    pass


class Application(object):
    """Load a config, construct an app and run it.
    """

    config_file_name = 'ipython_config.py'
    name = 'ipython'
    debug = False

    def __init__(self):
        pass

    def start(self):
        """Start the application."""
        self.attempt(self.create_default_config)
        self.attempt(self.pre_load_command_line_config)
        self.attempt(self.load_command_line_config, action='abort')
        self.attempt(self.post_load_command_line_config)
        self.attempt(self.find_ipythondir)
        self.attempt(self.find_config_file_name)
        self.attempt(self.find_config_file_paths)
        self.attempt(self.pre_load_file_config)
        self.attempt(self.load_file_config)
        self.attempt(self.post_load_file_config)
        self.attempt(self.merge_configs)
        self.attempt(self.pre_construct)
        self.attempt(self.construct)
        self.attempt(self.post_construct)
        self.attempt(self.start_app)

    #-------------------------------------------------------------------------
    # Various stages of Application creation
    #-------------------------------------------------------------------------

    def create_default_config(self):
        """Create defaults that can't be set elsewhere."""
        self.default_config = Config()
        self.default_config.Global.ipythondir = get_ipython_dir()

    def create_command_line_config(self):
        """Create and return a command line config loader."""
        return IPythonArgParseConfigLoader(description=self.name)

    def pre_load_command_line_config(self):
        """Do actions just before loading the command line config."""
        pass

    def load_command_line_config(self):
        """Load the command line config.

        This method also sets ``self.debug``.
        """

        loader = self.create_command_line_config()
        self.command_line_config = loader.load_config()
        try:
            self.debug = self.command_line_config.Global.debug
        except AttributeError:
            pass # use class default
        self.log("Default config loaded:", self.default_config)
        self.log("Command line config loaded:", self.command_line_config)

    def post_load_command_line_config(self):
        """Do actions just after loading the command line config."""
        pass

    def find_ipythondir(self):
        """Set the IPython directory.

        This sets ``self.ipythondir``, but the actual value that is passed
        to the application is kept in either ``self.default_config`` or
        ``self.command_line_config``.  This also added ``self.ipythondir`` to
        ``sys.path`` so config files there can be references by other config
        files.
        """

        try:
            self.ipythondir = self.command_line_config.Global.ipythondir
        except AttributeError:
            self.ipythondir = self.default_config.Global.ipythondir
        sys.path.append(os.path.abspath(self.ipythondir))
        if not os.path.isdir(self.ipythondir):
            os.makedirs(self.ipythondir, mode = 0777)
        self.log("IPYTHONDIR set to: %s" % self.ipythondir)

    def find_config_file_name(self):
        """Find the config file name for this application.

        If a profile has been set at the command line, this will resolve
        it.  The search paths for the config file are set in
        :meth:`find_config_file_paths` and then passed to the config file
        loader where they are resolved to an absolute path.
        """

        try:
            self.config_file_name = self.command_line_config.Global.config_file
        except AttributeError:
            pass

        try:
            self.profile_name = self.command_line_config.Global.profile
            name_parts = self.config_file_name.split('.')
            name_parts.insert(1, '_' + self.profile_name + '.')
            self.config_file_name = ''.join(name_parts)
        except AttributeError:
            pass

    def find_config_file_paths(self):
        """Set the search paths for resolving the config file."""
        self.config_file_paths = (os.getcwd(), self.ipythondir)

    def pre_load_file_config(self):
        """Do actions before the config file is loaded."""
        pass

    def load_file_config(self):
        """Load the config file.
        
        This tries to load the config file from disk.  If successful, the
        ``CONFIG_FILE`` config variable is set to the resolved config file
        location.  If not successful, an empty config is used.
        """
        loader = PyFileConfigLoader(self.config_file_name,
                                    path=self.config_file_paths)
        try:
            self.file_config = loader.load_config()
            self.file_config.Global.config_file = loader.full_filename
        except IOError:
            self.log("Config file not found, skipping: %s" % \
                     self.config_file_name)
            self.file_config = Config()
        else:
            self.log("Config file loaded: %s" % loader.full_filename,
                     self.file_config)

    def post_load_file_config(self):
        """Do actions after the config file is loaded."""
        pass

    def merge_configs(self):
        """Merge the default, command line and file config objects."""
        config = Config()
        config._merge(self.default_config)
        config._merge(self.file_config)
        config._merge(self.command_line_config)
        self.master_config = config
        self.log("Master config created:", self.master_config)

    def pre_construct(self):
        """Do actions after the config has been built, but before construct."""
        pass

    def construct(self):
        """Construct the main components that make up this app."""
        self.log("Constructing components for application...")

    def post_construct(self):
        """Do actions after construct, but before starting the app."""
        pass

    def start_app(self):
        """Actually start the app."""
        self.log("Starting application...")

    #-------------------------------------------------------------------------
    # Utility methods
    #-------------------------------------------------------------------------

    def abort(self):
        """Abort the starting of the application."""
        print "Aborting application: ", self.name
        sys.exit(1)

    def exit(self):
        print "Exiting application: ", self.name
        sys.exit(1)

    def attempt(self, func, action='abort'):
        try:
            func()
        except SystemExit:
            self.exit()
        except:
            if action == 'abort':
                self.print_traceback()
                self.abort()
            elif action == 'exit':
                self.exit()

    def print_traceback(self):
        print "Error in appliction startup: ", self.name
        print
        traceback.print_exc()

    def log(self, *args):
        if self.debug:
            for arg in args:
                print "[%s] %s" % (self.name, arg)        