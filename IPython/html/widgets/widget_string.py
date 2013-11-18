"""StringWidget class.  

Represents a unicode string using a widget.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import inspect
import types

from .widget import Widget
from IPython.utils.traitlets import Unicode, Bool, List, Int

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class StringWidget(Widget):
    target_name = Unicode('StringWidgetModel')
    default_view_name = Unicode('TextBoxView')

    # Keys
    _keys = ['value', 'disabled', 'description', 'submits']
    value = Unicode(help="String value")
    disabled = Bool(False, help="Enable or disable user changes")
    description = Unicode(help="Description of the value this widget represents")
    submits = Int(0, help="Used to capture and fire submission ")


    def __init__(self, **kwargs):
        super(StringWidget, self).__init__(**kwargs)
        self._submission_callbacks = []


    def on_submit(self, callback, remove=False):
        """Register a callback to handle text submission (triggered when the 
        user clicks enter).

        Parameters
        callback: Method handle
            Function to be called when the text has been submitted.  Function
            can have two possible signatures:
            callback()
            callback(sender)
        remove: bool (optional)
            Whether or not to unregister the callback"""
        if remove and callback in self._submission_callbacks:
            self._submission_callbacks.remove(callback)
        elif not remove and not callback in self._submission_callbacks:
            self._submission_callbacks.append(callback)


    def _submits_changed(self, name, old_value, new_value):
        """Handles when a string widget view is submitted."""
        if new_value > old_value:
            for handler in self._submission_callbacks:
                if callable(handler):
                    argspec = inspect.getargspec(handler)
                    nargs = len(argspec[0])

                    # Bound methods have an additional 'self' argument
                    if isinstance(handler, types.MethodType):
                        nargs -= 1

                    # Call the callback
                    if nargs == 0:
                        handler()
                    elif nargs == 1:
                        handler(self)
                    else:
                        raise TypeError('StringWidget submit callback must ' \
                            'accept 0 or 1 arguments.')
