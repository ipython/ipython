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

import logging
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
        self.parser.add_argument('-log_level',dest="Global.log_level",type=int,
            help='Set the log level (0,10,20,30,40,50).  Default is 30.',
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

    def __init__(self):
        self.init_logger()
        self.default_config_file_name = self.config_file_name

    def init_logger(self):
        self.log = logging.getLogger(self.__class__.__name__)
        # This is used as the default until the command line arguments are read.
        self.log.setLevel(logging.WARN)
        self._log_handler = logging.StreamHandler()
        self._log_formatter = logging.Formatter("[%(name)s] %(message)s")
        self._log_handler.setFormatter(self._log_formatter)
        self.log.addHandler(self._log_handler)

    def _set_log_level(self, level):
        self.log.setLevel(level)

    def _get_log_level(self):
        return self.log.level

    log_level = property(_get_log_level, _set_log_level)

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
        """Create defaults that can't be set elsewhere.

        For the most part, we try to set default in the class attributes
        of Components.  But, defaults the top-level Application (which is
        not a HasTraitlets or Component) are not set in this way.  Instead
        we set them here.  The Global section is for variables like this that
        don't belong to a particular component.
        """
        self.default_config = Config()
        self.default_config.Global.ipythondir = get_ipython_dir()
        self.log.debug('Default config loaded:')
        self.log.debug(repr(self.default_config))

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
        self.extra_args = loader.get_extra_args()

        try:
            self.log_level = self.command_line_config.Global.log_level
        except AttributeError:
            pass # Use existing value which is set in Application.init_logger.

        self.log.debug("Command line config loaded:")
        self.log.debug(repr(self.command_line_config))

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
        self.log.debug("IPYTHONDIR set to: %s" % self.ipythondir)

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
        self.log.debug("Attempting to load config file: <%s>" % self.config_file_name)
        loader = PyFileConfigLoader(self.config_file_name,
                                    path=self.config_file_paths)
        try:
            self.file_config = loader.load_config()
            self.file_config.Global.config_file = loader.full_filename
        except IOError:
            # Only warn if the default config file was NOT being used.
            if not self.config_file_name==self.default_config_file_name:
                self.log.warn("Config file not found, skipping: <%s>" % \
                               self.config_file_name, exc_info=True)
            self.file_config = Config()
        except:
            self.log.warn("Error loading config file: <%s>" % \
                           self.config_file_name, exc_info=True)
            self.file_config = Config()
        else:
            self.log.debug("Config file loaded: <%s>" % loader.full_filename)
            self.log.debug(repr(self.file_config))
        # We need to keeep self.log_level updated.
        try:
            self.log_level = self.file_config.Global.log_level
        except AttributeError:
            pass # Use existing value

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
        self.log.debug("Master config created:")
        self.log.debug(repr(self.master_config))

    def pre_construct(self):
        """Do actions after the config has been built, but before construct."""
        pass

    def construct(self):
        """Construct the main components that make up this app."""
        self.log.debug("Constructing components for application")

    def post_construct(self):
        """Do actions after construct, but before starting the app."""
        pass

    def start_app(self):
        """Actually start the app."""
        self.log.debug("Starting application")

    #-------------------------------------------------------------------------
    # Utility methods
    #-------------------------------------------------------------------------

    def abort(self):
        """Abort the starting of the application."""
        self.log.critical("Aborting application: %s" % self.name, exc_info=True)
        sys.exit(1)

    def exit(self):
        self.log.critical("Aborting application: %s" % self.name)
        sys.exit(1)

    def attempt(self, func, action='abort'):
        try:
            func()
        except SystemExit:
            self.exit()
        except:
            if action == 'abort':
                self.abort()
            elif action == 'exit':
                self.exit()
      