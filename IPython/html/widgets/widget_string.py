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
from .widget import DOMWidget, CallbackDispatcher
from IPython.utils.traitlets import Unicode, Bool, List

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
        self._submission_callbacks = CallbackDispatcher(acceptable_nargs=[0, 1])
        self.on_msg(self._handle_string_msg)

    def _handle_string_msg(self, content):
        """Handle a msg from the front-end.

        Parameters
        ----------
        content: dict
            Content of the msg."""
        if 'event' in content and content['event'] == 'submit':
            self._submission_callbacks()
            self._submission_callbacks(self)

    def on_submit(self, callback, remove=False):
        """(Un)Register a callback to handle text submission.

        Triggered when the user clicks enter.

        Parameters
        callback: Method handle
            Function to be called when the text has been submitted.  Function
            can have two possible signatures:
            callback()
            callback(sender)
        remove: bool (optional)
            Whether or not to unregister the callback"""
        self._submission_callbacks.register_callback(callback, remove=remove)
