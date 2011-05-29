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

import logging
import os
import shutil
import sys

from IPython.config.application import Application
from IPython.config.configurable import Configurable
from IPython.config.loader import Config
from IPython.core import release, crashhandler
from IPython.utils.path import get_ipython_dir, get_ipython_package_dir, expand_path
from IPython.utils.traitlets import List, Unicode, Type, Bool, Dict

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------


#-----------------------------------------------------------------------------
# Module errors
#-----------------------------------------------------------------------------

class ProfileDirError(Exception):
    pass


#-----------------------------------------------------------------------------
# Class for managing profile directories
#-----------------------------------------------------------------------------

class ProfileDir(Configurable):
    """An object to manage the profile directory and its resources.

    The profile directory is used by all IPython applications, to manage
    configuration, logging and security.

    This object knows how to find, create and manage these directories. This
    should be used by any code that wants to handle profiles.
    """

    security_dir_name = Unicode('security')
    log_dir_name = Unicode('log')
    pid_dir_name = Unicode('pid')
    security_dir = Unicode(u'')
    log_dir = Unicode(u'')
    pid_dir = Unicode(u'')

    location = Unicode(u'', config=True,
        help="""Set the profile location directly. This overrides the logic used by the
        `profile` option.""",
        )

    _location_isset = Bool(False) # flag for detecting multiply set location

    def _location_changed(self, name, old, new):
        if self._location_isset:
            raise RuntimeError("Cannot set profile location more than once.")
        self._location_isset = True
        if not os.path.isdir(new):
            os.makedirs(new)
        
        # ensure config files exist:
        self.security_dir = os.path.join(new, self.security_dir_name)
        self.log_dir = os.path.join(new, self.log_dir_name)
        self.pid_dir = os.path.join(new, self.pid_dir_name)
        self.check_dirs()

    def _log_dir_changed(self, name, old, new):
        self.check_log_dir()

    def check_log_dir(self):
        if not os.path.isdir(self.log_dir):
            os.mkdir(self.log_dir)

    def _security_dir_changed(self, name, old, new):
        self.check_security_dir()

    def check_security_dir(self):
        if not os.path.isdir(self.security_dir):
            os.mkdir(self.security_dir, 0700)
        else:
            os.chmod(self.security_dir, 0700)

    def _pid_dir_changed(self, name, old, new):
        self.check_pid_dir()

    def check_pid_dir(self):
        if not os.path.isdir(self.pid_dir):
            os.mkdir(self.pid_dir, 0700)
        else:
            os.chmod(self.pid_dir, 0700)

    def check_dirs(self):
        self.check_security_dir()
        self.check_log_dir()
        self.check_pid_dir()

    def copy_config_file(self, config_file, path=None, overwrite=False):
        """Copy a default config file into the active profile directory.

        Default configuration files are kept in :mod:`IPython.config.default`.
        This function moves these from that location to the working profile
        directory.
        """
        dst = os.path.join(self.location, config_file)
        if os.path.isfile(dst) and not overwrite:
            return
        if path is None:
            path = os.path.join(get_ipython_package_dir(), u'config', u'profile', u'default')
        src = os.path.join(path, config_file)
        shutil.copy(src, dst)

    @classmethod
    def create_profile_dir(cls, profile_dir, config=None):
        """Create a new profile directory given a full path.

        Parameters
        ----------
        profile_dir : str
            The full path to the profile directory.  If it does exist, it will
            be used.  If not, it will be created.
        """
        return cls(location=profile_dir, config=config)

    @classmethod
    def create_profile_dir_by_name(cls, path, name=u'default', config=None):
        """Create a profile dir by profile name and path.

        Parameters
        ----------
        path : unicode
            The path (directory) to put the profile directory in.
        name : unicode
            The name of the profile.  The name of the profile directory will
            be "profile_<profile>".
        """
        if not os.path.isdir(path):
            raise ProfileDirError('Directory not found: %s' % path)
        profile_dir = os.path.join(path, u'profile_' + name)
        return cls(location=profile_dir, config=config)

    @classmethod
    def find_profile_dir_by_name(cls, ipython_dir, name=u'default', config=None):
        """Find an existing profile dir by profile name, return its ProfileDir.

        This searches through a sequence of paths for a profile dir.  If it
        is not found, a :class:`ProfileDirError` exception will be raised.

        The search path algorithm is:
        1. ``os.getcwd()``
        2. ``ipython_dir``
        3. The directories found in the ":" separated 
           :env:`IPCLUSTER_DIR_PATH` environment variable.

        Parameters
        ----------
        ipython_dir : unicode or str
            The IPython directory to use.
        name : unicode or str
            The name of the profile.  The name of the profile directory
            will be "profile_<profile>".
        """
        dirname = u'profile_' + name
        profile_dir_paths = os.environ.get('IPYTHON_PROFILE_PATH','')
        if profile_dir_paths:
            profile_dir_paths = profile_dir_paths.split(os.pathsep)
        else:
            profile_dir_paths = []
        paths = [os.getcwd(), ipython_dir] + profile_dir_paths
        for p in paths:
            profile_dir = os.path.join(p, dirname)
            if os.path.isdir(profile_dir):
                return cls(location=profile_dir, config=config)
        else:
            raise ProfileDirError('Profile directory not found in paths: %s' % dirname)

    @classmethod
    def find_profile_dir(cls, profile_dir, config=None):
        """Find/create a profile dir and return its ProfileDir.

        This will create the profile directory if it doesn't exist.

        Parameters
        ----------
        profile_dir : unicode or str
            The path of the profile directory.  This is expanded using
            :func:`IPython.utils.genutils.expand_path`.
        """
        profile_dir = expand_path(profile_dir)
        if not os.path.isdir(profile_dir):
            raise ProfileDirError('Profile directory not found: %s' % profile_dir)
        return cls(location=profile_dir, config=config)


