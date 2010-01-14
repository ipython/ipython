# encoding: utf-8
"""
An application for IPython.

All top-level applications should use the classes in this module for
handling configuration and creating componenets.

The job of an :class:`Application` is to create the master configuration 
object and then create the components, passing the config to them.

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

from IPython.core import release, crashhandler
from IPython.utils.genutils import get_ipython_dir, get_ipython_package_dir
from IPython.config.loader import (
    PyFileConfigLoader,
    ArgParseConfigLoader,
    Config,
)

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class ApplicationError(Exception):
    pass


app_cl_args = (
    (('--ipython-dir', ), dict(
        dest='Global.ipython_dir',type=unicode,
        help=
        """Set to override default location of the IPython directory
        IPYTHON_DIR, stored as Global.ipython_dir.  This can also be specified
        through the environment variable IPYTHON_DIR.""",
        metavar='Global.ipython_dir') ),
    (('-p', '--profile',), dict(
        dest='Global.profile',type=unicode,
        help=
        """The string name of the ipython profile to be used.  Assume that your
        config file is ipython_config-<name>.py (looks in current dir first,
        then in IPYTHON_DIR). This is a quick way to keep and load multiple
        config files for different tasks, especially if include your basic one
        in your more specialized ones.  You can keep a basic
        IPYTHON_DIR/ipython_config.py file and then have other 'profiles' which
        include this one and load extra things for particular tasks.""",
        metavar='Global.profile') ),
    (('--log-level',), dict(
        dest="Global.log_level",type=int,
        help='Set the log level (0,10,20,30,40,50).  Default is 30.',
        metavar='Global.log_level')),
    (('--config-file',), dict(
        dest='Global.config_file',type=unicode,
        help=
        """Set the config file name to override default.  Normally IPython
        loads ipython_config.py (from current directory) or
        IPYTHON_DIR/ipython_config.py.  If the loading of your config file
        fails, IPython starts with a bare bones configuration (no modules
        loaded at all).""",
        metavar='Global.config_file')),
    )

class Application(object):
    """Load a config, construct components and set them running.

    The configuration of an application can be done via four different Config
    objects, which are loaded and ultimately merged into a single one used from
    that point on by the app.  These are:

    1. default_config: internal defaults, implemented in code.
    2. file_config: read from the filesystem.
    3. command_line_config: read from the system's command line flags.
    4. constructor_config: passed parametrically to the constructor.

    During initialization, 3 is actually read before 2, since at the
    command-line one may override the location of the file to be read.  But the
    above is the order in which the merge is made.

    There is a final config object can be created and passed to the
    constructor: override_config.  If it exists, this completely overrides the
    configs 2-4 above (the default is still used to ensure that all needed
    fields at least are created).  This makes it easier to create
    parametrically (e.g. in testing or sphinx plugins) objects with a known
    configuration, that are unaffected by whatever arguments may be present in
    sys.argv or files in the user's various directories.
    """

    name = u'ipython'
    description = 'IPython: an enhanced interactive Python shell.'
    #: usage message printed by argparse. If None, auto-generate
    usage = None
    config_file_name = u'ipython_config.py'
    #: Track the default and actual separately because some messages are
    #: only printed if we aren't using the default.
    default_config_file_name = config_file_name
    default_log_level = logging.WARN
    #: Set by --profile option
    profile_name = None
    #: User's ipython directory, typically ~/.ipython/
    ipython_dir = None
    #: internal defaults, implemented in code.
    default_config = None
    #: read from the filesystem
    file_config = None
    #: read from the system's command line flags
    command_line_config = None
    #: passed parametrically to the constructor.
    constructor_config = None
    #: final override, if given supercedes file/command/constructor configs
    override_config = None
    #: A reference to the argv to be used (typically ends up being sys.argv[1:])
    argv = None
    #: Default command line arguments.  Subclasses should create a new tuple
    #: that *includes* these.
    cl_arguments = app_cl_args

    #: extra arguments computed by the command-line loader
    extra_args = None

    # Private attributes
    _exiting = False
    _initialized = False

    # Class choices for things that will be instantiated at runtime.
    _CrashHandler = crashhandler.CrashHandler

    def __init__(self, argv=None, constructor_config=None, override_config=None):
        self.argv = sys.argv[1:] if argv is None else argv
        self.constructor_config = constructor_config
        self.override_config = override_config
        self.init_logger()

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

    def initialize(self):
        """Initialize the application.

        Loads all configuration information and sets all application state, but
        does not start any relevant processing (typically some kind of event
        loop).

        Once this method has been called, the application is flagged as
        initialized and the method becomes a no-op."""
        
        if self._initialized:
            return

        # The first part is protected with an 'attempt' wrapper, that will log
        # failures with the basic system traceback machinery.  Once our crash
        # handler is in place, we can let any subsequent exception propagate,
        # as our handler will log it with much better detail than the default.
        self.attempt(self.create_crash_handler)

        # Configuration phase
        # Default config (internally hardwired in application code)
        self.create_default_config()
        self.log_default_config()
        self.set_default_config_log_level()

        if self.override_config is None:
            # Command-line config
            self.pre_load_command_line_config()
            self.load_command_line_config()
            self.set_command_line_config_log_level()
            self.post_load_command_line_config()
            self.log_command_line_config()

        # Find resources needed for filesystem access, using information from
        # the above two
        self.find_ipython_dir()
        self.find_resources()
        self.find_config_file_name()
        self.find_config_file_paths()

        if self.override_config is None:
            # File-based config
            self.pre_load_file_config()
            self.load_file_config()
            self.set_file_config_log_level()
            self.post_load_file_config()
            self.log_file_config()

        # Merge all config objects into a single one the app can then use
        self.merge_configs()
        self.log_master_config()

        # Construction phase
        self.pre_construct()
        self.construct()
        self.post_construct()

        # Done, flag as such and
        self._initialized = True

    def start(self):
        """Start the application."""
        self.initialize()
        self.start_app()

    #-------------------------------------------------------------------------
    # Various stages of Application creation
    #-------------------------------------------------------------------------

    def create_crash_handler(self):
        """Create a crash handler, typically setting sys.excepthook to it."""
        self.crash_handler = self._CrashHandler(self, self.name)
        sys.excepthook = self.crash_handler

    def create_default_config(self):
        """Create defaults that can't be set elsewhere.

        For the most part, we try to set default in the class attributes
        of Components.  But, defaults the top-level Application (which is
        not a HasTraits or Component) are not set in this way.  Instead
        we set them here.  The Global section is for variables like this that
        don't belong to a particular component.
        """
        c = Config()
        c.Global.ipython_dir = get_ipython_dir()
        c.Global.log_level = self.log_level
        self.default_config = c

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
        return ArgParseConfigLoader(self.argv, self.cl_arguments,
                                    description=self.description, 
                                    version=release.version,
                                    usage=self.usage,
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

    def find_ipython_dir(self):
        """Set the IPython directory.

        This sets ``self.ipython_dir``, but the actual value that is passed to
        the application is kept in either ``self.default_config`` or
        ``self.command_line_config``.  This also adds ``self.ipython_dir`` to
        ``sys.path`` so config files there can be referenced by other config
        files.
        """

        try:
            self.ipython_dir = self.command_line_config.Global.ipython_dir
        except AttributeError:
            self.ipython_dir = self.default_config.Global.ipython_dir
        sys.path.append(os.path.abspath(self.ipython_dir))
        if not os.path.isdir(self.ipython_dir):
            os.makedirs(self.ipython_dir, mode=0777)
        self.log.debug("IPYTHON_DIR set to: %s" % self.ipython_dir)

    def find_resources(self):
        """Find other resources that need to be in place.

        Things like cluster directories need to be in place to find the
        config file.  These happen right after the IPython directory has
        been set.
        """
        pass

    def find_config_file_name(self):
        """Find the config file name for this application.

        This must set ``self.config_file_name`` to the filename of the
        config file to use (just the filename). The search paths for the
        config file are set in :meth:`find_config_file_paths` and then passed
        to the config file loader where they are resolved to an absolute path.

        If a profile has been set at the command line, this will resolve it.
        """

        try:
            self.config_file_name = self.command_line_config.Global.config_file
        except AttributeError:
            pass

        try:
            self.profile_name = self.command_line_config.Global.profile
        except AttributeError:
            pass
        else:
            name_parts = self.config_file_name.split('.')
            name_parts.insert(1, u'_' + self.profile_name + u'.')
            self.config_file_name = ''.join(name_parts)

    def find_config_file_paths(self):
        """Set the search paths for resolving the config file.

        This must set ``self.config_file_paths`` to a sequence of search
        paths to pass to the config file loader.
        """
        # Include our own profiles directory last, so that users can still find
        # our shipped copies of builtin profiles even if they don't have them
        # in their local ipython directory.
        prof_dir = os.path.join(get_ipython_package_dir(), 'config', 'profile')
        self.config_file_paths = (os.getcwd(), self.ipython_dir, prof_dir)

    def pre_load_file_config(self):
        """Do actions before the config file is loaded."""
        pass

    def load_file_config(self):
        """Load the config file.
        
        This tries to load the config file from disk.  If successful, the
        ``CONFIG_FILE`` config variable is set to the resolved config file
        location.  If not successful, an empty config is used.
        """
        self.log.debug("Attempting to load config file: %s" %
                       self.config_file_name)
        loader = PyFileConfigLoader(self.config_file_name,
                                    path=self.config_file_paths)
        try:
            self.file_config = loader.load_config()
            self.file_config.Global.config_file = loader.full_filename
        except IOError:
            # Only warn if the default config file was NOT being used.
            if not self.config_file_name==self.default_config_file_name:
                self.log.warn("Config file not found, skipping: %s" %
                               self.config_file_name, exc_info=True)
            self.file_config = Config()
        except:
            self.log.warn("Error loading config file: %s" %
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
            self.log.debug("Config file loaded: %s" %
                           self.file_config.Global.config_file)
            self.log.debug(repr(self.file_config))

    def merge_configs(self):
        """Merge the default, command line and file config objects."""
        config = Config()
        config._merge(self.default_config)
        if self.override_config is None:
            config._merge(self.file_config)
            config._merge(self.command_line_config)
            if self.constructor_config is not None:
                config._merge(self.constructor_config)
        else:
            config._merge(self.override_config)
        # XXX fperez - propose to Brian we rename master_config to simply
        # config, I think this is going to be heavily used in examples and
        # application code and the name is shorter/easier to find/remember.
        # For now, just alias it...
        self.master_config = config
        self.config = config

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
        if self._exiting:
            pass
        else:
            self.log.critical("Aborting application: %s" % self.name, exc_info=True)
            self._exiting = True
            sys.exit(1)

    def exit(self, exit_status=0):
        if self._exiting:
            pass
        else:
            self.log.debug("Exiting application: %s" % self.name)
            self._exiting = True
            sys.exit(exit_status)

    def attempt(self, func, action='abort'):
        try:
            func()
        except SystemExit:
            raise
        except:
            if action == 'abort':
                self.log.critical("Aborting application: %s" % self.name,
                                  exc_info=True)
                self.abort()
                raise
            elif action == 'exit':
                self.exit(0)
