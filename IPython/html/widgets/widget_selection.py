"""SelectionWidget classes.

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

from collections import OrderedDict
from threading import Lock

from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, List, Bool, Any, Dict, TraitError
from IPython.utils.py3compat import unicode_type

#-----------------------------------------------------------------------------
# SelectionWidget
#-----------------------------------------------------------------------------
class _SelectionWidget(DOMWidget):
    """Base class for Selection widgets
    
    ``values`` can be specified as a list or dict. If given as a list,
    it will be transformed to a dict of the form ``{str(value):value}``.
    """
    
    value = Any(help="Selected value")
    values = Dict(help="""Dictionary of {name: value} the user can select.
    
    The keys of this dictionary are the strings that will be displayed in the UI,
    representing the actual Python choices.
    
    The keys of this dictionary are also available as value_names.
    """)
    value_name = Unicode(help="The name of the selected value", sync=True)
    value_names = List(Unicode, help="""Read-only list of names for each value.
        
        If values is specified as a list, this is the string representation of each element.
        Otherwise, it is the keys of the values dictionary.
        
        These strings are used to display the choices in the front-end.""", sync=True)
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)
    

    def __init__(self, *args, **kwargs):
        self.value_lock = Lock()
        self._in_values_changed = False
        if 'values' in kwargs:
            values = kwargs['values']
            # convert list values to an dict of {str(v):v}
            if isinstance(values, list):
                # preserve list order with an OrderedDict
                kwargs['values'] = OrderedDict((unicode_type(v), v) for v in values)
        DOMWidget.__init__(self, *args, **kwargs)
    
    def _values_changed(self, name, old, new):
        """Handles when the values dict has been changed.

        Setting values implies setting value names from the keys of the dict.
        """
        self._in_values_changed = True
        try:
            self.value_names = list(new.keys())
        finally:
            self._in_values_changed = False
        
        # ensure that the chosen value is one of the choices
        if self.value not in new.values():
            self.value = next(iter(new.values()))
    
    def _value_names_changed(self, name, old, new):
        if not self._in_values_changed:
            raise TraitError("value_names is a read-only proxy to values.keys(). Use the values dict instead.")

    def _value_changed(self, name, old, new):
        """Called when value has been changed"""
        if self.value_lock.acquire(False):
            try:
                # Reverse dictionary lookup for the value name
                for k,v in self.values.items():
                    if new == v:
                        # set the selected value name
                        self.value_name = k
                        return
                # undo the change, and raise KeyError
                self.value = old
                raise KeyError(new)
            finally:
                self.value_lock.release()

    def _value_name_changed(self, name, old, new):
        """Called when the value name has been changed (typically by the frontend)."""
        if self.value_lock.acquire(False):
            try:
                self.value = self.values[new]
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
