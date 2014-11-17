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
        self._flush()
        self.send({'method': 'push'})

    def __exit__(self, exception_type, exception_value, traceback):
        self._flush()
        self.send({'method': 'pop'})

    def _flush(self):
        sys.stdout.flush()
        sys.stderr.flush()
