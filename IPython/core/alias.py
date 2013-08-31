# encoding: utf-8
"""
System command aliases.

Authors:

* Fernando Perez
* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import __builtin__
import keyword
import os
import re
import sys

from IPython.config.configurable import Configurable
from IPython.core.splitinput import split_user_input

from IPython.utils.traitlets import List, Instance
from IPython.utils.warn import warn, error

#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------

# This is used as the pattern for calls to split_user_input.
shell_line_split = re.compile(r'^(\s*)()(\S+)(.*$)')

def default_aliases():
    """Return list of shell aliases to auto-define.
    """
    # Note: the aliases defined here should be safe to use on a kernel
    # regardless of what frontend it is attached to.  Frontends that use a
    # kernel in-process can define additional aliases that will only work in
    # their case.  For example, things like 'less' or 'clear' that manipulate
    # the terminal should NOT be declared here, as they will only work if the
    # kernel is running inside a true terminal, and not over the network.

    if os.name == 'posix':
        default_aliases = [('mkdir', 'mkdir'), ('rmdir', 'rmdir'),
                           ('mv', 'mv -i'), ('rm', 'rm -i'), ('cp', 'cp -i'),
                           ('cat', 'cat'),
                           ]
        # Useful set of ls aliases.  The GNU and BSD options are a little
        # different, so we make aliases that provide as similar as possible
        # behavior in ipython, by passing the right flags for each platform
        if sys.platform.startswith('linux'):
            ls_aliases = [('ls', 'ls -F --color'),
                          # long ls
                          ('ll', 'ls -F -o --color'),
                          # ls normal files only
                          ('lf', 'ls -F -o --color %l | grep ^-'),
                          # ls symbolic links
                          ('lk', 'ls -F -o --color %l | grep ^l'),
                          # directories or links to directories,
                          ('ldir', 'ls -F -o --color %l | grep /$'),
                          # things which are executable
                          ('lx', 'ls -F -o --color %l | grep ^-..x'),
                          ]
        else:
            # BSD, OSX, etc.
            ls_aliases = [('ls', 'ls -F -G'),
                          # long ls
                          ('ll', 'ls -F -l -G'),
                          # ls normal files only
                          ('lf', 'ls -F -l -G %l | grep ^-'),
                          # ls symbolic links
                          ('lk', 'ls -F -l -G %l | grep ^l'),
                          # directories or links to directories,
                          ('ldir', 'ls -F -G -l %l | grep /$'),
                          # things which are executable
                          ('lx', 'ls -F -l -G %l | grep ^-..x'),
                          ]
        default_aliases = default_aliases + ls_aliases
    elif os.name in ['nt', 'dos']:
        default_aliases = [('ls', 'dir /on'),
                           ('ddir', 'dir /ad /on'), ('ldir', 'dir /ad /on'),
                           ('mkdir', 'mkdir'), ('rmdir', 'rmdir'),
                           ('echo', 'echo'), ('ren', 'ren'), ('copy', 'copy'),
                           ]
    else:
        default_aliases = []

    return default_aliases


class AliasError(Exception):
    pass


class InvalidAliasError(AliasError):
    pass

class AliasCaller(object):
    def __init__(self, shell, cmd):
        self.shell = shell
        self.cmd = cmd
        self.nargs = cmd.count('%s')
        if (self.nargs > 0) and (cmd.find('%l') >= 0):
            raise InvalidAliasError('The %s and %l specifiers are mutually '
                                    'exclusive in alias definitions.')        
        
    def __call__(self, rest=''):
        cmd = self.cmd
        nargs = self.nargs
        # Expand the %l special to be the user's input line
        if cmd.find('%l') >= 0:
            cmd = cmd.replace('%l', rest)
            rest = ''
        if nargs==0:
            # Simple, argument-less aliases
            cmd = '%s %s' % (cmd, rest)
        else:
            # Handle aliases with positional arguments
            args = rest.split(None, nargs)
            if len(args) < nargs:
                raise AliasError('Alias <%s> requires %s arguments, %s given.' %
                      (alias, nargs, len(args)))
            cmd = '%s %s' % (cmd % tuple(args[:nargs]),' '.join(args[nargs:]))
        
        self.shell.system(cmd)

#-----------------------------------------------------------------------------
# Main AliasManager class
#-----------------------------------------------------------------------------

class AliasManager(Configurable):

    default_aliases = List(default_aliases(), config=True)
    user_aliases = List(default_value=[], config=True)
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')

    def __init__(self, shell=None, **kwargs):
        super(AliasManager, self).__init__(shell=shell, **kwargs)
        self.alias_table = {}
        self.init_exclusions()
        self.init_aliases()

    @property
    def aliases(self):
        linemagics = self.shell.magics_manager.magics['line']
        return [(n, func.cmd) for (n, func) in linemagics.items()
                            if isinstance(func, AliasCaller)]

    def init_exclusions(self):
        # set of things NOT to alias (keywords, builtins and some magics)
        no_alias = {'cd','popd','pushd','dhist','alias','unalias'}
        no_alias.update(set(keyword.kwlist))
        no_alias.update(set(__builtin__.__dict__.keys()))
        self.no_alias = no_alias

    def init_aliases(self):
        # Load default aliases
        for name, cmd in self.default_aliases:
            self.soft_define_alias(name, cmd)

        # Load user aliases
        for name, cmd in self.user_aliases:
            self.soft_define_alias(name, cmd)
    
    def clear_aliases(self):
        for name, cmd in self.aliases:
            self.undefine_alias(name)

    def soft_define_alias(self, name, cmd):
        """Define an alias, but don't raise on an AliasError."""
        try:
            self.define_alias(name, cmd)
        except AliasError as e:
            error("Invalid alias: %s" % e)

    def define_alias(self, name, cmd):
        """Define a new alias after validating it.

        This will raise an :exc:`AliasError` if there are validation
        problems.
        """
        self.validate_alias(name, cmd)
        caller = AliasCaller(shell=self.shell, cmd=cmd)
        self.shell.magics_manager.register_function(caller, magic_kind='line',
                                                    magic_name=name)

    def undefine_alias(self, name):
        linemagics = self.shell.magics_manager.magics['line']
        caller = linemagics.get(name, None)
        if isinstance(caller, AliasCaller):
            del linemagics[name]
        else:
            raise ValueError('%s is not an alias' % name)

    def validate_alias(self, name, cmd):
        """Validate an alias and return the its number of arguments."""
        if name in self.no_alias:
            raise InvalidAliasError("The name %s can't be aliased "
                                    "because it is a keyword or builtin." % name)
        if not (isinstance(cmd, basestring)):
            raise InvalidAliasError("An alias command must be a string, "
                                    "got: %r" % cmd)
        return True
    
    def retrieve_alias(self, name):
        """Retrieve the command to which an alias expands."""
        caller = self.shell.magics_manager.magics['line'].get(name, None)
        if isinstance(caller, AliasCaller):
            return caller.cmd
        else:
            raise ValueError('%s is not an alias' % name)
