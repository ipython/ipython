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

from .widget import Widget
from IPython.utils.traitlets import Unicode, Bool, Int

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class ButtonWidget(Widget):
    target_name = Unicode('ButtonWidgetModel')
    default_view_name = Unicode('ButtonView')

    # Keys
    _keys = ['clicks', 'description', 'disabled']
    clicks = Int(0, help="Number of times the button has been clicked.")
    description = Unicode('', help="Description of the button (label).")
    disabled = Bool(False, help="Enable or disable user changes.")
    
    _click_handlers = []


    def on_click(self, callback, remove=False):
        """Register a callback to execute when the button is clicked.

        Parameters
        ----------
        remove : bool (optional)
            Set to tru to remove the callback from the list of callbacks."""
        if remove:
            self._click_handlers.remove(callback)
        else:
            self._click_handlers.append(callback)


    def _clicks_changed(self, name, old, new):
        """Handles when the clicks property has been changed.  Fires on_click
        callbacks when appropriate."""
        if new > old:
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
