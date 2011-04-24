# encoding: utf-8
"""
A base class for a configurable application.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from copy import deepcopy
import logging
import sys

from IPython.config.configurable import SingletonConfigurable
from IPython.utils.traitlets import (
    Unicode, List, Int, Enum
)
from IPython.config.loader import (
    KeyValueConfigLoader, PyFileConfigLoader
)

#-----------------------------------------------------------------------------
# Application class
#-----------------------------------------------------------------------------


class Application(SingletonConfigurable):
    """A singleton application with full configuration support."""

    # The name of the application, will usually match the name of the command
    # line application
    app_name = Unicode(u'application')

    # The description of the application that is printed at the beginning
    # of the help.
    description = Unicode(u'This is an application.')

    # A sequence of Configurable subclasses whose config=True attributes will
    # be exposed at the command line (shortnames and help).
    classes = List([])

    # The version string of this application.
    version = Unicode(u'0.0')

    # The log level for the application
    log_level = Enum((0,10,20,30,40,50), default_value=logging.WARN,
                     config=True, shortname="log_level",
                     help="Set the log level (0,10,20,30,40,50).")

    def __init__(self, **kwargs):
        SingletonConfigurable.__init__(self, **kwargs)
        # Add my class to self.classes so my attributes appear in command line
        # options.
        self.classes.insert(0, self.__class__)
        self.init_logging()

    def init_logging(self):
        """Start logging for this application.

        The default is to log to stdout using a StreaHandler. The log level
        starts at loggin.WARN, but this can be adjusted by setting the 
        ``log_level`` attribute.
        """
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(self.log_level)
        self._log_handler = logging.StreamHandler()
        self._log_formatter = logging.Formatter("[%(name)s] %(message)s")
        self._log_handler.setFormatter(self._log_formatter)
        self.log.addHandler(self._log_handler)

    def _log_level_changed(self, name, old, new):
        """Adjust the log level when log_level is set."""
        self.log.setLevel(new)

    def print_help(self):
        """Print the help for each Configurable class in self.classes."""
        for cls in self.classes:
            cls.class_print_help()
            print

    def print_description(self):
        """Print the application description."""
        print self.description
        print

    def print_version(self):
        """Print the version string."""
        print self.version

    def update_config(self, config):
        """Fire the traits events when the config is updated."""
        # Save a copy of the current config.
        newconfig = deepcopy(self.config)
        # Merge the new config into the current one.
        newconfig._merge(config)
        # Save the combined config as self.config, which triggers the traits
        # events.
        self.config = config

    def parse_command_line(self, argv=None):
        """Parse the command line arguments."""
        argv = sys.argv[1:] if argv is None else argv

        if '-h' in argv or '--h' in argv:
            self.print_description()
            self.print_help()
            sys.exit(1)

        if '--version' in argv:
            self.print_version()
            sys.exit(1)

        loader = KeyValueConfigLoader(argv=argv, classes=self.classes)
        config = loader.load_config()
        self.update_config(config)

    def load_config_file(self, filename, path=None):
        """Load a .py based config file by filename and path."""
        # TODO: this raises IOError if filename does not exist.
        loader = PyFileConfigLoader(filename, path=path)
        config = loader.load_config()
        self.update_config(config)

