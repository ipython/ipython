"""Interact with functions using widgets.
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

try:  # Python >= 3.3
    from inspect import signature, Parameter
except ImportError:
    from IPython.utils.signatures import signature, Parameter

from IPython.html.widgets import (Widget, TextWidget,
    FloatSliderWidget, IntSliderWidget, CheckboxWidget, DropdownWidget,
    ContainerWidget)
from IPython.display import display, clear_output
from IPython.utils.py3compat import string_types, unicode_type

#-----------------------------------------------------------------------------
# Classes and Functions
#-----------------------------------------------------------------------------


def _matches(o, pattern):
    if not len(o) == len(pattern):
        return False
    comps = zip(o,pattern)
    return all(isinstance(obj,kind) for obj,kind in comps)


def _get_min_max_value(min, max, value):
    """Return min, max, value given input values with possible None."""
    if value is None:
        if not max > min:
            raise ValueError('max must be greater than min: (min={0}, max={1})'.format(min, max))
        value = min + abs(min-max)/2
        value = type(min)(value)
    elif min is None and max is None:
        if value == 0.0:
            min, max, value = 0.0, 1.0, 0.5
        elif value == 0:
            min, max, value = 0, 1, 0
        elif isinstance(value, float):
            min, max = -value, 3.0*value
        elif isinstance(value, int):
            min, max = -value, 3*value
        else:
            raise TypeError('expected a number, got: %r' % value)
    else:
        raise ValueError('unable to infer range, value from: ({0}, {1}, {2})'.format(min, max, value))
    return min, max, value

def _widget_abbrev_single_value(o):
    """Make widgets from single values, which can be used written as parameter defaults."""
    if isinstance(o, string_types):
        return TextWidget(value=unicode_type(o))
    elif isinstance(o, dict):
        labels = [unicode_type(k) for k in o]
        values = o.values()
        w = DropdownWidget(value=values[0], values=values, labels=labels)
        return w
    # Special case float and int == 0.0
    # get_range(value):
    elif isinstance(o, bool):
        return CheckboxWidget(value=o)
    elif isinstance(o, float):
        min, max, value = _get_min_max_value(None, None, o)
        return FloatSliderWidget(value=o, min=min, max=max)
    elif isinstance(o, int):
        min, max, value = _get_min_max_value(None, None, o)
        return IntSliderWidget(value=o, min=min, max=max)

def _widget_abbrev(o):
    """Make widgets from abbreviations: single values, lists or tuples."""
    if isinstance(o, (list, tuple)):
        if _matches(o, (int, int)):
            min, max, value = _get_min_max_value(o[0], o[1], None)
            return IntSliderWidget(value=value, min=min, max=max)
        elif _matches(o, (int, int, int)):
            min, max, value = _get_min_max_value(o[0], o[1], None)
            return IntSliderWidget(value=value, min=min, max=max, step=o[2])
        elif _matches(o, (float, float)):
            min, max, value = _get_min_max_value(o[0], o[1], None)
            return FloatSliderWidget(value=value, min=min, max=max)
        elif _matches(o, (float, float, float)):
            min, max, value = _get_min_max_value(o[0], o[1], None)
            return FloatSliderWidget(value=value, min=min, max=max, step=o[2])
        elif _matches(o, (float, float, int)):
            min, max, value = _get_min_max_value(o[0], o[1], None)
            return FloatSliderWidget(value=value, min=min, max=max, step=float(o[2]))
        elif all(isinstance(x, string_types) for x in o):
            return DropdownWidget(value=unicode_type(o[0]),
                                   values=[unicode_type(k) for k in o])

    else:
        return _widget_abbrev_single_value(o)

def _widget_or_abbrev(value):
    if isinstance(value, Widget):
        return value
    
    widget = _widget_abbrev(value)
    if widget is None:
        raise ValueError("%r cannot be transformed to a Widget" % value)
    return widget

def _widget_for_param(param, kwargs):
    """Get a widget for a parameter.
    
    We look for, in this order:
    - keyword arguments passed to interact[ive]() that match the parameter name.
    - function annotations
    - default values
    
    Returns an instance of Widget, or None if nothing suitable is found.
    
    Raises ValueError if the kwargs or annotation value cannot be made into
    a widget.
    """
    if param.name in kwargs:
        return _widget_or_abbrev(kwargs.pop(param.name))
    
    if param.annotation is not Parameter.empty:
        return _widget_or_abbrev(param.annotation)
    
    if param.default is not Parameter.empty:
        # Returns None if it's not suitable
        return _widget_abbrev_single_value(param.default)
    
    return None

def interactive(f, **kwargs):
    """Build a group of widgets for setting the inputs to a function."""
    
    co = kwargs.pop('clear_output', True)
    # First convert all args to Widget instances
    widgets = []
    container = ContainerWidget()
    container.result = None
    container.kwargs = dict()
    
    # Extract parameters from the function signature
    for param in signature(f).parameters.values():
        param_widget = _widget_for_param(param, kwargs)
        if param_widget is not None:
            param_widget.description = param.name
            widgets.append(param_widget)
    
    # Extra parameters from keyword args - we assume f takes **kwargs
    for name, value in sorted(kwargs.items(), key = lambda x: x[0]):
        widget = _widget_or_abbrev(value)
        widget.description = name
        widgets.append(widget)
    
    # This has to be done as an assignment, not using container.children.append,
    # so that traitlets notices the update.
    container.children = widgets

    # Build the callback
    def call_f(name, old, new):
        actual_kwargs = {}
        for widget in widgets:
            value = widget.value
            container.kwargs[widget.description] = value
            actual_kwargs[widget.description] = value
        if co:
            clear_output(wait=True)
        container.result = f(**actual_kwargs)

    # Wire up the widgets
    for widget in widgets:
        widget.on_trait_change(call_f, 'value')

    container.on_displayed(lambda _: call_f(None, None, None))

    return container

def interact(f, **kwargs):
    """Interact with a function using widgets."""
    w = interactive(f, **kwargs)
    f.widget = w
    display(w)
