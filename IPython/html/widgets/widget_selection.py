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
    value_names = Dict(help="""List of string representations for each value.  
        These string representations are used to display the values in the
        front-end.""")
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)

    _value = Unicode(sync=True) # Bi-directionally synced.
    _values = List(sync=True) # Only back-end to front-end synced.
    _reverse_value_names = Dict()

    def __init__(self, *pargs, **kwargs):
        """Constructor"""
        DOMWidget.__init__(self, *pargs, **kwargs)
        self.value_lock = Lock()
        self.on_trait_change(self._string_value_set, ['_value'])

    def _value_names_changed(self, name=None, old=None, new=None):
        """Handles when the value_names Dict has been changed.

        This method sets the _reverse_value_names Dict to the inverse of the new
        value for the value_names Dict."""
        self._reverse_value_names = {v:k for k, v in self.value_names.items()}
        self._values_changed()

    def _values_changed(self, name=None, old=None, new=None):
        """Called when values has been changed"""
        self._values = [self._get_string_repr(v) for v in self.values]

    def _value_changed(self, name, old, new):
        """Called when value has been changed"""
        if self.value_lock.acquire(False):
            try:
                # Make sure the value is in the list of values.
                if new in self.values:
                    # Set the string version of the value.
                    self._value = self._get_string_repr(new)
                else:
                    raise TypeError('Value must be a value in the values list.')
            finally:
                self.value_lock.release()

    def _get_string_repr(self, value):
        """Get the string repr of a value"""
        if value not in self.value_names:
            self.value_names[value] = str(value)
            self._value_names_changed()
        return self.value_names[value]

    def _string_value_set(self, name, old, new):
        """Called when _value has been changed."""
        if self.value_lock.acquire(False):
            try:
                if new in self._reverse_value_names:
                    self.value = self._reverse_value_names[new]
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
    

class ListBoxWidget(_SelectionWidget):
    _view_name = Unicode('ListBoxView', sync=True)
