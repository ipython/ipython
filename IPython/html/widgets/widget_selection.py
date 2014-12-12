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

from collections import OrderedDict
from threading import Lock

from .widget import DOMWidget, register
from IPython.utils.traitlets import (
    Unicode, Bool, Any, Dict, TraitError, CaselessStrEnum, Tuple
)
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
    value_name = Unicode(help="The name of the selected value", sync=True)
    values = Any(help="""List of (key, value) tuples or dict of values that the 
        user can select.
    
    The keys of this list are the strings that will be displayed in the UI,
    representing the actual Python choices.
    
    The keys of this list are also available as _value_names.
    """)
    
    _values_dict = Dict()
    _value_names = Tuple(sync=True)
    _value_values = Tuple()

    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)
        
    def __init__(self, *args, **kwargs):
        self.value_lock = Lock()
        self.values_lock = Lock()
        self.on_trait_change(self._values_readonly_changed, ['_values_dict', '_value_names', '_value_values', '_values'])
        if 'values' in kwargs:
            self.values = kwargs.pop('values')
        DOMWidget.__init__(self, *args, **kwargs)
        self._value_in_values()
    
    def _make_values(self, x):
        # If x is a dict, convert it to list format.
        if isinstance(x, (OrderedDict, dict)):
            return [(k, v) for k, v in x.items()]
        
        # Make sure x is a list or tuple.
        if not isinstance(x, (list, tuple)):
            raise ValueError('x')
        
        # If x is an ordinary list, use the values as names.
        for y in x:
            if not isinstance(y, (list, tuple)) or len(y) < 2:
                return [(i, i) for i in x]
        
        # Value is already in the correct format.
        return x

    def _values_changed(self, name, old, new):
        """Handles when the values tuple has been changed.

        Setting values implies setting value names from the keys of the dict.
        """        
        if self.values_lock.acquire(False):
            try:
                self.values = new

                values = self._make_values(new)
                self._values_dict = {i[0]: i[1] for i in values}
                self._value_names = [i[0] for i in values]
                self._value_values = [i[1] for i in values]
                self._value_in_values()
            finally:
                self.values_lock.release()
        
    def _value_in_values(self):
        # ensure that the chosen value is one of the choices
        if self._value_values:
            if self.value not in self._value_values:
                self.value = next(iter(self._value_values))
    
    def _values_readonly_changed(self, name, old, new):
        if not self.values_lock.locked():
            raise TraitError("`.%s` is a read-only trait. Use the `.values` tuple instead." % name)

    def _value_changed(self, name, old, new):
        """Called when value has been changed"""
        if self.value_lock.acquire(False):
            try:
                # Reverse dictionary lookup for the value name
                for k,v in self._values_dict.items():
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
                self.value = self._values_dict[new]
            finally:
                self.value_lock.release()


@register('IPython.ToggleButtons')
class ToggleButtons(_Selection):
    """Group of toggle buttons that represent an enumeration.  Only one toggle
    button can be toggled at any point in time.""" 
    _view_name = Unicode('ToggleButtonsView', sync=True)

    button_style = CaselessStrEnum(
        values=['primary', 'success', 'info', 'warning', 'danger', ''], 
        default_value='', allow_none=True, sync=True, help="""Use a
        predefined styling for the buttons.""")

@register('IPython.Dropdown')
class Dropdown(_Selection):
    """Allows you to select a single item from a dropdown."""
    _view_name = Unicode('DropdownView', sync=True)

    button_style = CaselessStrEnum(
        values=['primary', 'success', 'info', 'warning', 'danger', ''], 
        default_value='', allow_none=True, sync=True, help="""Use a
        predefined styling for the buttons.""")

@register('IPython.RadioButtons')
class RadioButtons(_Selection):
    """Group of radio buttons that represent an enumeration.  Only one radio
    button can be toggled at any point in time.""" 
    _view_name = Unicode('RadioButtonsView', sync=True)
    


@register('IPython.Select')
class Select(_Selection):
    """Listbox that only allows one item to be selected at any given time."""
    _view_name = Unicode('SelectView', sync=True)


# Remove in IPython 4.0
ToggleButtonsWidget = DeprecatedClass(ToggleButtons, 'ToggleButtonsWidget')
DropdownWidget = DeprecatedClass(Dropdown, 'DropdownWidget')
RadioButtonsWidget = DeprecatedClass(RadioButtons, 'RadioButtonsWidget')
SelectWidget = DeprecatedClass(Select, 'SelectWidget')
