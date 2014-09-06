"""Selection classes.

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

from collections import OrderedDict, Iterable, Mapping
from threading import Lock

from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, List, Bool, Any, Dict, TraitError
from IPython.utils.py3compat import unicode_type
from IPython.utils.warn import DeprecatedClass

#-----------------------------------------------------------------------------
# SelectionWidget
#-----------------------------------------------------------------------------
class _Selection(DOMWidget):
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
            if not isinstance(values, Mapping) and isinstance(values, Iterable):
                # preserve list order with an OrderedDict
                kwargs['values'] = OrderedDict((unicode_type(v), v) for v in values)
            # python3.3 turned on hash randomization by default - this means that sometimes, randomly
            # we try to set value before setting values, due to dictionary ordering.  To fix this, force
            # the setting of self.values right now, before anything else runs
            self.values = kwargs.pop('values')
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


class ToggleButtons(_Selection):
    """Group of toggle buttons that represent an enumeration.  Only one toggle
    button can be toggled at any point in time.""" 
    _view_name = Unicode('ToggleButtonsView', sync=True)


class Dropdown(_Selection):
    """Allows you to select a single item from a dropdown."""
    _view_name = Unicode('DropdownView', sync=True)


class RadioButtons(_Selection):
    """Group of radio buttons that represent an enumeration.  Only one radio
    button can be toggled at any point in time.""" 
    _view_name = Unicode('RadioButtonsView', sync=True)
    

class Select(_Selection):
    """Listbox that only allows one item to be selected at any given time."""
    _view_name = Unicode('SelectView', sync=True)


# Remove in IPython 4.0
ToggleButtonsWidget = DeprecatedClass(ToggleButtons, 'ToggleButtonsWidget')
DropdownWidget = DeprecatedClass(Dropdown, 'DropdownWidget')
RadioButtonsWidget = DeprecatedClass(RadioButtons, 'RadioButtonsWidget')
SelectWidget = DeprecatedClass(Select, 'SelectWidget')
