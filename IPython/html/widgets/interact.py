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

from IPython.html.widgets import (Widget, StringWidget,
    FloatRangeWidget, IntRangeWidget, BoolWidget, SelectionWidget,
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


def _min_max_value(o):
    min = o[0]
    max = o[1]
    if not max > min:
        raise ValueError('max must be greater than min: (min={0}, max={1})'.format(min, max))
    value = min + abs(o[0]-o[1])/2
    return min, max, value

def _widget_abbrev(o):
    if isinstance(o, string_types):
        return StringWidget(value=unicode_type(o))
    elif isinstance(o, dict):
        values = [unicode_type(k) for k in o]
        w = SelectionWidget(value=values[0], values=values)
        w.actual_values = o
        return w
    # Special case float and int == 0.0
    # get_range(value):
    elif isinstance(o, bool):
        return BoolWidget(value=o)
    elif isinstance(o, float):
        return FloatRangeWidget(value=o, min=-o, max=3.0*o)
    elif isinstance(o, int):
        return IntRangeWidget(value=o, min=-o, max=3*o)
    if isinstance(o, (list, tuple)):
        if _matches(o, (int, int)):
            min, max, value = _min_max_value(o)
            return IntRangeWidget(value=int(value), min=min, max=max)
        elif _matches(o, (int, int, int)):
            min, max, value = _min_max_value(o)
            return IntRangeWidget(value=int(value), min=min, max=max, step=o[2])
        elif _matches(o, (float, float)):
            min, max, value = _min_max_value(o)
            return FloatRangeWidget(value=value, min=min, max=max)
        elif _matches(o, (float, float, float)):
            min, max, value = _min_max_value(o)
            return FloatRangeWidget(value=value, min=min, max=max, step=o[2])
        elif _matches(o, (float, float, int)):
            min, max, value = _min_max_value(o)
            return FloatRangeWidget(value=value, min=min, max=max, step=float(o[2]))
        elif all(isinstance(x, string_types) for x in o):
            return SelectionWidget(value=unicode_type(o[0]),
                                   values=[unicode_type(k) for k in o])


def interactive(f, **kwargs):
    """Interact with a function using widgets."""
    
    co = kwargs.pop('clear_output', True)
    # First convert all args to Widget instances
    widgets = []
    container = ContainerWidget()
    container.result = None
    container.arguments = dict()
    for key, value in kwargs.items():
        if isinstance(value, Widget):
            widget = value
        else:
            widget = _widget_abbrev(value)
            if widget is None:
                raise ValueError("Object cannot be transformed to a Widget")
        widgets.append((key,widget))
        widget.parent = container
    widgets.sort(key=lambda e: e[1].__class__.__name__)
 
    # Build the callback
    def call_f(name, old, new):
        actual_kwargs = {}
        for key, widget in widgets:
            value = widget.value
            if hasattr(widget, 'actual_values'):
                value = widget.actual_values[value]
            container.arguments[key] = value
            actual_kwargs[key] = value
        if co:
            clear_output(wait=True)
        container.result = f(**actual_kwargs)

    # Wire up the widgets
    for key, widget in widgets:
        widget.on_trait_change(call_f, 'value')
        widget.description = key

    container.on_displayed(lambda : call_f(None, None, None))

    return container

def interact(f, **kwargs):
    w = interactive(f, **kwargs)
    display(w)
