#!/usr/bin/env python
# encoding: utf-8
"""
IPython's alias component

Authors:

* Brian Granger
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

import __builtin__
import keyword
import os
import re
import sys

from IPython.core.component import Component
from IPython.core.splitinput import split_user_input

from IPython.utils.traitlets import List
from IPython.utils.autoattr import auto_attr
from IPython.utils.warn import warn, error

#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------

# This is used as the pattern for calls to split_user_input.
shell_line_split = re.compile(r'^(\s*)(\S*\s*)(.*$)')

def default_aliases():
    # Make some aliases automatically
    # Prepare list of shell aliases to auto-define
    if os.name == 'posix':
        default_aliases = ('mkdir mkdir', 'rmdir rmdir',
                      'mv mv -i','rm rm -i','cp cp -i',
                      'cat cat','less less','clear clear',
                      # a better ls
                      'ls ls -F',
                      # long ls
                      'll ls -lF')
        # Extra ls aliases with color, which need special treatment on BSD
        # variants
        ls_extra = ( # color ls
                     'lc ls -F -o --color',
                     # ls normal files only
                     'lf ls -F -o --color %l | grep ^-',
                     # ls symbolic links
                     'lk ls -F -o --color %l | grep ^l',
                     # directories or links to directories,
                     'ldir ls -F -o --color %l | grep /$',
                     # things which are executable
                     'lx ls -F -o --color %l | grep ^-..x',
                     )
        # The BSDs don't ship GNU ls, so they don't understand the
        # --color switch out of the box
        if 'bsd' in sys.platform:
            ls_extra = ( # ls normal files only
                         'lf ls -lF | grep ^-',
                         # ls symbolic links
                         'lk ls -lF | grep ^l',
                         # directories or links to directories,
                         'ldir ls -lF | grep /$',
                         # things which are executable
                         'lx ls -lF | grep ^-..x',
                         )
        default_aliases = default_aliases + ls_extra
    elif os.name in ['nt','dos']:
        default_aliases = ('ls dir /on',
                      'ddir dir /ad /on', 'ldir dir /ad /on',
                      'mkdir mkdir','rmdir rmdir','echo echo',
                      'ren ren','cls cls','copy copy')
    else:
        default_aliases = ()
    return [s.split(None,1) for s in default_aliases]


class AliasError(Exception):
    pass


class InvalidAliasError(AliasError):
    pass


#-----------------------------------------------------------------------------
# Main AliasManager class
#-----------------------------------------------------------------------------


class AliasManager(Component):

    default_aliases = List(default_aliases(), config=True)
    user_aliases = List(default_value=[], config=True)

    def __init__(self, parent, config=None):
        super(AliasManager, self).__init__(parent, config=config)
        self.alias_table = {}
        self.exclude_aliases()
        self.init_aliases()

    @auto_attr
    def shell(self):
        return Component.get_instances(
            root=self.root,
            klass='IPython.core.iplib.InteractiveShell')[0]

    def __contains__(self, name):
        if name in self.alias_table:
            return True
        else:
            return False

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
        except AliasError, e:
            error("Invalid alias: %s" % e)

    def define_alias(self, name, cmd):
        """Define a new alias after validating it.

        This will raise an :exc:`AliasError` if there are validation
        problems.
        """
        nargs = self.validate_alias(name, cmd)
        self.alias_table[name] = (nargs, cmd)

    def undefine_alias(self, name):
        if self.alias_table.has_key(name):
            del self.alias_table[name]

    def validate_alias(self, name, cmd):
        """Validate an alias and return the its number of arguments."""
        if name in self.no_alias:
            raise InvalidAliasError("The name %s can't be aliased "
                                    "because it is a keyword or builtin." % name)
        if not (isinstance(cmd, basestring)):
            raise InvalidAliasError("An alias command must be a string, "
                                    "got: %r" % name)
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
        
        pre,fn,rest = split_user_input(line)
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
            pre,fn,rest = split_user_input(line, shell_line_split)
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
                line=l2
            else:
                break
                
        return line
