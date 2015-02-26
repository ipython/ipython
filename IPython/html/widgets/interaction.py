"""Interact with functions using widgets."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

try:  # Python >= 3.3
    from inspect import signature, Parameter
except ImportError:
    from IPython.utils.signatures import signature, Parameter
from inspect import getcallargs

from IPython.core.getipython import get_ipython
from IPython.html.widgets import (Widget, Text,
    FloatSlider, IntSlider, Checkbox, Dropdown,
    Box, Button, DOMWidget)
from IPython.display import display, clear_output
from IPython.utils.py3compat import string_types, unicode_type
from IPython.utils.traitlets import HasTraits, Any, Unicode

empty = Parameter.empty


def _matches(o, pattern):
    """Match a pattern of types in a sequence."""
    if not len(o) == len(pattern):
        return False
    comps = zip(o,pattern)
    return all(isinstance(obj,kind) for obj,kind in comps)


def _get_min_max_value(min, max, value=None, step=None):
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
        elif isinstance(value, (int, float)):
            min, max = (-value, 3*value) if value > 0 else (3*value, -value)
        else:
            raise TypeError('expected a number, got: %r' % value)
    else:
        raise ValueError('unable to infer range, value from: ({0}, {1}, {2})'.format(min, max, value))
    if step is not None:
        # ensure value is on a step
        r = (value - min) % step
        value = value - r
    return min, max, value

def _widget_abbrev_single_value(o):
    """Make widgets from single values, which can be used as parameter defaults."""
    if isinstance(o, string_types):
        return Text(value=unicode_type(o))
    elif isinstance(o, dict):
        return Dropdown(options=o)
    elif isinstance(o, bool):
        return Checkbox(value=o)
    elif isinstance(o, float):
        min, max, value = _get_min_max_value(None, None, o)
        return FloatSlider(value=o, min=min, max=max)
    elif isinstance(o, int):
        min, max, value = _get_min_max_value(None, None, o)
        return IntSlider(value=o, min=min, max=max)
    else:
        return None

def _widget_abbrev(o):
    """Make widgets from abbreviations: single values, lists or tuples."""
    float_or_int = (float, int)
    if isinstance(o, (list, tuple)):
        if o and all(isinstance(x, string_types) for x in o):
            return Dropdown(options=[unicode_type(k) for k in o])
        elif _matches(o, (float_or_int, float_or_int)):
            min, max, value = _get_min_max_value(o[0], o[1])
            if all(isinstance(_, int) for _ in o):
                cls = IntSlider
            else:
                cls = FloatSlider
            return cls(value=value, min=min, max=max)
        elif _matches(o, (float_or_int, float_or_int, float_or_int)):
            step = o[2]
            if step <= 0:
                raise ValueError("step must be >= 0, not %r" % step)
            min, max, value = _get_min_max_value(o[0], o[1], step=step)
            if all(isinstance(_, int) for _ in o):
                cls = IntSlider
            else:
                cls = FloatSlider
            return cls(value=value, min=min, max=max, step=step)
    else:
        return _widget_abbrev_single_value(o)

def _widget_from_abbrev(abbrev, default=empty):
    """Build a Widget instance given an abbreviation or Widget."""
    if isinstance(abbrev, Widget) or isinstance(abbrev, fixed):
        return abbrev

    widget = _widget_abbrev(abbrev)
    if default is not empty and isinstance(abbrev, (list, tuple, dict)):
        # if it's not a single-value abbreviation,
        # set the initial value from the default
        try:
            widget.value = default
        except Exception:
            # ignore failure to set default
            pass
    if widget is None:
        raise ValueError("%r cannot be transformed to a Widget" % (abbrev,))
    return widget

def _yield_abbreviations_for_parameter(param, kwargs):
    """Get an abbreviation for a function parameter."""
    name = param.name
    kind = param.kind
    ann = param.annotation
    default = param.default
    not_found = (name, empty, empty)
    if kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY):
        if name in kwargs:
            value = kwargs.pop(name)
        elif ann is not empty:
            value = ann
        elif default is not empty:
            value = default
        else:
            yield not_found
        yield (name, value, default)
    elif kind == Parameter.VAR_KEYWORD:
        # In this case name=kwargs and we yield the items in kwargs with their keys.
        for k, v in kwargs.copy().items():
            kwargs.pop(k)
            yield k, v, empty

def _find_abbreviations(f, kwargs):
    """Find the abbreviations for a function and kwargs passed to interact."""
    new_kwargs = []
    for param in signature(f).parameters.values():
        for name, value, default in _yield_abbreviations_for_parameter(param, kwargs):
            if value is empty:
                raise ValueError('cannot find widget or abbreviation for argument: {!r}'.format(name))
            new_kwargs.append((name, value, default))
    return new_kwargs

def _widgets_from_abbreviations(seq):
    """Given a sequence of (name, abbrev) tuples, return a sequence of Widgets."""
    result = []
    for name, abbrev, default in seq:
        widget = _widget_from_abbrev(abbrev, default)
        if not widget.description:
            widget.description = name
        widget._kwarg = name
        result.append(widget)
    return result

def interactive(__interact_f, **kwargs):
    """
    Builds a group of interactive widgets tied to a function and places the
    group into a Box container.

    Returns
    -------
    container : a Box instance containing multiple widgets

    Parameters
    ----------
    __interact_f : function
        The function to which the interactive widgets are tied. The `**kwargs`
        should match the function signature.
    **kwargs : various, optional
        An interactive widget is created for each keyword argument that is a
        valid widget abbreviation.
    """
    f = __interact_f
    co = kwargs.pop('clear_output', True)
    manual = kwargs.pop('__manual', False)
    kwargs_widgets = []
    container = Box(_dom_classes=['widget-interact'])
    container.result = None
    container.args = []
    container.kwargs = dict()
    kwargs = kwargs.copy()

    new_kwargs = _find_abbreviations(f, kwargs)
    # Before we proceed, let's make sure that the user has passed a set of args+kwargs
    # that will lead to a valid call of the function. This protects against unspecified
    # and doubly-specified arguments.
    getcallargs(f, **{n:v for n,v,_ in new_kwargs})
    # Now build the widgets from the abbreviations.
    kwargs_widgets.extend(_widgets_from_abbreviations(new_kwargs))

    # This has to be done as an assignment, not using container.children.append,
    # so that traitlets notices the update. We skip any objects (such as fixed) that
    # are not DOMWidgets.
    c = [w for w in kwargs_widgets if isinstance(w, DOMWidget)]

    # If we are only to run the function on demand, add a button to request this
    if manual:
        manual_button = Button(description="Run %s" % f.__name__)
        c.append(manual_button)
    container.children = c

    # Build the callback
    def call_f(name=None, old=None, new=None):
        container.kwargs = {}
        for widget in kwargs_widgets:
            value = widget.value
            container.kwargs[widget._kwarg] = value
        if co:
            clear_output(wait=True)
        if manual:
            manual_button.disabled = True
        try:
            container.result = f(**container.kwargs)
        except Exception as e:
            ip = get_ipython()
            if ip is None:
                container.log.warn("Exception in interact callback: %s", e, exc_info=True)
            else:
                ip.showtraceback()
        finally:
            if manual:
                manual_button.disabled = False

    # Wire up the widgets
    # If we are doing manual running, the callback is only triggered by the button
    # Otherwise, it is triggered for every trait change received
    # On-demand running also suppresses running the function with the initial parameters
    if manual:
        manual_button.on_click(call_f)
    else:
        for widget in kwargs_widgets:
            widget.on_trait_change(call_f, 'value')

        container.on_displayed(lambda _: call_f(None, None, None))

    return container

def interact(__interact_f=None, **kwargs):
    """
    Displays interactive widgets which are tied to a function.
    Expects the first argument to be a function. Parameters to this function are
    widget abbreviations passed in as keyword arguments (`**kwargs`). Can be used
    as a decorator (see examples).

    Returns
    -------
    f : __interact_f with interactive widget attached to it.

    Parameters
    ----------
    __interact_f : function
        The function to which the interactive widgets are tied. The `**kwargs`
        should match the function signature. Passed to :func:`interactive()`
    **kwargs : various, optional
        An interactive widget is created for each keyword argument that is a
        valid widget abbreviation. Passed to :func:`interactive()`

    Examples
    --------
    Render an interactive text field that shows the greeting with the passed in
    text::

       # 1. Using interact as a function
       def greeting(text="World"):
           print "Hello {}".format(text)
       interact(greeting, text="IPython Widgets")
        
       # 2. Using interact as a decorator
       @interact
       def greeting(text="World"):
           print "Hello {}".format(text)
        
       # 3. Using interact as a decorator with named parameters
       @interact(text="IPython Widgets")
       def greeting(text="World"):
           print "Hello {}".format(text)
        
    Render an interactive slider widget and prints square of number::

       # 1. Using interact as a function
       def square(num=1):
           print "{} squared is {}".format(num, num*num)
       interact(square, num=5)

       # 2. Using interact as a decorator
       @interact
       def square(num=2):
           print "{} squared is {}".format(num, num*num)
        
       # 3. Using interact as a decorator with named parameters
       @interact(num=5)
       def square(num=2):
           print "{} squared is {}".format(num, num*num)
    """
    # positional arg support in: https://gist.github.com/8851331
    if __interact_f is not None:
        # This branch handles the cases 1 and 2
        # 1. interact(f, **kwargs)
        # 2. @interact
        #    def f(*args, **kwargs):
        #        ...
        f = __interact_f
        w = interactive(f, **kwargs)
        try:
            f.widget = w
        except AttributeError:
            # some things (instancemethods) can't have attributes attached,
            # so wrap in a lambda
            f = lambda *args, **kwargs: __interact_f(*args, **kwargs)
            f.widget = w
        display(w)
        return f
    else:
        # This branch handles the case 3
        # @interact(a=30, b=40)
        # def f(*args, **kwargs):
        #     ...
        def dec(f):
            return interact(f, **kwargs)
        return dec

def interact_manual(__interact_f=None, **kwargs):
    """interact_manual(f, **kwargs)
    
    As `interact()`, generates widgets for each argument, but rather than running
    the function after each widget change, adds a "Run" button and waits for it
    to be clicked. Useful if the function is long-running and has several
    parameters to change.
    """
    return interact(__interact_f, __manual=True, **kwargs)

class fixed(HasTraits):
    """A pseudo-widget whose value is fixed and never synced to the client."""
    value = Any(help="Any Python object")
    description = Unicode('', help="Any Python object")
    def __init__(self, value, **kwargs):
        super(fixed, self).__init__(value=value, **kwargs)
