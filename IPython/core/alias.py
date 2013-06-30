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
        self.exclude_aliases()
        self.init_aliases()

    def __contains__(self, name):
        return name in self.alias_table

    @property
    def aliases(self):
        return [(item[0], item[1][1]) for item in self.alias_table.iteritems()]

    def exclude_aliases(self):
        # set of things NOT to alias (keywords, builtins and some magics)
        no_alias = set(['cd','popd','pushd','dhist','alias','unalias'])
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
        self.alias_table.clear()

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
        nargs = self.validate_alias(name, cmd)
        self.alias_table[name] = (nargs, cmd)

    def undefine_alias(self, name):
        if name in self.alias_table:
            del self.alias_table[name]

    def validate_alias(self, name, cmd):
        """Validate an alias and return the its number of arguments."""
        if name in self.no_alias:
            raise InvalidAliasError("The name %s can't be aliased "
                                    "because it is a keyword or builtin." % name)
        if not (isinstance(cmd, basestring)):
            raise InvalidAliasError("An alias command must be a string, "
                                    "got: %r" % cmd)
        nargs = cmd.count('%s')
        if nargs>0 and cmd.find('%l')>=0:
            raise InvalidAliasError('The %s and %l specifiers are mutually '
                                    'exclusive in alias definitions.')
        return nargs

    def call_alias(self, alias, rest=''):
        """Call an alias given its name and the rest of the line."""
        cmd = self.transform_alias(alias, rest)
        try:
            self.shell.system(cmd)
        except:
            self.shell.showtraceback()

    def transform_alias(self, alias,rest=''):
        """Transform alias to system command string."""
        nargs, cmd = self.alias_table[alias]

        if ' ' in cmd and os.path.isfile(cmd):
            cmd = '"%s"' % cmd

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
        return cmd

    def expand_alias(self, line):
        """ Expand an alias in the command line

        Returns the provided command line, possibly with the first word
        (command) translated according to alias expansion rules.

        [ipython]|16> _ip.expand_aliases("np myfile.txt")
                 <16> 'q:/opt/np/notepad++.exe myfile.txt'
        """

        pre,_,fn,rest = split_user_input(line)
        res = pre + self.expand_aliases(fn, rest)
        return res

    def expand_aliases(self, fn, rest):
        """Expand multiple levels of aliases:

        if:

        alias foo bar /tmp
        alias baz foo

        then:

        baz huhhahhei -> bar /tmp huhhahhei
        """
        line = fn + " " + rest

        done = set()
        while 1:
            pre,_,fn,rest = split_user_input(line, shell_line_split)
            if fn in self.alias_table:
                if fn in done:
                    warn("Cyclic alias definition, repeated '%s'" % fn)
                    return ""
                done.add(fn)

                l2 = self.transform_alias(fn, rest)
                if l2 == line:
                    break
                # ls -> ls -F should not recurse forever
                if l2.split(None,1)[0] == line.split(None,1)[0]:
                    line = l2
                    break
                line = l2
            else:
                break

        return line
