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

from IPython.core import release
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


class BaseAppArgParseConfigLoader(ArgParseConfigLoader):
    """Default command line options for IPython based applications."""

    def _add_other_arguments(self):
        self.parser.add_argument('-ipythondir', '--ipython-dir', 
            dest='Global.ipythondir',type=str,
            help='Set to override default location of Global.ipythondir.',
            default=NoConfigDefault,
            metavar='Global.ipythondir')
        self.parser.add_argument('-p','-profile', '--profile',
            dest='Global.profile',type=str,
            help='The string name of the ipython profile to be used.',
            default=NoConfigDefault,
            metavar='Global.profile')
        self.parser.add_argument('-log_level', '--log-level',
            dest="Global.log_level",type=int,
            help='Set the log level (0,10,20,30,40,50).  Default is 30.',
            default=NoConfigDefault,
            metavar='Global.log_level')
        self.parser.add_argument('-config_file', '--config-file',
            dest='Global.config_file',type=str,
            help='Set the config file name to override default.',
            default=NoConfigDefault,
            metavar='Global.config_file')


class ApplicationError(Exception):
    pass


class Application(object):
    """Load a config, construct an app and run it.
    """

    name = 'ipython'
    description = 'IPython: an enhanced interactive Python shell.'
    config_file_name = 'ipython_config.py'
    default_log_level = logging.WARN
    

    def __init__(self):
        self.init_logger()
        self.default_config_file_name = self.config_file_name

    def init_logger(self):
        self.log = logging.getLogger(self.__class__.__name__)
        # This is used as the default until the command line arguments are read.
        self.log.setLevel(self.default_log_level)
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
        self.log_default_config()
        self.set_default_config_log_level()
        self.attempt(self.pre_load_command_line_config)
        self.attempt(self.load_command_line_config, action='abort')
        self.set_command_line_config_log_level()
        self.attempt(self.post_load_command_line_config)
        self.log_command_line_config()
        self.attempt(self.find_ipythondir)
        self.attempt(self.find_config_file_name)
        self.attempt(self.find_config_file_paths)
        self.attempt(self.pre_load_file_config)
        self.attempt(self.load_file_config)
        self.set_file_config_log_level()
        self.attempt(self.post_load_file_config)
        self.log_file_config()
        self.attempt(self.merge_configs)
        self.log_master_config()
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
        self.default_config.Global.log_level = self.log_level

    def log_default_config(self):
        self.log.debug('Default config loaded:')
        self.log.debug(repr(self.default_config))

    def set_default_config_log_level(self):
        try:
            self.log_level = self.default_config.Global.log_level
        except AttributeError:
            # Fallback to the default_log_level class attribute
            pass

    def create_command_line_config(self):
        """Create and return a command line config loader."""
        return BaseAppArgParseConfigLoader(
            description=self.description, 
            version=release.version
        )

    def pre_load_command_line_config(self):
        """Do actions just before loading the command line config."""
        pass

    def load_command_line_config(self):
        """Load the command line config."""
        loader = self.create_command_line_config()
        self.command_line_config = loader.load_config()
        self.extra_args = loader.get_extra_args()

    def set_command_line_config_log_level(self):
        try:
            self.log_level = self.command_line_config.Global.log_level
        except AttributeError:
            pass

    def post_load_command_line_config(self):
        """Do actions just after loading the command line config."""
        pass

    def log_command_line_config(self):
        self.log.debug("Command line config loaded:")
        self.log.debug(repr(self.command_line_config))

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
            os.makedirs(self.ipythondir, mode=0777)
        self.log.debug("IPYTHONDIR set to: %s" % self.ipythondir)

    def find_config_file_name(self):
        """Find the config file name for this application.

        This must set ``self.config_file_name`` to the filename of the
        config file to use (just the filename). The search paths for the
        config file are set in :meth:`find_config_file_paths` and then passed
        to the config file loader where they are resolved to an absolute path.

        If a profile has been set at the command line, this will resolve
        it.
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
        """Set the search paths for resolving the config file.

        This must set ``self.config_file_paths`` to a sequence of search
        paths to pass to the config file loader.
        """
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
        self.log.debug("Attempting to load config file: %s" % self.config_file_name)
        loader = PyFileConfigLoader(self.config_file_name,
                                    path=self.config_file_paths)
        try:
            self.file_config = loader.load_config()
            self.file_config.Global.config_file = loader.full_filename
        except IOError:
            # Only warn if the default config file was NOT being used.
            if not self.config_file_name==self.default_config_file_name:
                self.log.warn("Config file not found, skipping: %s" % \
                               self.config_file_name, exc_info=True)
            self.file_config = Config()
        except:
            self.log.warn("Error loading config file: %s" % \
                           self.config_file_name, exc_info=True)
            self.file_config = Config()

    def set_file_config_log_level(self):
        # We need to keeep self.log_level updated.  But we only use the value
        # of the file_config if a value was not specified at the command
        # line, because the command line overrides everything.
        if not hasattr(self.command_line_config.Global, 'log_level'):
            try:
                self.log_level = self.file_config.Global.log_level
            except AttributeError:
                pass # Use existing value

    def post_load_file_config(self):
        """Do actions after the config file is loaded."""
        pass

    def log_file_config(self):
        if hasattr(self.file_config.Global, 'config_file'):
            self.log.debug("Config file loaded: %s" % self.file_config.Global.config_file)
            self.log.debug(repr(self.file_config))

    def merge_configs(self):
        """Merge the default, command line and file config objects."""
        config = Config()
        config._merge(self.default_config)
        config._merge(self.file_config)
        config._merge(self.command_line_config)
        self.master_config = config

    def log_master_config(self):
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


class AppWithDirArgParseConfigLoader(ArgParseConfigLoader):
    """Default command line options for IPython based applications."""

    def _add_other_arguments(self):
        self.parser.add_argument('-ipythondir', '--ipython-dir', 
            dest='Global.ipythondir',type=str,
            help='Set to override default location of Global.ipythondir.',
            default=NoConfigDefault,
            metavar='Global.ipythondir')
        self.parser.add_argument('-p','-profile', '--profile',
            dest='Global.profile',type=str,
            help='The string name of the profile to be used. This determines '
            'the name of the application dir: basename_<profile>.  The basename is '
            'determined by the particular application.  The default profile '
            'is named "default".  This convention is used if the -app_dir '
            'option is not used.',
            default=NoConfigDefault,
            metavar='Global.profile')
        self.parser.add_argument('-log_level', '--log-level',
            dest="Global.log_level",type=int,
            help='Set the log level (0,10,20,30,40,50).  Default is 30.',
            default=NoConfigDefault)
        self.parser.add_argument('-app_dir', '--app-dir',
            dest='Global.app_dir',type=str,
            help='Set the application dir where everything for this '
            'application will be found (including the config file). This '
            'overrides the logic used by the profile option.',
            default=NoConfigDefault,
            metavar='Global.app_dir')


class ApplicationWithDir(Application):
    """An application that puts everything into a application directory.

    Instead of looking for things in the ipythondir, this type of application
    will use its own private directory called the "application directory"
    for things like config files, log files, etc.

    The application directory is resolved as follows:

    * If the ``--app-dir`` option is given, it is used.
    * If ``--app-dir`` is not given, the application directory is resolve using
      ``app_dir_basename`` and ``profile`` as ``<app_dir_basename>_<profile>``.
      The search path for this directory is then i) cwd if it is found there
      and ii) in ipythondir otherwise.

    The config file for the application is to be put in the application
    dir and named the value of the ``config_file_name`` class attribute.
    """

    # The basename used for the application dir: <app_dir_basename>_<profile>
    app_dir_basename = 'cluster'

    def create_default_config(self):
        super(ApplicationWithDir, self).create_default_config()
        self.default_config.Global.profile = 'default'
        # The application dir.  This is empty initially so the default is to
        # try to resolve this using the profile.
        self.default_config.Global.app_dir = ''

    def create_command_line_config(self):
        """Create and return a command line config loader."""
        return AppWithDirArgParseConfigLoader(
            description=self.description, 
            version=release.version
        )

    def find_config_file_name(self):
        """Find the config file name for this application."""
        self.find_app_dir()
        self.create_app_dir()

    def find_app_dir(self):
        """This resolves the app directory.

        This method must set ``self.app_dir`` to the location of the app
        dir.
        """
        # Instead, first look for an explicit app_dir
        try:
            self.app_dir = self.command_line_config.Global.app_dir
        except AttributeError:
            self.app_dir = self.default_config.Global.app_dir
        self.app_dir = os.path.expandvars(os.path.expanduser(self.app_dir))
        if not self.app_dir:
            # Then look for a profile
            try:
                self.profile = self.command_line_config.Global.profile
            except AttributeError:
                self.profile = self.default_config.Global.profile
            app_dir_name = self.app_dir_basename + '_' + self.profile
            try_this = os.path.join(os.getcwd(), app_dir_name)
            if os.path.isdir(try_this):
                self.app_dir = try_this
            else:
                self.app_dir = os.path.join(self.ipythondir, app_dir_name)
        # These have to be set because they could be different from the one
        # that we just computed.  Because command line has the highest
        # priority, this will always end up in the master_config.
        self.default_config.Global.app_dir = self.app_dir
        self.command_line_config.Global.app_dir = self.app_dir
        self.log.info("Application directory set to: %s" % self.app_dir)

    def create_app_dir(self):
        """Make sure that the app dir exists."""
        if not os.path.isdir(self.app_dir):
            os.makedirs(self.app_dir, mode=0777)

    def find_config_file_paths(self):
        """Set the search paths for resolving the config file."""
        self.config_file_paths = (self.app_dir,)
