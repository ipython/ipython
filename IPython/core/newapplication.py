# encoding: utf-8
"""
An application for IPython.

All top-level applications should use the classes in this module for
handling configuration and creating componenets.

The job of an :class:`Application` is to create the master configuration 
object and then create the configurable objects, passing the config to them.

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

from IPython.config.application import Application
from IPython.core import release, crashhandler
from IPython.utils.path import get_ipython_dir, get_ipython_package_dir
from IPython.utils.traitlets import List, Unicode, Type

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------


class BaseIPythonApplication(Application):

    name = Unicode(u'ipython')
    description = Unicode(u'IPython: an enhanced interactive Python shell.')
    version = Unicode(release.version)

    # The name of the default config file. Track separately from the actual
    # name because some logic happens only if we aren't using the default.
    default_config_file_name = Unicode(u'ipython_config.py')

    # The directory that contains IPython's builtin profiles.
    builtin_profile_dir = Unicode(
        os.path.join(get_ipython_package_dir(), u'config', u'profile')
    )

    config_file_paths = List(Unicode)
    def _config_file_paths_default(self):
        return [os.getcwdu(), self.ipython_dir, self.builtin_profile_dir]

    profile_name = Unicode(u'', config=True,
        help="""The IPython profile to use."""
    )

    ipython_dir = Unicode(get_ipython_dir(), config=True, help=
        """
        The name of the IPython directory. This directory is used for logging
        configuration (through profiles), history storage, etc. The default
        is usually $HOME/.ipython. This options can also be specified through
        the environment variable IPYTHON_DIR.
        """
    )

    # The class to use as the crash handler.
    crash_handler_class = Type(crashhandler.CrashHandler)

    #-------------------------------------------------------------------------
    # Various stages of Application creation
    #-------------------------------------------------------------------------

    def init_crash_handler(self):
        """Create a crash handler, typically setting sys.excepthook to it."""
        self.crash_handler = self.crash_handler_class(self)
        sys.excepthook = self.crash_handler

    def _ipython_dir_changed(self, name, old, new):
        if old in sys.path:
            sys.path.remove(old)
        sys.path.append(os.path.abspath(new))
        if not os.path.isdir(new):
            os.makedirs(new, mode=0777)
        self.config_file_paths = (os.getcwdu(), new, self.builtin_profile_dir)
        self.log.debug("IPYTHON_DIR set to: %s" % new)

    @property
    def config_file_name(self):
        """Find the config file name for this application."""
        if self.profile_name:
            name_parts = self.default_config_file_name.split('.')
            name_parts.insert(1, u'_' + self.profile_name + u'.')
            return ''.join(name_parts)
        else:
            return self.default_config_file_name

    def load_config_file(self, suppress_errors=True):
        """Load the config file.

        By default, errors in loading config are handled, and a warning
        printed on screen. For testing, the suppress_errors option is set
        to False, so errors will make tests fail.
        """
        self.log.debug("Attempting to load config file: %s" %
                       self.config_file_name)
        try:
            Application.load_config_file(
                self,
                self.config_file_name, 
                path=self.config_file_paths
            )
        except IOError:
            # Only warn if the default config file was NOT being used.
            if not self.config_file_name == self.default_config_file_name:
                self.log.warn("Config file not found, skipping: %s" %
                               self.config_file_name, exc_info=True)
        except:
            # For testing purposes.
            if not suppress_errors:
                raise
            self.log.warn("Error loading config file: %s" %
                          self.config_file_name, exc_info=True)

    def initialize(self, argv=None):
        self.init_crash_handler()
        self.parse_command_line(argv)
        cl_config = self.config
        self.load_config_file()
        # enforce cl-opts override configfile opts:
        self.update_config(cl_config)


