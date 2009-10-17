#!/usr/bin/env python
# encoding: utf-8
"""
A context manager for handling sys.displayhook.

Authors:

* Robert Kern
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

import sys

from IPython.core.component import Component

from IPython.utils.autoattr import auto_attr

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------


class DisplayTrap(Component):
    """Object to manage sys.displayhook.

    This came from IPython.core.kernel.display_hook, but is simplified
    (no callbacks or formatters) until more of the core is refactored.
    """

    def __init__(self, parent, hook):
        super(DisplayTrap, self).__init__(parent, None, None)
        self.hook = hook
        self.old_hook = None
        # We define this to track if a single BuiltinTrap is nested.
        # Only turn off the trap when the outermost call to __exit__ is made.
        self._nested_level = 0

    # @auto_attr
    # def shell(self):
    #     return Component.get_instances(
    #         root=self.root,
    #         klass='IPython.core.iplib.InteractiveShell')[0]

    def __enter__(self):
        if self._nested_level == 0:
            self.set()
        self._nested_level += 1
        return self

    def __exit__(self, type, value, traceback):
        if self._nested_level == 1:
            self.unset()
        self._nested_level -= 1
        # Returning False will cause exceptions to propagate
        return False

    def set(self):
        """Set the hook."""
        if sys.displayhook is not self.hook:
            self.old_hook = sys.displayhook
            sys.displayhook = self.hook

    def unset(self):
        """Unset the hook."""
        sys.displayhook = self.old_hook

