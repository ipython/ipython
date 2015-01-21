"""Output class.  

Represents a widget that can be used to display output within the widget area.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .widget import DOMWidget
import sys
from IPython.utils.traitlets import Unicode, List
from IPython.display import clear_output
from IPython.testing.skipdoctest import skip_doctest

@skip_doctest
class Output(DOMWidget):
    """Widget used as a context manager to display output.

    This widget can capture and display stdout, stderr, and rich output.  To use
    it, create an instance of it and display it.  Then use it as a context
    manager.  Any output produced while in it's context will be captured and
    displayed in it instead of the standard output area.

    Example
        from IPython.html import widgets
        from IPython.display import display
        out = widgets.Output()
        display(out)
        
        print('prints to output area')

        with out:
            print('prints to output widget')"""
    _view_name = Unicode('OutputView', sync=True)

    def clear_output(self, *pargs, **kwargs):
        with self:
            clear_output(*pargs, **kwargs)

    def __enter__(self):
        """Called upon entering output widget context manager."""
        self._flush()
        kernel = get_ipython().kernel
        session = kernel.session
        send = session.send
        self._original_send = send
        self._session = session

        def send_hook(stream, msg_or_type, *args, **kwargs):            
            if stream is kernel.iopub_socket and msg_or_type in ['clear_output', 'stream', 'display_data']:
                msg = {'type': msg_or_type, 'args': args, 'kwargs': kwargs}
                self.send(msg)
            else:
                send(stream, msg_or_type, *args, **kwargs)
                return

        session.send = send_hook

    def __exit__(self, exception_type, exception_value, traceback):
        """Called upon exiting output widget context manager."""
        self._flush()
        self._session.send = self._original_send

    def _flush(self):
        """Flush stdout and stderr buffers."""
        sys.stdout.flush()
        sys.stderr.flush()
