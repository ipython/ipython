"""SelectionWidget class.  

Represents an enumeration using a widget.
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
from threading import Lock

from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, List, Bool, Any, Dict

#-----------------------------------------------------------------------------
# SelectionWidget
#-----------------------------------------------------------------------------
class _SelectionWidget(DOMWidget):
    value = Any(help="Selected value") 
    values = List(help="List of values the user can select")
    labels = List(help="""List of string representations for each value.  
        These string representations are used to display the values in the
        front-end.""", sync=True) # Only synced to the back-end.
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)

    _value = Unicode(sync=True) # Bi-directionally synced.

    def __init__(self, *pargs, **kwargs):
        """Constructor"""
        self.value_lock = Lock()
        self.on_trait_change(self._string_value_set, ['_value'])
        DOMWidget.__init__(self, *pargs, **kwargs)

    def _labels_changed(self, name=None, old=None, new=None):
        """Handles when the value_names Dict has been changed.

        This method sets the _reverse_value_names Dict to the inverse of the new
        value for the value_names Dict."""
        if len(new) != len(self.values):
            raise TypeError('Labels list must be the same size as the values list.')

    def _values_changed(self, name=None, old=None, new=None):
        """Handles when the value_names Dict has been changed.

        This method sets the _reverse_value_names Dict to the inverse of the new
        value for the value_names Dict."""
        if len(new) != len(self.labels):
            self.labels = [(self.labels[i] if i < len(self.labels) else str(v)) for i, v in enumerate(new)]

    def _value_changed(self, name, old, new):
        """Called when value has been changed"""
        if self.value_lock.acquire(False):
            try:
                # Make sure the value is in the list of values.
                if new in self.values:
                    # Set the string version of the value.
                    self._value = self.labels[self.values.index(new)]
                else:
                    raise TypeError('Value must be a value in the values list.')
            finally:
                self.value_lock.release()

    def _string_value_set(self, name, old, new):
        """Called when _value has been changed."""
        if self.value_lock.acquire(False):
            try:
                if new in self.labels:
                    self.value = self.values[self.labels.index(new)]
                else:
                    self.value = None
            finally:
                self.value_lock.release()


class ToggleButtonsWidget(_SelectionWidget):
    _view_name = Unicode('ToggleButtonsView', sync=True)


class DropdownWidget(_SelectionWidget):
    _view_name = Unicode('DropdownView', sync=True)


class RadioButtonsWidget(_SelectionWidget):
    _view_name = Unicode('RadioButtonsView', sync=True)
    

class SelectWidget(_SelectionWidget):
    _view_name = Unicode('SelectView', sync=True)
