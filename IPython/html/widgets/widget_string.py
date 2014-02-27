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
from IPython.utils.traitlets import Unicode, Bool

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class _StringWidget(DOMWidget):
    value = Unicode(help="String value", sync=True)
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)


class HTMLWidget(_StringWidget):
    _view_name = Unicode('HTMLView', sync=True)


class LatexWidget(_StringWidget):
    _view_name = Unicode('LatexView', sync=True)


class TextareaWidget(_StringWidget):
    _view_name = Unicode('TextareaView', sync=True)

    def scroll_to_bottom(self):
        self.send({"method": "scroll_to_bottom"})


class TextWidget(_StringWidget):
    _view_name = Unicode('TextView', sync=True)

    def __init__(self, **kwargs):
        super(TextWidget, self).__init__(**kwargs)
        self._submission_callbacks = CallbackDispatcher()
        self.on_msg(self._handle_string_msg)

    def _handle_string_msg(self, _, content):
        """Handle a msg from the front-end.

        Parameters
        ----------
        content: dict
            Content of the msg."""
        if content.get('event', '') == 'submit':
            self._submission_callbacks(self)

    def on_submit(self, callback, remove=False):
        """(Un)Register a callback to handle text submission.

        Triggered when the user clicks enter.

        Parameters
        ----------
        callback: callable
            Will be called with exactly one argument: the Widget instance
        remove: bool (optional)
            Whether to unregister the callback"""
        self._submission_callbacks.register_callback(callback, remove=remove)
