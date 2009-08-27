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

    def __enter__(self):
        self.set()
        return self

    def __exit__(self, type, value, traceback):
        self.unset()
        return True

    def set(self):
        """Set the hook."""
        if sys.displayhook is not self.hook:
            self.old_hook = sys.displayhook
            sys.displayhook = self.hook

    def unset(self):
        """Unset the hook."""
        sys.displayhook = self.old_hook

