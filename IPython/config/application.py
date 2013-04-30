# encoding: utf-8
"""
A base class for a configurable application.

Authors:

* Brian Granger
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

import logging
import os
import re
import sys
from copy import deepcopy
from collections import defaultdict

from IPython.external.decorator import decorator

from IPython.config.configurable import SingletonConfigurable
from IPython.config.loader import (
    KVArgParseConfigLoader, PyFileConfigLoader, Config, ArgumentError, ConfigFileNotFound,
)

from IPython.utils.traitlets import (
    Unicode, List, Enum, Dict, Instance, TraitError
)
from IPython.utils.importstring import import_item
from IPython.utils.text import indent, wrap_paragraphs, dedent

#-----------------------------------------------------------------------------
# function for re-wrapping a helpstring
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Descriptions for the various sections
#-----------------------------------------------------------------------------

# merge flags&aliases into options
option_description = """
Arguments that take values are actually convenience aliases to full
Configurables, whose aliases are listed on the help line. For more information
on full configurables, see '--help-all'.
""".strip() # trim newlines of front and back

keyvalue_description = """
Parameters are set from command-line arguments of the form:
`--Class.trait=value`.
This line is evaluated in Python, so simple expressions are allowed, e.g.::
`--C.a='range(3)'` For setting C.a=[0,1,2].
""".strip() # trim newlines of front and back

subcommand_description = """
Subcommands are launched as `{app} cmd [args]`. For information on using
subcommand 'cmd', do: `{app} cmd -h`.
""".strip().format(app=os.path.basename(sys.argv[0]))
# get running program name

#-----------------------------------------------------------------------------
# Application class
#-----------------------------------------------------------------------------

@decorator
def catch_config_error(method, app, *args, **kwargs):
    """Method decorator for catching invalid config (Trait/ArgumentErrors) during init.

    On a TraitError (generally caused by bad config), this will print the trait's
    message, and exit the app.
    
    For use on init methods, to prevent invoking excepthook on invalid input.
    """
    try:
        return method(app, *args, **kwargs)
    except (TraitError, ArgumentError) as e:
        app.print_description()
        app.print_help()
        app.print_examples()
        app.log.fatal("Bad config encountered during initialization:")
        app.log.fatal(str(e))
        app.log.debug("Config at the time: %s", app.config)
        app.exit(1)


class ApplicationError(Exception):
    pass


class Application(SingletonConfigurable):
    """A singleton application with full configuration support."""

    # The name of the application, will usually match the name of the command
    # line application
    name = Unicode(u'application')

    # The description of the application that is printed at the beginning
    # of the help.
    description = Unicode(u'This is an application.')
    # default section descriptions
    option_description = Unicode(option_description)
    keyvalue_description = Unicode(keyvalue_description)
    subcommand_description = Unicode(subcommand_description)

    # The usage and example string that goes at the end of the help string.
    examples = Unicode()

    # A sequence of Configurable subclasses whose config=True attributes will
    # be exposed at the command line.
    classes = List([])

    # The version string of this application.
    version = Unicode(u'0.0')

    # The log level for the application
    log_level = Enum((0,10,20,30,40,50,'DEBUG','INFO','WARN','ERROR','CRITICAL'),
                    default_value=logging.WARN,
                    config=True,
                    help="Set the log level by value or name.")
    def _log_level_changed(self, name, old, new):
        """Adjust the log level when log_level is set."""
        if isinstance(new, basestring):
            new = getattr(logging, new)
            self.log_level = new
        self.log.setLevel(new)
    
    log_format = Unicode("[%(name)s] %(message)s", config=True,
        help="The Logging format template",
    )
    def _log_format_changed(self, name, old, new):
        """Change the log formatter when log_format is set."""
        _log_handler = self.log.handlers[0]
        _log_formatter = logging.Formatter(new)
        _log_handler.setFormatter(_log_formatter)

    log = Instance(logging.Logger)
    def _log_default(self):
        """Start logging for this application.

        The default is to log to stderr using a StreamHandler, if no default
        handler already exists.  The log level starts at logging.WARN, but this
        can be adjusted by setting the ``log_level`` attribute.
        """
        log = logging.getLogger(self.__class__.__name__)
        log.setLevel(self.log_level)
        log.propagate = False
        _log = log # copied from Logger.hasHandlers() (new in Python 3.2)
        while _log:
            if _log.handlers:
                return log
            if not _log.propagate:
                break
            else:
                _log = _log.parent
        if sys.executable.endswith('pythonw.exe'):
            # this should really go to a file, but file-logging is only
            # hooked up in parallel applications
            _log_handler = logging.StreamHandler(open(os.devnull, 'w'))
        else:
            _log_handler = logging.StreamHandler()
        _log_formatter = logging.Formatter(self.log_format)
        _log_handler.setFormatter(_log_formatter)
        log.addHandler(_log_handler)
        return log

    # the alias map for configurables
    aliases = Dict({'log-level' : 'Application.log_level'})

    # flags for loading Configurables or store_const style flags
    # flags are loaded from this dict by '--key' flags
    # this must be a dict of two-tuples, the first element being the Config/dict
    # and the second being the help string for the flag
    flags = Dict()
    def _flags_changed(self, name, old, new):
        """ensure flags dict is valid"""
        for key,value in new.iteritems():
            assert len(value) == 2, "Bad flag: %r:%s"%(key,value)
            assert isinstance(value[0], (dict, Config)), "Bad flag: %r:%s"%(key,value)
            assert isinstance(value[1], basestring), "Bad flag: %r:%s"%(key,value)


    # subcommands for launching other applications
    # if this is not empty, this will be a parent Application
    # this must be a dict of two-tuples,
    # the first element being the application class/import string
    # and the second being the help string for the subcommand
    subcommands = Dict()
    # parse_command_line will initialize a subapp, if requested
    subapp = Instance('IPython.config.application.Application', allow_none=True)

    # extra command-line arguments that don't set config values
    extra_args = List(Unicode)


    def __init__(self, **kwargs):
        SingletonConfigurable.__init__(self, **kwargs)
        # Ensure my class is in self.classes, so my attributes appear in command line
        # options and config files.
        if self.__class__ not in self.classes:
            self.classes.insert(0, self.__class__)

    def _config_changed(self, name, old, new):
        SingletonConfigurable._config_changed(self, name, old, new)
        self.log.debug('Config changed:')
        self.log.debug(repr(new))

    @catch_config_error
    def initialize(self, argv=None):
        """Do the basic steps to configure me.

        Override in subclasses.
        """
        self.parse_command_line(argv)


    def start(self):
        """Start the app mainloop.

        Override in subclasses.
        """
        if self.subapp is not None:
            return self.subapp.start()

    def print_alias_help(self):
        """Print the alias part of the help."""
        if not self.aliases:
            return

        lines = []
        classdict = {}
        for cls in self.classes:
            # include all parents (up to, but excluding Configurable) in available names
            for c in cls.mro()[:-3]:
                classdict[c.__name__] = c

        for alias, longname in self.aliases.iteritems():
            classname, traitname = longname.split('.',1)
            cls = classdict[classname]

            trait = cls.class_traits(config=True)[traitname]
            help = cls.class_get_trait_help(trait).splitlines()
            # reformat first line
            help[0] = help[0].replace(longname, alias) + ' (%s)'%longname
            if len(alias) == 1:
                help[0] = help[0].replace('--%s='%alias, '-%s '%alias)
            lines.extend(help)
        # lines.append('')
        print os.linesep.join(lines)

    def print_flag_help(self):
        """Print the flag part of the help."""
        if not self.flags:
            return

        lines = []
        for m, (cfg,help) in self.flags.iteritems():
            prefix = '--' if len(m) > 1 else '-'
            lines.append(prefix+m)
            lines.append(indent(dedent(help.strip())))
        # lines.append('')
        print os.linesep.join(lines)

    def print_options(self):
        if not self.flags and not self.aliases:
            return
        lines = ['Options']
        lines.append('-'*len(lines[0]))
        lines.append('')
        for p in wrap_paragraphs(self.option_description):
            lines.append(p)
            lines.append('')
        print os.linesep.join(lines)
        self.print_flag_help()
        self.print_alias_help()
        print

    def print_subcommands(self):
        """Print the subcommand part of the help."""
        if not self.subcommands:
            return

        lines = ["Subcommands"]
        lines.append('-'*len(lines[0]))
        lines.append('')
        for p in wrap_paragraphs(self.subcommand_description):
            lines.append(p)
            lines.append('')
        for subc, (cls, help) in self.subcommands.iteritems():
            lines.append(subc)
            if help:
                lines.append(indent(dedent(help.strip())))
        lines.append('')
        print os.linesep.join(lines)

    def print_help(self, classes=False):
        """Print the help for each Configurable class in self.classes.

        If classes=False (the default), only flags and aliases are printed.
        """
        self.print_subcommands()
        self.print_options()

        if classes:
            if self.classes:
                print "Class parameters"
                print "----------------"
                print
                for p in wrap_paragraphs(self.keyvalue_description):
                    print p
                    print

            for cls in self.classes:
                cls.class_print_help()
                print
        else:
            print "To see all available configurables, use `--help-all`"
            print

    def print_description(self):
        """Print the application description."""
        for p in wrap_paragraphs(self.description):
            print p
            print

    def print_examples(self):
        """Print usage and examples.

        This usage string goes at the end of the command line help string
        and should contain examples of the application's usage.
        """
        if self.examples:
            print "Examples"
            print "--------"
            print
            print indent(dedent(self.examples.strip()))
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
        self.config = newconfig

    @catch_config_error
    def initialize_subcommand(self, subc, argv=None):
        """Initialize a subcommand with argv."""
        subapp,help = self.subcommands.get(subc)

        if isinstance(subapp, basestring):
            subapp = import_item(subapp)

        # clear existing instances
        self.__class__.clear_instance()
        # instantiate
        self.subapp = subapp.instance()
        # and initialize subapp
        self.subapp.initialize(argv)
    
    def flatten_flags(self):
        """flatten flags and aliases, so cl-args override as expected.
        
        This prevents issues such as an alias pointing to InteractiveShell,
        but a config file setting the same trait in TerminalInteraciveShell
        getting inappropriate priority over the command-line arg.

        Only aliases with exactly one descendent in the class list
        will be promoted.
        
        """
        # build a tree of classes in our list that inherit from a particular
        # it will be a dict by parent classname of classes in our list
        # that are descendents
        mro_tree = defaultdict(list)
        for cls in self.classes:
            clsname = cls.__name__
            for parent in cls.mro()[1:-3]:
                # exclude cls itself and Configurable,HasTraits,object
                mro_tree[parent.__name__].append(clsname)
        # flatten aliases, which have the form:
        # { 'alias' : 'Class.trait' }
        aliases = {}
        for alias, cls_trait in self.aliases.iteritems():
            cls,trait = cls_trait.split('.',1)
            children = mro_tree[cls]
            if len(children) == 1:
                # exactly one descendent, promote alias
                cls = children[0]
            aliases[alias] = '.'.join([cls,trait])
        
        # flatten flags, which are of the form:
        # { 'key' : ({'Cls' : {'trait' : value}}, 'help')}
        flags = {}
        for key, (flagdict, help) in self.flags.iteritems():
            newflag = {}
            for cls, subdict in flagdict.iteritems():
                children = mro_tree[cls]
                # exactly one descendent, promote flag section
                if len(children) == 1:
                    cls = children[0]
                newflag[cls] = subdict
            flags[key] = (newflag, help)
        return flags, aliases

    @catch_config_error
    def parse_command_line(self, argv=None):
        """Parse the command line arguments."""
        argv = sys.argv[1:] if argv is None else argv
        
        if argv and argv[0] == 'help':
            # turn `ipython help notebook` into `ipython notebook -h`
            argv = argv[1:] + ['-h']

        if self.subcommands and len(argv) > 0:
            # we have subcommands, and one may have been specified
            subc, subargv = argv[0], argv[1:]
            if re.match(r'^\w(\-?\w)*$', subc) and subc in self.subcommands:
                # it's a subcommand, and *not* a flag or class parameter
                return self.initialize_subcommand(subc, subargv)

        # Arguments after a '--' argument are for the script IPython may be
        # about to run, not IPython iteslf. For arguments parsed here (help and
        # version), we want to only search the arguments up to the first
        # occurrence of '--', which we're calling interpreted_argv.
        try:
            interpreted_argv = argv[:argv.index('--')]
        except ValueError:
            interpreted_argv = argv

        if any(x in interpreted_argv for x in ('-h', '--help-all', '--help')):
            self.print_description()
            self.print_help('--help-all' in interpreted_argv)
            self.print_examples()
            self.exit(0)

        if '--version' in interpreted_argv or '-V' in interpreted_argv:
            self.print_version()
            self.exit(0)
        
        # flatten flags&aliases, so cl-args get appropriate priority:
        flags,aliases = self.flatten_flags()

        loader = KVArgParseConfigLoader(argv=argv, aliases=aliases,
                                        flags=flags)
        config = loader.load_config()
        self.update_config(config)
        # store unparsed args in extra_args
        self.extra_args = loader.extra_args

    @catch_config_error
    def load_config_file(self, filename, path=None):
        """Load a .py based config file by filename and path."""
        loader = PyFileConfigLoader(filename, path=path)
        try:
            config = loader.load_config()
        except ConfigFileNotFound:
            # problem finding the file, raise
            raise
        except Exception:
            # try to get the full filename, but it will be empty in the
            # unlikely event that the error raised before filefind finished
            filename = loader.full_filename or filename
            # problem while running the file
            self.log.error("Exception while loading config file %s",
                            filename, exc_info=True)
        else:
            self.log.debug("Loaded config file: %s", loader.full_filename)
            self.update_config(config)

    def generate_config_file(self):
        """generate default config file from Configurables"""
        lines = ["# Configuration file for %s."%self.name]
        lines.append('')
        lines.append('c = get_config()')
        lines.append('')
        for cls in self.classes:
            lines.append(cls.class_config_section())
        return '\n'.join(lines)

    def exit(self, exit_status=0):
        self.log.debug("Exiting application: %s" % self.name)
        sys.exit(exit_status)

#-----------------------------------------------------------------------------
# utility functions, for convenience
#-----------------------------------------------------------------------------

def boolean_flag(name, configurable, set_help='', unset_help=''):
    """Helper for building basic --trait, --no-trait flags.

    Parameters
    ----------

    name : str
        The name of the flag.
    configurable : str
        The 'Class.trait' string of the trait to be set/unset with the flag
    set_help : unicode
        help string for --name flag
    unset_help : unicode
        help string for --no-name flag

    Returns
    -------

    cfg : dict
        A dict with two keys: 'name', and 'no-name', for setting and unsetting
        the trait, respectively.
    """
    # default helpstrings
    set_help = set_help or "set %s=True"%configurable
    unset_help = unset_help or "set %s=False"%configurable

    cls,trait = configurable.split('.')

    setter = {cls : {trait : True}}
    unsetter = {cls : {trait : False}}
    return {name : (setter, set_help), 'no-'+name : (unsetter, unset_help)}

