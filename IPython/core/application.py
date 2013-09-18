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
* Min RK

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

import atexit
import glob
import logging
import os
import shutil
import sys

from IPython.config.application import Application, catch_config_error
from IPython.config.loader import ConfigFileNotFound
from IPython.core import release, crashhandler
from IPython.core.profiledir import ProfileDir, ProfileDirError
from IPython.utils.path import get_ipython_dir, get_ipython_package_dir
from IPython.utils.traitlets import List, Unicode, Type, Bool, Dict, Set, Instance

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------


#-----------------------------------------------------------------------------
# Base Application Class
#-----------------------------------------------------------------------------

# aliases and flags

base_aliases = {
    'profile-dir' : 'ProfileDir.location',
    'profile' : 'BaseIPythonApplication.profile',
    'ipython-dir' : 'BaseIPythonApplication.ipython_dir',
    'log-level' : 'Application.log_level',
    'config' : 'BaseIPythonApplication.extra_config_file',
}

base_flags = dict(
    debug = ({'Application' : {'log_level' : logging.DEBUG}},
            "set log level to logging.DEBUG (maximize logging output)"),
    quiet = ({'Application' : {'log_level' : logging.CRITICAL}},
            "set log level to logging.CRITICAL (minimize logging output)"),
    init = ({'BaseIPythonApplication' : {
                    'copy_config_files' : True,
                    'auto_create' : True}
            }, """Initialize profile with default config files.  This is equivalent
            to running `ipython profile create <profile>` prior to startup.
            """)
)


