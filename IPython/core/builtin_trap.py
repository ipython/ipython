"""
A context manager for managing things injected into :mod:`__builtin__`.

Authors:

* Brian Granger
* Fernando Perez
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team.
#
#  Distributed under the terms of the BSD License.
#
#  Complete license in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import __builtin__

from IPython.config.configurable import Configurable

from IPython.utils.traitlets import Instance

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class __BuiltinUndefined(object): pass
BuiltinUndefined = __BuiltinUndefined()

class __HideBuiltin(object): pass
HideBuiltin = __HideBuiltin()


class BuiltinTrap(Configurable):

    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')

    def __init__(self, shell=None):
        super(BuiltinTrap, self).__init__(shell=shell, config=None)
        self._orig_builtins = {}
        # We define this to track if a single BuiltinTrap is nested.
        # Only turn off the trap when the outermost call to __exit__ is made.
        self._nested_level = 0
        self.shell = shell
        # builtins we always add - if set to HideBuiltin, they will just
        # be removed instead of being replaced by something else
        self.auto_builtins = {'exit': HideBuiltin,
                              'quit': HideBuiltin,
                              'get_ipython': self.shell.get_ipython,
                              }
        # Recursive reload function
        try:
            from IPython.lib import deepreload
            if self.shell.deep_reload:
                self.auto_builtins['reload'] = deepreload.reload
            else:
                self.auto_builtins['dreload']= deepreload.reload
        except ImportError:
            pass

    def __enter__(self):
        if self._nested_level == 0:
            self.activate()
        self._nested_level += 1
        # I return self, so callers can use add_builtin in a with clause.
        return self

    def __exit__(self, type, value, traceback):
        if self._nested_level == 1:
            self.deactivate()
        self._nested_level -= 1
        # Returning False will cause exceptions to propagate
        return False

    def add_builtin(self, key, value):
        """Add a builtin and save the original."""
        bdict = __builtin__.__dict__
        orig = bdict.get(key, BuiltinUndefined)
        if value is HideBuiltin:
            if orig is not BuiltinUndefined: #same as 'key in bdict'
                self._orig_builtins[key] = orig
                del bdict[key]
        else:
            self._orig_builtins[key] = orig
            bdict[key] = value

    def remove_builtin(self, key, orig):
        """Remove an added builtin and re-set the original."""
        if orig is BuiltinUndefined:
            del __builtin__.__dict__[key]
        else:
            __builtin__.__dict__[key] = orig

    def activate(self):
        """Store ipython references in the __builtin__ namespace."""

        add_builtin = self.add_builtin
        for name, func in self.auto_builtins.iteritems():
            add_builtin(name, func)

    def deactivate(self):
        """Remove any builtins which might have been added by add_builtins, or
        restore overwritten ones to their previous values."""
        remove_builtin = self.remove_builtin
        for key, val in self._orig_builtins.iteritems():
            remove_builtin(key, val)
        self._orig_builtins.clear()
        self._builtins_added = False
