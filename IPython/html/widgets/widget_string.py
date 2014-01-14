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

from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, Bool, List, Int

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class HTMLWidget(DOMWidget):
    view_name = Unicode('HTMLView', sync=True)

    # Keys
    value = Unicode(help="String value", sync=True)
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)


class LatexWidget(HTMLWidget):
    view_name = Unicode('LatexView', sync=True)


class TextAreaWidget(HTMLWidget):
    view_name = Unicode('TextAreaView', sync=True)

    def scroll_to_bottom(self):
        self.send({"method": "scroll_to_bottom"})


class TextBoxWidget(HTMLWidget):
    view_name = Unicode('TextBoxView', sync=True)

    def __init__(self, **kwargs):
        super(TextBoxWidget, self).__init__(**kwargs)
        self._submission_callbacks = []        
        self.on_msg(self._handle_string_msg)

    def _handle_string_msg(self, content):
        """Handle a msg from the front-end

        Parameters
        ----------
        content: dict
            Content of the msg."""
        if 'event' in content and content['event'] == 'submit':
            for handler in self._submission_callbacks:
                handler(self)

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
            if callable(callback):
                argspec = inspect.getargspec(callback)
                nargs = len(argspec[0])

                # Bound methods have an additional 'self' argument
                if isinstance(callback, types.MethodType):
                    nargs -= 1

                # Call the callback
                if nargs == 0:
                    self._submission_callbacks.append(lambda sender: callback())
                elif nargs == 1:
                    self._submission_callbacks.append(callback)
                else:
                    raise TypeError('TextBoxWidget submit callback must ' \
                        'accept 0 or 1 arguments.')
