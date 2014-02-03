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
    value_names = List(Unicode, help="""List of names for each value.
        
        If values is specified as a list, this is the string representation of each element.
        Otherwise, it is the keys of the values dictionary.
        
        These strings are used to display the choices in the front-end.""", sync=True)
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)
    

    def __init__(self, *args, **kwargs):
        self.value_lock = Lock()
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
        self.value_names = list(new.keys())
    
    def _value_names_changed(self, name, old, new):
        if len(new) != len(self.values):
            raise TraitError("Expected %i value names, got %i." % (len(self.values), len(new)))

    def _value_changed(self, name, old, new):
        """Called when value has been changed"""
        if self.value_lock.acquire(False):
            try:
                # Make sure the value is one of the options
                for k,v in self.values.items():
                    if new == v:
                        # set the selected value name
                        self.value_name = k
                        return
                raise TraitError('Value not found: %r' % new)
            finally:
                self.value_lock.release()

    def _value_name_changed(self, name, old, new):
        """Called when the value name has been changed (typically by the frontend)."""
        if self.value_lock.acquire(False):
            try:
                if new in self.values:
                    self.value = self.values[new]
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