#-----------------------------------------------------------------------------
# Base Application Class
#-----------------------------------------------------------------------------

# aliases and flags

base_aliases = dict(
    profile='BaseIPythonApplication.profile',
    ipython_dir='BaseIPythonApplication.ipython_dir',
)

base_flags = dict(
    debug = ({'Application' : Config({'log_level' : logging.DEBUG})},
            "set log level to logging.DEBUG (maximize logging output)"),
    quiet = ({'Application' : Config({'log_level' : logging.CRITICAL})},
            "set log level to logging.CRITICAL (minimize logging output)"),
    init = ({'BaseIPythonApplication' : Config({
                    'copy_config_files' : True,
                    'auto_create' : True})
            }, "Initialize profile with default config files")
)


class BaseIPythonApplication(Application):

    name = Unicode(u'ipython')
    description = Unicode(u'IPython: an enhanced interactive Python shell.')
    version = Unicode(release.version)
    
    aliases = Dict(base_aliases)
    flags = Dict(base_flags)
    
    # Track whether the config_file has changed,
    # because some logic happens only if we aren't using the default.
    config_file_specified = Bool(False)
    
    config_file_name = Unicode(u'ipython_config.py')
    def _config_file_name_changed(self, name, old, new):
        if new != old:
            self.config_file_specified = True

    # The directory that contains IPython's builtin profiles.
    builtin_profile_dir = Unicode(
        os.path.join(get_ipython_package_dir(), u'config', u'profile', u'default')
    )

    config_file_paths = List(Unicode)
    def _config_file_paths_default(self):
        return [os.getcwdu()]

    profile = Unicode(u'default', config=True,
        help="""The IPython profile to use."""
    )
    def _profile_changed(self, name, old, new):
        self.builtin_profile_dir = os.path.join(
                get_ipython_package_dir(), u'config', u'profile', new
        )
        

    ipython_dir = Unicode(get_ipython_dir(), config=True, 
        help="""
        The name of the IPython directory. This directory is used for logging
        configuration (through profiles), history storage, etc. The default
        is usually $HOME/.ipython. This options can also be specified through
        the environment variable IPYTHON_DIR.
        """
    )
    
    overwrite = Bool(False, config=True,
        help="""Whether to overwrite existing config files when copying""")
    auto_create = Bool(False, config=True,
        help="""Whether to create profile dir if it doesn't exist""")
    
    config_files = List(Unicode)
    def _config_files_default(self):
        return [u'ipython_config.py']
    
    copy_config_files = Bool(False, config=True,
        help="""Whether to copy the default config files into the profile dir.""")

    # The class to use as the crash handler.
    crash_handler_class = Type(crashhandler.CrashHandler)

    def __init__(self, **kwargs):
        super(BaseIPythonApplication, self).__init__(**kwargs)
        # ensure even default IPYTHON_DIR exists
        if not os.path.exists(self.ipython_dir):
            self._ipython_dir_changed('ipython_dir', self.ipython_dir, self.ipython_dir)
    
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
        readme = os.path.join(new, 'README')
        if not os.path.exists(readme):
            path = os.path.join(get_ipython_package_dir(), u'config', u'profile')
            shutil.copy(os.path.join(path, 'README'), readme)
        self.log.debug("IPYTHON_DIR set to: %s" % new)

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
            if self.config_file_specified:
                self.log.warn("Config file not found, skipping: %s" %
                               self.config_file_name)
        except:
            # For testing purposes.
            if not suppress_errors:
                raise
            self.log.warn("Error loading config file: %s" %
                          self.config_file_name, exc_info=True)

    def init_profile_dir(self):
        """initialize the profile dir"""
        try:
            # location explicitly specified:
            location = self.config.ProfileDir.location
        except AttributeError:
            # location not specified, find by profile name
            try:
                p = ProfileDir.find_profile_dir_by_name(self.ipython_dir, self.profile, self.config)
            except ProfileDirError:
                # not found, maybe create it (always create default profile)
                if self.auto_create or self.profile=='default':
                    try:
                        p = ProfileDir.create_profile_dir_by_name(self.ipython_dir, self.profile, self.config)
                    except ProfileDirError:
                        self.log.fatal("Could not create profile: %r"%self.profile)
                        self.exit(1)
                    else:
                        self.log.info("Created profile dir: %r"%p.location)
                else:
                    self.log.fatal("Profile %r not found."%self.profile)
                    self.exit(1)
            else:
                self.log.info("Using existing profile dir: %r"%p.location)
        else:
            # location is fully specified
            try:
                p = ProfileDir.find_profile_dir(location, self.config)
            except ProfileDirError:
                # not found, maybe create it
                if self.auto_create:
                    try:
                        p = ProfileDir.create_profile_dir(location, self.config)
                    except ProfileDirError:
                        self.log.fatal("Could not create profile directory: %r"%location)
                        self.exit(1)
                    else:
                        self.log.info("Creating new profile dir: %r"%location)
                else:
                    self.log.fatal("Profile directory %r not found."%location)
                    self.exit(1)
            else:
                self.log.info("Using existing profile dir: %r"%location)
        
        self.profile_dir = p
        self.config_file_paths.append(p.location)
    
    def init_config_files(self):
        """[optionally] copy default config files into profile dir."""
        # copy config files
        if self.copy_config_files:
            path = self.builtin_profile_dir
            src = self.profile
            if not os.path.exists(path):
                # use default if new profile doesn't have a preset
                path = None
                src = 'default'
            
            self.log.debug("Staging %s config files into %r [overwrite=%s]"%(
                    src, self.profile_dir.location, self.overwrite)
            )
            
            for cfg in self.config_files:
                self.profile_dir.copy_config_file(cfg, path=path, overwrite=self.overwrite)
    
    def initialize(self, argv=None):
        self.init_crash_handler()
        self.parse_command_line(argv)
        cl_config = self.config
        self.init_profile_dir()
        self.init_config_files()
        self.load_config_file()
        # enforce cl-opts override configfile opts:
        self.update_config(cl_config)

