"""ButtonWidget class.  

Represents a button in the frontend using a widget.  Allows user to listen for
click events on the button and trigger backend code when the clicks are fired.
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

from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, Bool, Int

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class ButtonWidget(DOMWidget):
    target_name = Unicode('ButtonWidgetModel')
    view_name = Unicode('ButtonView')

    # Keys
    description = Unicode('', help="Description of the button (label).", sync=True)
    disabled = Bool(False, help="Enable or disable user changes.", sync=True)
    

    def __init__(self, **kwargs):
        super(ButtonWidget, self).__init__(**kwargs)
        
        self._click_handlers = []
        self.on_msg(self._handle_button_msg)


    def on_click(self, callback, remove=False):
        """Register a callback to execute when the button is clicked.  The
        callback can either accept no parameters or one sender parameter:
        - callback()
        - callback(sender)
        If the callback has a sender parameter, the ButtonWidget instance that
        called the callback will be passed into the method as the sender.

        Parameters
        ----------
        remove : bool (optional)
            Set to true to remove the callback from the list of callbacks."""
        if remove:
            self._click_handlers.remove(callback)
        elif not callback in self._click_handlers:
            self._click_handlers.append(callback)


    def _handle_button_msg(self, content):
        """Handle a msg from the front-end

        Parameters
        ----------
        content: dict
            Content of the msg."""
        if 'event' in content and content['event'] == 'click':
            self._handle_click()


    def _handle_click(self):
        """Handles when the button has been clicked.  Fires on_click
        callbacks when appropriate."""
        
        for handler in self._click_handlers:
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
                    raise TypeError('ButtonWidget click callback must ' \
                        'accept 0 or 1 arguments.')
        
