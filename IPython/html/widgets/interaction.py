"""Interact with functions using widgets."""

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

from __future__ import print_function

try:  # Python >= 3.3
    from inspect import signature, Parameter
except ImportError:
    from IPython.utils.signatures import signature, Parameter
from inspect import getcallargs

from IPython.html.widgets import (Widget, TextWidget,
    FloatSliderWidget, IntSliderWidget, CheckboxWidget, DropdownWidget,
    ContainerWidget)
from IPython.display import display, clear_output
from IPython.utils.py3compat import string_types, unicode_type

#-----------------------------------------------------------------------------
# Classes and Functions
#-----------------------------------------------------------------------------


def _matches(o, pattern):
    """Match a pattern of types in a sequence."""
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
            min, max = (-value, 3.0*value) if value > 0 else (3.0*value, -value)
        elif isinstance(value, int):
            min, max = (-value, 3*value) if value > 0 else (3*value, -value)
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
    elif isinstance(o, bool):
        return CheckboxWidget(value=o)
    elif isinstance(o, float):
        min, max, value = _get_min_max_value(None, None, o)
        return FloatSliderWidget(value=o, min=min, max=max)
    elif isinstance(o, int):
        min, max, value = _get_min_max_value(None, None, o)
        return IntSliderWidget(value=o, min=min, max=max)
    else:
        return None

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

def _widget_from_abbrev(abbrev):
    """Build a Widget intstance given an abbreviation or Widget."""
    if isinstance(abbrev, Widget):
        return abbrev
    
    widget = _widget_abbrev(abbrev)
    if widget is None:
        raise ValueError("%r cannot be transformed to a Widget" % abbrev)
    return widget

def _yield_abbreviations_for_parameter(param, args, kwargs):
    """Get an abbreviation for a function parameter."""
    # print(param, args, kwargs)
    name = param.name
    kind = param.kind
    ann = param.annotation
    default = param.default
    empty = Parameter.empty
    if kind == Parameter.POSITIONAL_ONLY:
        if args:
            yield name, args.pop(0), False
        elif ann is not empty:
            yield name, ann, False
        else:
            yield None, None, None
    elif kind == Parameter.POSITIONAL_OR_KEYWORD:
        if name in kwargs:
            yield name, kwargs.pop(name), True
        elif args:
            yield name, args.pop(0), False
        elif ann is not empty:
            if default is empty:
                yield name, ann, False
            else:
                yield name, ann, True
        elif default is not empty:
            yield name, default, True
        else:
            yield None, None, None
    elif kind == Parameter.VAR_POSITIONAL:
        # In this case name=args or something and we don't actually know the names.
        for item in args[::]:
            args.pop(0)
            yield '', item, False
    elif kind == Parameter.KEYWORD_ONLY:
        if name in kwargs:
            yield name, kwargs.pop(name), True
        elif ann is not empty:
            yield name, ann, True
        elif default is not empty:
            yield name, default, True
        else:
            yield None, None, None
    elif kind == Parameter.VAR_KEYWORD:
        # In this case name=kwargs and we yield the items in kwargs with their keys.
        for k, v in kwargs.copy().items():
            kwargs.pop(k)
            yield k, v, True

def _find_abbreviations(f, args, kwargs):
    """Find the abbreviations for a function and args/kwargs passed to interact."""
    new_args = []
    new_kwargs = []
    for param in signature(f).parameters.values():
        for name, value, kw in _yield_abbreviations_for_parameter(param, args, kwargs):
            if value is None:
                raise ValueError('cannot find widget or abbreviation for argument: {!r}'.format(name))
            if kw:
                new_kwargs.append((name, value))
            else:
                new_args.append((name, value))
    return new_args, new_kwargs

def _widgets_from_abbreviations(seq):
    """Given a sequence of (name, abbrev) tuples, return a sequence of Widgets."""
    result = []
    for name, abbrev in seq:
        widget = _widget_from_abbrev(abbrev)
        widget.description = name
        result.append(widget)
    return result

def interactive(f, *args, **kwargs):
    """Build a group of widgets to interact with a function."""
    co = kwargs.pop('clear_output', True)
    args_widgets = []
    kwargs_widgets = []
    container = ContainerWidget()
    container.result = None
    container.args = []
    container.kwargs = dict()
    # We need this to be a list as we iteratively pop elements off it
    args = list(args)
    kwargs = kwargs.copy()

    new_args, new_kwargs = _find_abbreviations(f, args, kwargs)
    # Before we proceed, let's make sure that the user has passed a set of args+kwargs
    # that will lead to a valid call of the function. This protects against unspecified
    # and doubly-specified arguments.
    getcallargs(f, *[v for n,v in new_args], **{n:v for n,v in new_kwargs})
    # Now build the widgets from the abbreviations.
    args_widgets.extend(_widgets_from_abbreviations(new_args))
    kwargs_widgets.extend(_widgets_from_abbreviations(new_kwargs))
    kwargs_widgets.extend(_widgets_from_abbreviations(sorted(kwargs.items(), key = lambda x: x[0])))

    # This has to be done as an assignment, not using container.children.append,
    # so that traitlets notices the update.
    container.children = args_widgets + kwargs_widgets

    # Build the callback
    def call_f(name, old, new):
        container.args = []
        for widget in args_widgets:
            value = widget.value
            container.args.append(value)
        for widget in kwargs_widgets:
            value = widget.value
            container.kwargs[widget.description] = value
        if co:
            clear_output(wait=True)
        container.result = f(*container.args, **container.kwargs)

    # Wire up the widgets
    for widget in args_widgets:
        widget.on_trait_change(call_f, 'value')
    for widget in kwargs_widgets:
        widget.on_trait_change(call_f, 'value')

    container.on_displayed(lambda _: call_f(None, None, None))

    return container

def interact(f, *args, **kwargs):
    """Interact with a function using widgets."""
    w = interactive(f, *args, **kwargs)
    f.widget = w
    display(w)

def annotate(**kwargs):
    """Python 3 compatible function annotation for Python 2."""
    if not kwargs:
        raise ValueError('annotations must be provided as keyword arguments')
    def dec(f):
        if hasattr(f, '__annotations__'):
            for k, v in kwargs.items():
                f.__annotations__[k] = v
        else:
            f.__annotations__ = kwargs
        return f
    return dec

