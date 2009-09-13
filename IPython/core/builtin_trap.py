#!/usr/bin/env python
# encoding: utf-8
"""
A context manager for managing things injected into :mod:`__builtin__`.

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

from IPython.core.component import Component
from IPython.core.quitter import Quitter

from IPython.utils.autoattr import auto_attr

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------


class BuiltinUndefined(object): pass
BuiltinUndefined = BuiltinUndefined()


class BuiltinTrap(Component):

    def __init__(self, parent):
        super(BuiltinTrap, self).__init__(parent, None, None)
        self._orig_builtins = {}
        # We define this to track if a single BuiltinTrap is nested.
        # Only turn off the trap when the outermost call to __exit__ is made.
        self._nested_level = 0

    @auto_attr
    def shell(self):
        return Component.get_instances(
            root=self.root,
            klass='IPython.core.iplib.InteractiveShell')[0]

    def __enter__(self):
        if self._nested_level == 0:
            self.set()
        self._nested_level += 1
        # I return self, so callers can use add_builtin in a with clause.
        return self

    def __exit__(self, type, value, traceback):
        if self._nested_level == 1:
            self.unset()
        self._nested_level -= 1
        return True

    def add_builtin(self, key, value):
        """Add a builtin and save the original."""
        orig = __builtin__.__dict__.get(key, BuiltinUndefined)
        self._orig_builtins[key] = orig
        __builtin__.__dict__[key] = value

    def remove_builtin(self, key):
        """Remove an added builtin and re-set the original."""
        try:
            orig = self._orig_builtins.pop(key)
        except KeyError:
            pass
        else:
            if orig is BuiltinUndefined:
                del __builtin__.__dict__[key]
            else:
                __builtin__.__dict__[key] = orig

    def set(self):
        """Store ipython references in the __builtin__ namespace."""
        self.add_builtin('exit', Quitter(self.shell, 'exit'))
        self.add_builtin('quit', Quitter(self.shell, 'quit'))

        # Recursive reload function
        try:
            from IPython.lib import deepreload
            if self.shell.deep_reload:
                self.add_builtin('reload', deepreload.reload)
            else:
                self.add_builtin('dreload', deepreload.reload)
            del deepreload
        except ImportError:
            pass

        # Keep in the builtins a flag for when IPython is active.  We set it
        # with setdefault so that multiple nested IPythons don't clobber one
        # another.  Each will increase its value by one upon being activated,
        # which also gives us a way to determine the nesting level.
        __builtin__.__dict__.setdefault('__IPYTHON__active',0)

    def unset(self):
        """Remove any builtins which might have been added by add_builtins, or
        restore overwritten ones to their previous values."""
        for key in self._orig_builtins.keys():
            self.remove_builtin(key)
        self._orig_builtins.clear()
        self._builtins_added = False
        try:
            del __builtin__.__dict__['__IPYTHON__active']
        except KeyError:
            pass
