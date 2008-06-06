# encoding: utf-8

"""Manager for replacing sys.displayhook()."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

# Standard library imports.
import sys



class DisplayTrap(object):
    """ Object to trap and format objects passing through sys.displayhook().

    This trap maintains two lists of callables: formatters and callbacks. The
    formatters take the *last* object that has gone through since the trap was
    set and returns a string representation. Callbacks are executed on *every*
    object that passes through the displayhook and does not return anything.
    """

    def __init__(self, formatters=None, callbacks=None):
        # A list of formatters to apply. Each should be an instance conforming
        # to the IDisplayFormatter interface.
        if formatters is None:
            formatters = []
        self.formatters = formatters

        # A list of callables, each of which should be executed *every* time an
        # object passes through sys.displayhook().
        if callbacks is None:
            callbacks = []
        self.callbacks = callbacks

        # The last object to pass through the displayhook.
        self.obj = None

        # The previous hook before we replace it.
        self.old_hook = None
        
    def hook(self, obj):
        """ This method actually implements the hook.
        """

        # Run through the list of callbacks and trigger all of them.
        for callback in self.callbacks:
            callback(obj)

        # Store the object for formatting.
        self.obj = obj

    def set(self):
        """ Set the hook.
        """

        if sys.displayhook is not self.hook:
            self.old_hook = sys.displayhook
            sys.displayhook = self.hook

    def unset(self):
        """ Unset the hook.
        """

        sys.displayhook = self.old_hook

    def clear(self):
        """ Reset the stored object.
        """

        self.obj = None

    def add_to_message(self, message):
        """ Add the formatted display of the objects to the message dictionary
        being returned from the interpreter to its listeners.
        """

        # If there was no displayed object (or simply None), then don't add
        # anything.
        if self.obj is None:
            return

        # Go through the list of formatters and let them add their formatting.
        display = {}
        for formatter in self.formatters:
            representation = formatter(self.obj)
            if representation is not None:
                display[formatter.identifier] = representation

        message['display'] = display

