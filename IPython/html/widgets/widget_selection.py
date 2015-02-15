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
    Unicode, Bool, Any, Dict, TraitError, CaselessStrEnum, Tuple, List
)
from IPython.utils.py3compat import unicode_type
from IPython.utils.warn import DeprecatedClass

#-----------------------------------------------------------------------------
# SelectionWidget
#-----------------------------------------------------------------------------
class _Selection(DOMWidget):
    """Base class for Selection widgets
    
    ``options`` can be specified as a list or dict. If given as a list,
    it will be transformed to a dict of the form ``{str(value):value}``.

    When programmatically setting the value, a reverse lookup is performed
    among the options to set the value of ``selected_label`` accordingly. The
    reverse lookup uses the equality operator by default, but an other
    predicate may be provided via the ``equals`` argument. For example, when
    dealing with numpy arrays, one may set equals=np.array_equal.
    """
    
    value = Any(help="Selected value")
    selected_label = Unicode(help="The label of the selected value", sync=True)
    options = Any(help="""List of (key, value) tuples or dict of values that the
        user can select.
    
    The keys of this list are the strings that will be displayed in the UI,
    representing the actual Python choices.
    
    The keys of this list are also available as _options_labels.
    """)
    
    _options_dict = Dict()
    _options_labels = Tuple(sync=True)
    _options_values = Tuple()

    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)
        
    def __init__(self, *args, **kwargs):
        self.value_lock = Lock()
        self.options_lock = Lock()
        self.equals = kwargs.pop('equals', lambda x, y: x == y)
        self.on_trait_change(self._options_readonly_changed, ['_options_dict', '_options_labels', '_options_values', '_options'])
        if 'options' in kwargs:
            self.options = kwargs.pop('options')
        DOMWidget.__init__(self, *args, **kwargs)
        self._value_in_options()
    
    def _make_options(self, x):
        # If x is a dict, convert it to list format.
        if isinstance(x, (OrderedDict, dict)):
            return [(k, v) for k, v in x.items()]
        
        # Make sure x is a list or tuple.
        if not isinstance(x, (list, tuple)):
            raise ValueError('x')
        
        # If x is an ordinary list, use the option values as names.
        for y in x:
            if not isinstance(y, (list, tuple)) or len(y) < 2:
                return [(i, i) for i in x]
        
        # Value is already in the correct format.
        return x

    def _options_changed(self, name, old, new):
        """Handles when the options tuple has been changed.

        Setting options implies setting option labels from the keys of the dict.
        """
        if self.options_lock.acquire(False):
            try:
                self.options = new

                options = self._make_options(new)
                self._options_dict = {i[0]: i[1] for i in options}
                self._options_labels = [i[0] for i in options]
                self._options_values = [i[1] for i in options]
                self._value_in_options()
            finally:
                self.options_lock.release()
        
    def _value_in_options(self):
        # ensure that the chosen value is one of the choices
    
        if self._options_values:
            if self.value not in self._options_values:
                self.value = next(iter(self._options_values))

    def _options_readonly_changed(self, name, old, new):
        if not self.options_lock.locked():
            raise TraitError("`.%s` is a read-only trait. Use the `.options` tuple instead." % name)

    def _value_changed(self, name, old, new):
        """Called when value has been changed"""
        if self.value_lock.acquire(False):
            try:
                # Reverse dictionary lookup for the value name
                for k, v in self._options_dict.items():
                    if self.equals(new, v):
                        # set the selected value name
                        self.selected_label = k
                        return
                # undo the change, and raise KeyError
                self.value = old
                raise KeyError(new)
            finally:
                self.value_lock.release()

    def _selected_label_changed(self, name, old, new):
        """Called when the value name has been changed (typically by the frontend)."""
        if self.value_lock.acquire(False):
            try:
                self.value = self._options_dict[new]
            finally:
                self.value_lock.release()


class _MultipleSelection(_Selection):
    """Base class for MultipleSelection widgets.

    As with ``_Selection``, ``options`` can be specified as a list or dict. If
    given as a list, it will be transformed to a dict of the form
    ``{str(value): value}``.

    Despite their names, ``value`` (and ``selected_label``) will be tuples, even
    if only a single option is selected.
    """

    value = Tuple(help="Selected values")
    selected_labels = Tuple(help="The labels of the selected options",
                            sync=True)

    @property
    def selected_label(self):
        raise AttributeError(
            "Does not support selected_label, use selected_labels")

    def _value_in_options(self):
        # ensure that the chosen value is one of the choices
        if self.options:
            old_value = self.value or []
            new_value = []
            for value in old_value:
                if value in self._options_dict.values():
                    new_value.append(value)
            if new_value:
                self.value = new_value
            else:
                self.value = [next(iter(self._options_dict.values()))]

    def _value_changed(self, name, old, new):
        """Called when value has been changed"""
        if self.value_lock.acquire(False):
            try:
                self.selected_labels = [
                    self._options_labels[self._options_values.index(v)]
                    for v in new
                ]
            except:
                self.value = old
                raise KeyError(new)
            finally:
                self.value_lock.release()

    def _selected_labels_changed(self, name, old, new):
        """Called when the selected label has been changed (typically by the
        frontend)."""
        if self.value_lock.acquire(False):
            try:
                self.value = [self._options_dict[name] for name in new]
            finally:
                self.value_lock.release()


@register('IPython.ToggleButtons')
class ToggleButtons(_Selection):
    """Group of toggle buttons that represent an enumeration.  Only one toggle
    button can be toggled at any point in time.""" 
    _view_name = Unicode('ToggleButtonsView', sync=True)
    tooltips = List(Unicode(), sync=True)
    icons = List(Unicode(), sync=True)

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


@register('IPython.SelectMultiple')
class SelectMultiple(_MultipleSelection):
    """Listbox that allows many items to be selected at any given time.
    Despite their names, inherited from ``_Selection``, the currently chosen
    option values, ``value``, or their labels, ``selected_labels`` must both be
    updated with a list-like object."""
    _view_name = Unicode('SelectMultipleView', sync=True)


# Remove in IPython 4.0
ToggleButtonsWidget = DeprecatedClass(ToggleButtons, 'ToggleButtonsWidget')
DropdownWidget = DeprecatedClass(Dropdown, 'DropdownWidget')
RadioButtonsWidget = DeprecatedClass(RadioButtons, 'RadioButtonsWidget')
SelectWidget = DeprecatedClass(Select, 'SelectWidget')
