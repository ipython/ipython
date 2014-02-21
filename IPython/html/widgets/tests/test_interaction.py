"""Test interact and interactive."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2014 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import print_function

from collections import OrderedDict

import nose.tools as nt
import IPython.testing.tools as tt

# from IPython.core.getipython import get_ipython
from IPython.html import widgets
from IPython.html.widgets import interact, interactive, Widget, interaction
from IPython.utils.py3compat import annotate

#-----------------------------------------------------------------------------
# Utility stuff
#-----------------------------------------------------------------------------

class DummyComm(object):
    comm_id = 'a-b-c-d'
    def send(self, *args, **kwargs):
        pass
    
    def close(self, *args, **kwargs):
        pass

_widget_attrs = {}
displayed = []

def setup():
    _widget_attrs['comm'] = Widget.comm
    Widget.comm = DummyComm()
    _widget_attrs['_ipython_display_'] = Widget._ipython_display_
    def raise_not_implemented(*args, **kwargs):
        raise NotImplementedError()
    Widget._ipython_display_ = raise_not_implemented

def teardown():
    for attr, value in _widget_attrs.items():
        setattr(Widget, attr, value)

def f(**kwargs):
    pass

def clear_display():
    global displayed
    displayed = []

def record_display(*args):
    displayed.extend(args)

#-----------------------------------------------------------------------------
# Actual tests
#-----------------------------------------------------------------------------

def check_widget(w, **d):
    """Check a single widget against a dict"""
    for attr, expected in d.items():
        if attr == 'cls':
            nt.assert_is(w.__class__, expected)
        else:
            value = getattr(w, attr)
            nt.assert_equal(value, expected,
                "%s.%s = %r != %r" % (w.__class__.__name__, attr, value, expected)
            )

def check_widgets(container, **to_check):
    """Check that widgets are created as expected"""
    # build a widget dictionary, so it matches
    widgets = {}
    for w in container.children:
        widgets[w.description] = w
    
    for key, d in to_check.items():
        nt.assert_in(key, widgets)
        check_widget(widgets[key], **d)
    

def test_single_value_string():
    a = u'hello'
    c = interactive(f, a=a)
    w = c.children[0]
    check_widget(w,
        cls=widgets.TextWidget,
        description='a',
        value=a,
    )

def test_single_value_bool():
    for a in (True, False):
        c = interactive(f, a=a)
        w = c.children[0]
        check_widget(w,
            cls=widgets.CheckboxWidget,
            description='a',
            value=a,
        )

def test_single_value_dict():
    for d in [
        dict(a=5),
        dict(a=5, b='b', c=dict),
    ]:
        c = interactive(f, d=d)
        w = c.children[0]
        check_widget(w,
            cls=widgets.DropdownWidget,
            description='d',
            values=d,
            value=next(iter(d.values())),
        )

def test_single_value_float():
    for a in (2.25, 1.0, -3.5):
        c = interactive(f, a=a)
        w = c.children[0]
        check_widget(w,
            cls=widgets.FloatSliderWidget,
            description='a',
            value=a,
            min= -a if a > 0 else 3*a,
            max= 3*a if a > 0 else -a,
            step=0.1,
            readout=True,
        )

def test_single_value_int():
    for a in (1, 5, -3):
        c = interactive(f, a=a)
        nt.assert_equal(len(c.children), 1)
        w = c.children[0]
        check_widget(w,
            cls=widgets.IntSliderWidget,
            description='a',
            value=a,
            min= -a if a > 0 else 3*a,
            max= 3*a if a > 0 else -a,
            step=1,
            readout=True,
        )

def test_list_tuple_2_int():
    with nt.assert_raises(ValueError):
        c = interactive(f, tup=(1,1))
    with nt.assert_raises(ValueError):
        c = interactive(f, tup=(1,-1))
    for min, max in [ (0,1), (1,10), (1,2), (-5,5), (-20,-19) ]:
        c = interactive(f, tup=(min, max), lis=[min, max])
        nt.assert_equal(len(c.children), 2)
        d = dict(
            cls=widgets.IntSliderWidget,
            min=min,
            max=max,
            step=1,
            readout=True,
        )
        check_widgets(c, tup=d, lis=d)

def test_list_tuple_3_int():
    with nt.assert_raises(ValueError):
        c = interactive(f, tup=(1,2,0))
    with nt.assert_raises(ValueError):
        c = interactive(f, tup=(1,2,-1))
    for min, max, step in [ (0,2,1), (1,10,2), (1,100,2), (-5,5,4), (-100,-20,4) ]:
        c = interactive(f, tup=(min, max, step), lis=[min, max, step])
        nt.assert_equal(len(c.children), 2)
        d = dict(
            cls=widgets.IntSliderWidget,
            min=min,
            max=max,
            step=step,
            readout=True,
        )
        check_widgets(c, tup=d, lis=d)

def test_list_tuple_2_float():
    with nt.assert_raises(ValueError):
        c = interactive(f, tup=(1.0,1.0))
    with nt.assert_raises(ValueError):
        c = interactive(f, tup=(0.5,-0.5))
    for min, max in [ (0.5, 1.5), (1.1,10.2), (1,2.2), (-5.,5), (-20,-19.) ]:
        c = interactive(f, tup=(min, max), lis=[min, max])
        nt.assert_equal(len(c.children), 2)
        d = dict(
            cls=widgets.FloatSliderWidget,
            min=min,
            max=max,
            step=.1,
            readout=True,
        )
        check_widgets(c, tup=d, lis=d)

def test_list_tuple_3_float():
    with nt.assert_raises(ValueError):
        c = interactive(f, tup=(1,2,0.0))
    with nt.assert_raises(ValueError):
        c = interactive(f, tup=(-1,-2,1.))
    with nt.assert_raises(ValueError):
        c = interactive(f, tup=(1,2.,-1.))
    for min, max, step in [ (0.,2,1), (1,10.,2), (1,100,2.), (-5.,5.,4), (-100,-20.,4.) ]:
        c = interactive(f, tup=(min, max, step), lis=[min, max, step])
        nt.assert_equal(len(c.children), 2)
        d = dict(
            cls=widgets.FloatSliderWidget,
            min=min,
            max=max,
            step=step,
            readout=True,
        )
        check_widgets(c, tup=d, lis=d)

def test_list_tuple_str():
    values = ['hello', 'there', 'guy']
    first = values[0]
    dvalues = OrderedDict((v,v) for v in values)
    c = interactive(f, tup=tuple(values), lis=list(values))
    nt.assert_equal(len(c.children), 2)
    d = dict(
        cls=widgets.DropdownWidget,
        value=first,
        values=dvalues
    )
    check_widgets(c, tup=d, lis=d)

def test_list_tuple_invalid():
    for bad in [
        (),
        (5, 'hi'),
        ('hi', 5),
        ({},),
        (None,),
    ]:
        with nt.assert_raises(ValueError):
            print(bad) # because there is no custom message in assert_raises
            c = interactive(f, tup=bad)

def test_defaults():
    @annotate(n=10)
    def f(n, f=4.5, g=1):
        pass
    
    c = interactive(f)
    check_widgets(c,
        n=dict(
            cls=widgets.IntSliderWidget,
            value=10,
        ),
        f=dict(
            cls=widgets.FloatSliderWidget,
            value=4.5,
        ),
        g=dict(
            cls=widgets.IntSliderWidget,
            value=1,
        ),
    )

def test_default_values():
    @annotate(n=10, f=(0, 10.), g=5, h={'a': 1, 'b': 2}, j=['hi', 'there'])
    def f(n, f=4.5, g=1, h=2, j='there'):
        pass
    
    c = interactive(f)
    check_widgets(c,
        n=dict(
            cls=widgets.IntSliderWidget,
            value=10,
        ),
        f=dict(
            cls=widgets.FloatSliderWidget,
            value=4.5,
        ),
        g=dict(
            cls=widgets.IntSliderWidget,
            value=5,
        ),
        h=dict(
            cls=widgets.DropdownWidget,
            values={'a': 1, 'b': 2},
            value=2
        ),
        j=dict(
            cls=widgets.DropdownWidget,
            values={'hi':'hi', 'there':'there'},
            value='there'
        ),
    )

def test_default_out_of_bounds():
    @annotate(f=(0, 10.), h={'a': 1}, j=['hi', 'there'])
    def f(f='hi', h=5, j='other'):
        pass
    
    c = interactive(f)
    check_widgets(c,
        f=dict(
            cls=widgets.FloatSliderWidget,
            value=5.,
        ),
        h=dict(
            cls=widgets.DropdownWidget,
            values={'a': 1},
            value=1,
        ),
        j=dict(
            cls=widgets.DropdownWidget,
            values={'hi':'hi', 'there':'there'},
            value='hi',
        ),
    )

def test_annotations():
    @annotate(n=10, f=widgets.FloatTextWidget())
    def f(n, f):
        pass
    
    c = interactive(f)
    check_widgets(c,
        n=dict(
            cls=widgets.IntSliderWidget,
            value=10,
        ),
        f=dict(
            cls=widgets.FloatTextWidget,
        ),
    )

def test_priority():
    @annotate(annotate='annotate', kwarg='annotate')
    def f(kwarg='default', annotate='default', default='default'):
        pass
    
    c = interactive(f, kwarg='kwarg')
    check_widgets(c,
        kwarg=dict(
            cls=widgets.TextWidget,
            value='kwarg',
        ),
        annotate=dict(
            cls=widgets.TextWidget,
            value='annotate',
        ),
    )

@nt.with_setup(clear_display)
def test_decorator_kwarg():
    with tt.monkeypatch(interaction, 'display', record_display):
        @interact(a=5)
        def foo(a):
            pass
    nt.assert_equal(len(displayed), 1)
    w = displayed[0].children[0]
    check_widget(w,
        cls=widgets.IntSliderWidget,
        value=5,
    )

@nt.with_setup(clear_display)
def test_decorator_no_call():
    with tt.monkeypatch(interaction, 'display', record_display):
        @interact
        def foo(a='default'):
            pass
    nt.assert_equal(len(displayed), 1)
    w = displayed[0].children[0]
    check_widget(w,
        cls=widgets.TextWidget,
        value='default',
    )

@nt.with_setup(clear_display)
def test_call_interact():
    def foo(a='default'):
        pass
    with tt.monkeypatch(interaction, 'display', record_display):
        ifoo = interact(foo)
    nt.assert_equal(len(displayed), 1)
    w = displayed[0].children[0]
    check_widget(w,
        cls=widgets.TextWidget,
        value='default',
    )

@nt.with_setup(clear_display)
def test_call_interact_kwargs():
    def foo(a='default'):
        pass
    with tt.monkeypatch(interaction, 'display', record_display):
        ifoo = interact(foo, a=10)
    nt.assert_equal(len(displayed), 1)
    w = displayed[0].children[0]
    check_widget(w,
        cls=widgets.IntSliderWidget,
        value=10,
    )

@nt.with_setup(clear_display)
def test_call_decorated_on_trait_change():
    """test calling @interact decorated functions"""
    d = {}
    with tt.monkeypatch(interaction, 'display', record_display):
        @interact
        def foo(a='default'):
            d['a'] = a
            return a
    nt.assert_equal(len(displayed), 1)
    w = displayed[0].children[0]
    check_widget(w,
        cls=widgets.TextWidget,
        value='default',
    )
    # test calling the function directly
    a = foo('hello')
    nt.assert_equal(a, 'hello')
    nt.assert_equal(d['a'], 'hello')
    
    # test that setting trait values calls the function
    w.value = 'called'
    nt.assert_equal(d['a'], 'called')

@nt.with_setup(clear_display)
def test_call_decorated_kwargs_on_trait_change():
    """test calling @interact(foo=bar) decorated functions"""
    d = {}
    with tt.monkeypatch(interaction, 'display', record_display):
        @interact(a='kwarg')
        def foo(a='default'):
            d['a'] = a
            return a
    nt.assert_equal(len(displayed), 1)
    w = displayed[0].children[0]
    check_widget(w,
        cls=widgets.TextWidget,
        value='kwarg',
    )
    # test calling the function directly
    a = foo('hello')
    nt.assert_equal(a, 'hello')
    nt.assert_equal(d['a'], 'hello')
    
    # test that setting trait values calls the function
    w.value = 'called'
    nt.assert_equal(d['a'], 'called')

def test_fixed():
    c = interactive(f, a=widgets.fixed(5), b='text')
    nt.assert_equal(len(c.children), 1)
    w = c.children[0]
    check_widget(w,
        cls=widgets.TextWidget,
        value='text',
        description='b',
    )

