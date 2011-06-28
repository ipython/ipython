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

from IPython.config.configurable import SingletonConfigurable
from IPython.config.loader import (
    KeyValueConfigLoader, PyFileConfigLoader, Config, ArgumentError
)

from IPython.utils.traitlets import (
    Unicode, List, Int, Enum, Dict, Instance, TraitError
)
from IPython.utils.importstring import import_item
from IPython.utils.text import indent, wrap_paragraphs, dedent

#-----------------------------------------------------------------------------
# function for re-wrapping a helpstring
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Descriptions for the various sections
#-----------------------------------------------------------------------------

flag_description = """
Flags are command-line arguments passed as '--<flag>'.
These take no parameters, unlike regular key-value arguments.
They are typically used for setting boolean flags, or enabling
modes that involve setting multiple options together.

Flags *always* begin with '--', never just one '-'.
""".strip() # trim newlines of front and back

alias_description = """
These are commonly set parameters, given abbreviated aliases for convenience.
They are set in the same `name=value` way as class parameters, where
<name> is replaced by the real parameter for which it is an alias.
""".strip() # trim newlines of front and back

keyvalue_description = """
Parameters are set from command-line arguments of the form:
`Class.trait=value`.  Parameters will *never* be prefixed with '-'.
This line is evaluated in Python, so simple expressions are allowed, e.g.
    `C.a='range(3)'`   For setting C.a=[0,1,2]
""".strip() # trim newlines of front and back

#-----------------------------------------------------------------------------
# Application class
#-----------------------------------------------------------------------------


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
    flag_description = Unicode(flag_description)
    alias_description = Unicode(alias_description)
    keyvalue_description = Unicode(keyvalue_description)
    

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
    
    # the alias map for configurables
    aliases = Dict(dict(log_level='Application.log_level'))
    
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
        # Add my class to self.classes so my attributes appear in command line
        # options.
        self.classes.insert(0, self.__class__)
        
        self.init_logging()

    def _config_changed(self, name, old, new):
        SingletonConfigurable._config_changed(self, name, old, new)
        self.log.debug('Config changed:')
        self.log.debug(repr(new))

    def init_logging(self):
        """Start logging for this application.

        The default is to log to stdout using a StreaHandler. The log level
        starts at loggin.WARN, but this can be adjusted by setting the 
        ``log_level`` attribute.
        """
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(self.log_level)
        if sys.executable.endswith('pythonw.exe'):
            # this should really go to a file, but file-logging is only
            # hooked up in parallel applications
            self._log_handler = logging.StreamHandler(open(os.devnull, 'w'))
        else:
            self._log_handler = logging.StreamHandler()
        self._log_formatter = logging.Formatter("[%(name)s] %(message)s")
        self._log_handler.setFormatter(self._log_formatter)
        self.log.addHandler(self._log_handler)
    
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
        
        lines = ['Aliases']
        lines.append('-'*len(lines[0]))
        lines.append('')
        for p in wrap_paragraphs(self.alias_description):
            lines.append(p)
            lines.append('')
        
        classdict = {}
        for cls in self.classes:
            # include all parents (up to, but excluding Configurable) in available names
            for c in cls.mro()[:-3]:
                classdict[c.__name__] = c
        
        for alias, longname in self.aliases.iteritems():
            classname, traitname = longname.split('.',1)
            cls = classdict[classname]
            
            trait = cls.class_traits(config=True)[traitname]
            help = cls.class_get_trait_help(trait)
            help = help.replace(longname, "%s (%s)"%(alias, longname), 1)
            lines.append(help)
        lines.append('')
        print '\n'.join(lines)
    
    def print_flag_help(self):
        """Print the flag part of the help."""
        if not self.flags:
            return
        
        lines = ['Flags']
        lines.append('-'*len(lines[0]))
        lines.append('')
        for p in wrap_paragraphs(self.flag_description):
            lines.append(p)
            lines.append('')
        
        for m, (cfg,help) in self.flags.iteritems():
            lines.append('--'+m)
            lines.append(indent(dedent(help.strip())))
        lines.append('')
        print '\n'.join(lines)
    
    def print_subcommands(self):
        """Print the subcommand part of the help."""
        if not self.subcommands:
            return
        
        lines = ["Subcommands"]
        lines.append('-'*len(lines[0]))
        for subc, (cls,help) in self.subcommands.iteritems():
            lines.append("%s : %s"%(subc, cls))
            if help:
                lines.append(indent(dedent(help.strip())))
        lines.append('')
        print '\n'.join(lines)
    
    def print_help(self, classes=False):
        """Print the help for each Configurable class in self.classes.
        
        If classes=False (the default), only flags and aliases are printed.
        """
        self.print_subcommands()
        self.print_flag_help()
        self.print_alias_help()
        
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
        
    def parse_command_line(self, argv=None):
        """Parse the command line arguments."""
        argv = sys.argv[1:] if argv is None else argv

        if self.subcommands and len(argv) > 0:
            # we have subcommands, and one may have been specified
            subc, subargv = argv[0], argv[1:]
            if re.match(r'^\w(\-?\w)*$', subc) and subc in self.subcommands:
                # it's a subcommand, and *not* a flag or class parameter
                return self.initialize_subcommand(subc, subargv)
            
        if '-h' in argv or '--help' in argv or '--help-all' in argv:
            self.print_description()
            self.print_help('--help-all' in argv)
            self.exit(0)

        if '--version' in argv:
            self.print_version()
            self.exit(0)
        
        loader = KeyValueConfigLoader(argv=argv, aliases=self.aliases,
                                        flags=self.flags)
        try:
            config = loader.load_config()
            self.update_config(config)
        except (TraitError, ArgumentError) as e:
            self.print_description()
            self.print_help()
            self.log.fatal(str(e))
            self.exit(1)
        # store unparsed args in extra_args
        self.extra_args = loader.extra_args

    def load_config_file(self, filename, path=None):
        """Load a .py based config file by filename and path."""
        loader = PyFileConfigLoader(filename, path=path)
        config = loader.load_config()
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

