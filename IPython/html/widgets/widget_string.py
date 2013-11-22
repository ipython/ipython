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
    _keys = ['value', 'disabled', 'description']
    value = Unicode(help="String value")
    disabled = Bool(False, help="Enable or disable user changes")
    description = Unicode(help="Description of the value this widget represents")


    def __init__(self, **kwargs):
        super(StringWidget, self).__init__(**kwargs)
        self._submission_callbacks = []        
        self.on_msg(self._handle_string_msg)


    def scroll_to_bottom(self):
        self._comm.send({"method": "scroll_to_bottom"})


    def _handle_string_msg(self, content):
        """Handle a msg from the front-end

        Parameters
        ----------
        content: dict
            Content of the msg."""
        if 'event' in content and content['event'] == 'submit':
            self._handle_submit()


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


    def _handle_submit(self):
        """Handles when a string widget view is submitted."""
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
