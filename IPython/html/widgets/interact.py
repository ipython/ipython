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
            raise TypeError('expected a number, got: %r' % number)
    else:
        raise ValueError('unable to infer range, value from: ({0}, {1}, {2})'.format(min, max, value))
    return min, max, value


def _widget_abbrev(o):
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


def interactive(f, **kwargs):
    """Interact with a function using widgets."""
    
    co = kwargs.pop('clear_output', True)
    # First convert all args to Widget instances
    widgets = []
    container = ContainerWidget()
    container.result = None
    container.kwargs = dict()
    for key, value in kwargs.items():
        if isinstance(value, Widget):
            widget = value
        else:
            widget = _widget_abbrev(value)
            if widget is None:
                raise ValueError("Object cannot be transformed to a Widget")
        widget.description = key
        widgets.append((key,widget))
    widgets.sort(key=lambda e: e[1].__class__.__name__)
    container.children = [e[1] for e in widgets]

    # Build the callback
    def call_f(name, old, new):
        actual_kwargs = {}
        for key, widget in widgets:
            value = widget.value
            container.kwargs[key] = value
            actual_kwargs[key] = value
        if co:
            clear_output(wait=True)
        container.result = f(**actual_kwargs)

    # Wire up the widgets
    for key, widget in widgets:
        widget.on_trait_change(call_f, 'value')

    container.on_displayed(lambda _: call_f(None, None, None))

    return container

def interact(f, **kwargs):
    w = interactive(f, **kwargs)
    display(w)
