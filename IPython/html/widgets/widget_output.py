"""Output class.  

Represents a widget that can be used to display output within the widget area.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .widget import DOMWidget
import sys
from IPython.utils.traitlets import Unicode, List
from IPython.display import clear_output

class Output(DOMWidget):
    """Displays multiple widgets in a group."""
    _view_name = Unicode('OutputView', sync=True)

    def clear_output(self, *pargs, **kwargs):
        with self:
            clear_output(*pargs, **kwargs)

    def __enter__(self):
        self._flush()
        self.send({'method': 'push'})

    def __exit__(self, exception_type, exception_value, traceback):
        self._flush()
        self.send({'method': 'pop'})

    def _flush(self):
        sys.stdout.flush()
        sys.stderr.flush()