class BaseIPythonApplication(Application):

    name = Unicode(u'ipython')
    description = Unicode(u'IPython: an enhanced interactive Python shell.')
    version = Unicode(release.version)

    aliases = Dict(base_aliases)
    flags = Dict(base_flags)
    classes = List([ProfileDir])

    # Track whether the config_file has changed,
    # because some logic happens only if we aren't using the default.
    config_file_specified = Set()

    config_file_name = Unicode()
    def _config_file_name_default(self):
        return self.name.replace('-','_') + u'_config.py'
    def _config_file_name_changed(self, name, old, new):
        if new != old:
            self.config_file_specified.add(new)

    # The directory that contains IPython's builtin profiles.
    builtin_profile_dir = Unicode(
        os.path.join(get_ipython_package_dir(), u'config', u'profile', u'default')
    )

    config_file_paths = List(Unicode)
    def _config_file_paths_default(self):
        return [os.getcwdu()]

    extra_config_file = Unicode(config=True,
    help="""Path to an extra config file to load.
    
    If specified, load this config file in addition to any other IPython config.
    """)
    def _extra_config_file_changed(self, name, old, new):
        try:
            self.config_files.remove(old)
        except ValueError:
            pass
        self.config_file_specified.add(new)
        self.config_files.append(new)

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
        the environment variable IPYTHONDIR.
        """
    )
    _in_init_profile_dir = False
    profile_dir = Instance(ProfileDir)
    def _profile_dir_default(self):
        # avoid recursion
        if self._in_init_profile_dir:
            return
        # profile_dir requested early, force initialization
        self.init_profile_dir()
        return self.profile_dir

    overwrite = Bool(False, config=True,
        help="""Whether to overwrite existing config files when copying""")
    auto_create = Bool(False, config=True,
        help="""Whether to create profile dir if it doesn't exist""")

    config_files = List(Unicode)
    def _config_files_default(self):
        return [self.config_file_name]

    copy_config_files = Bool(False, config=True,
        help="""Whether to install the default config files into the profile dir.
        If a new profile is being created, and IPython contains config files for that
        profile, then they will be staged into the new directory.  Otherwise,
        default config files will be automatically generated.
        """)
    
    verbose_crash = Bool(False, config=True,
        help="""Create a massive crash report when IPython encounters what may be an
        internal error.  The default is to append a short message to the
        usual traceback""")

    # The class to use as the crash handler.
    crash_handler_class = Type(crashhandler.CrashHandler)

    @catch_config_error
    def __init__(self, **kwargs):
        super(BaseIPythonApplication, self).__init__(**kwargs)
        # ensure current working directory exists
        try:
            directory = os.getcwdu()
        except:
            # raise exception
            self.log.error("Current working directory doesn't exist.")
            raise

        # ensure even default IPYTHONDIR exists
        if not os.path.exists(self.ipython_dir):
            self._ipython_dir_changed('ipython_dir', self.ipython_dir, self.ipython_dir)

    #-------------------------------------------------------------------------
    # Various stages of Application creation
    #-------------------------------------------------------------------------

    def init_crash_handler(self):
        """Create a crash handler, typically setting sys.excepthook to it."""
        self.crash_handler = self.crash_handler_class(self)
        sys.excepthook = self.excepthook
        def unset_crashhandler():
            sys.excepthook = sys.__excepthook__
        atexit.register(unset_crashhandler)
    
    def excepthook(self, etype, evalue, tb):
        """this is sys.excepthook after init_crashhandler
        
        set self.verbose_crash=True to use our full crashhandler, instead of
        a regular traceback with a short message (crash_handler_lite)
        """
        
        if self.verbose_crash:
            return self.crash_handler(etype, evalue, tb)
        else:
            return crashhandler.crash_handler_lite(etype, evalue, tb)
    
    def _ipython_dir_changed(self, name, old, new):
        if old in sys.path:
            sys.path.remove(old)
        sys.path.append(os.path.abspath(new))
        if not os.path.isdir(new):
            os.makedirs(new, mode=0o777)
        readme = os.path.join(new, 'README')
        if not os.path.exists(readme):
            path = os.path.join(get_ipython_package_dir(), u'config', u'profile')
            shutil.copy(os.path.join(path, 'README'), readme)
        self.log.debug("IPYTHONDIR set to: %s" % new)

    def load_config_file(self, suppress_errors=True):
        """Load the config file.

        By default, errors in loading config are handled, and a warning
        printed on screen. For testing, the suppress_errors option is set
        to False, so errors will make tests fail.
        """
        self.log.debug("Searching path %s for config files", self.config_file_paths)
        base_config = 'ipython_config.py'
        self.log.debug("Attempting to load config file: %s" %
                       base_config)
        try:
            Application.load_config_file(
                self,
                base_config,
                path=self.config_file_paths
            )
        except ConfigFileNotFound:
            # ignore errors loading parent
            self.log.debug("Config file %s not found", base_config)
            pass
        
        for config_file_name in self.config_files:
            if not config_file_name or config_file_name == base_config:
                continue
            self.log.debug("Attempting to load config file: %s" %
                           self.config_file_name)
            try:
                Application.load_config_file(
                    self,
                    config_file_name,
                    path=self.config_file_paths
                )
            except ConfigFileNotFound:
                # Only warn if the default config file was NOT being used.
                if config_file_name in self.config_file_specified:
                    msg = self.log.warn
                else:
                    msg = self.log.debug
                msg("Config file not found, skipping: %s", config_file_name)
            except:
                # For testing purposes.
                if not suppress_errors:
                    raise
                self.log.warn("Error loading config file: %s" %
                              self.config_file_name, exc_info=True)

    def init_profile_dir(self):
        """initialize the profile dir"""
        self._in_init_profile_dir = True
        if self.profile_dir is not None:
            # already ran
            return
        try:
            # location explicitly specified:
            location = self.config.ProfileDir.location
        except AttributeError:
            # location not specified, find by profile name
            try:
                p = ProfileDir.find_profile_dir_by_name(self.ipython_dir, self.profile, self.config)
            except ProfileDirError:
                # not found, maybe create it (always create default profile)
                if self.auto_create or self.profile == 'default':
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
        self._in_init_profile_dir = False

    def init_config_files(self):
        """[optionally] copy default config files into profile dir."""
        # copy config files
        path = self.builtin_profile_dir
        if self.copy_config_files:
            src = self.profile

            cfg = self.config_file_name
            if path and os.path.exists(os.path.join(path, cfg)):
                self.log.warn("Staging %r from %s into %r [overwrite=%s]"%(
                        cfg, src, self.profile_dir.location, self.overwrite)
                )
                self.profile_dir.copy_config_file(cfg, path=path, overwrite=self.overwrite)
            else:
                self.stage_default_config_file()
        else:
            # Still stage *bundled* config files, but not generated ones
            # This is necessary for `ipython profile=sympy` to load the profile
            # on the first go
            files = glob.glob(os.path.join(path, '*.py'))
            for fullpath in files:
                cfg = os.path.basename(fullpath)
                if self.profile_dir.copy_config_file(cfg, path=path, overwrite=False):
                    # file was copied
                    self.log.warn("Staging bundled %s from %s into %r"%(
                            cfg, self.profile, self.profile_dir.location)
                    )


    def stage_default_config_file(self):
        """auto generate default config file, and stage it into the profile."""
        s = self.generate_config_file()
        fname = os.path.join(self.profile_dir.location, self.config_file_name)
        if self.overwrite or not os.path.exists(fname):
            self.log.warn("Generating default config file: %r"%(fname))
            with open(fname, 'w') as f:
                f.write(s)

    @catch_config_error
    def initialize(self, argv=None):
        # don't hook up crash handler before parsing command-line
        self.parse_command_line(argv)
        self.init_crash_handler()
        if self.subapp is not None:
            # stop here if subapp is taking over
            return
        cl_config = self.config
        self.init_profile_dir()
        self.init_config_files()
        self.load_config_file()
        # enforce cl-opts override configfile opts:
        self.update_config(cl_config)

