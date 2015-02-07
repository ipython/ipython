"""Test interact and interactive."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

from collections import OrderedDict

import nose.tools as nt
import IPython.testing.tools as tt

from IPython.kernel.comm import Comm
from IPython.html import widgets
from IPython.html.widgets import interact, interactive, Widget, interaction
from IPython.utils.py3compat import annotate

#-----------------------------------------------------------------------------
# Utility stuff
#-----------------------------------------------------------------------------

class DummyComm(Comm):
    comm_id = 'a-b-c-d'
    
    def open(self, *args, **kwargs):
        pass
    
    def send(self, *args, **kwargs):
        pass
    
    def close(self, *args, **kwargs):
        pass

_widget_attrs = {}
displayed = []
undefined = object()

def setup():
    _widget_attrs['_comm_default'] = getattr(Widget, '_comm_default', undefined)
    Widget._comm_default = lambda self: DummyComm()
    _widget_attrs['_ipython_display_'] = Widget._ipython_display_
    def raise_not_implemented(*args, **kwargs):
        raise NotImplementedError()
    Widget._ipython_display_ = raise_not_implemented

def teardown():
    for attr, value in _widget_attrs.items():
        if value is undefined:
            delattr(Widget, attr)
        else:
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
        cls=widgets.Text,
        description='a',
        value=a,
    )

def test_single_value_bool():
    for a in (True, False):
        c = interactive(f, a=a)
        w = c.children[0]
        check_widget(w,
            cls=widgets.Checkbox,
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
            cls=widgets.Dropdown,
            description='d',
            options=d,
            value=next(iter(d.values())),
        )

def test_single_value_float():
    for a in (2.25, 1.0, -3.5):
        c = interactive(f, a=a)
        w = c.children[0]
        check_widget(w,
            cls=widgets.FloatSlider,
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
            cls=widgets.IntSlider,
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
            cls=widgets.IntSlider,
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
            cls=widgets.IntSlider,
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
            cls=widgets.FloatSlider,
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
            cls=widgets.FloatSlider,
            min=min,
            max=max,
            step=step,
            readout=True,
        )
        check_widgets(c, tup=d, lis=d)

def test_list_tuple_str():
    values = ['hello', 'there', 'guy']
    first = values[0]
    c = interactive(f, tup=tuple(values), lis=list(values))
    nt.assert_equal(len(c.children), 2)
    d = dict(
        cls=widgets.Dropdown,
        value=first,
        options=values
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
            cls=widgets.IntSlider,
            value=10,
        ),
        f=dict(
            cls=widgets.FloatSlider,
            value=4.5,
        ),
        g=dict(
            cls=widgets.IntSlider,
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
            cls=widgets.IntSlider,
            value=10,
        ),
        f=dict(
            cls=widgets.FloatSlider,
            value=4.5,
        ),
        g=dict(
            cls=widgets.IntSlider,
            value=5,
        ),
        h=dict(
            cls=widgets.Dropdown,
            options={'a': 1, 'b': 2},
            value=2
        ),
        j=dict(
            cls=widgets.Dropdown,
            options=['hi', 'there'],
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
            cls=widgets.FloatSlider,
            value=5.,
        ),
        h=dict(
            cls=widgets.Dropdown,
            options={'a': 1},
            value=1,
        ),
        j=dict(
            cls=widgets.Dropdown,
            options=['hi', 'there'],
            value='hi',
        ),
    )

def test_annotations():
    @annotate(n=10, f=widgets.FloatText())
    def f(n, f):
        pass
    
    c = interactive(f)
    check_widgets(c,
        n=dict(
            cls=widgets.IntSlider,
            value=10,
        ),
        f=dict(
            cls=widgets.FloatText,
        ),
    )

def test_priority():
    @annotate(annotate='annotate', kwarg='annotate')
    def f(kwarg='default', annotate='default', default='default'):
        pass
    
    c = interactive(f, kwarg='kwarg')
    check_widgets(c,
        kwarg=dict(
            cls=widgets.Text,
            value='kwarg',
        ),
        annotate=dict(
            cls=widgets.Text,
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
        cls=widgets.IntSlider,
        value=5,
    )

@nt.with_setup(clear_display)
def test_interact_instancemethod():
    class Foo(object):
        def show(self, x):
            print(x)

    f = Foo()
    
    with tt.monkeypatch(interaction, 'display', record_display):
        g = interact(f.show, x=(1,10))
    nt.assert_equal(len(displayed), 1)
    w = displayed[0].children[0]
    check_widget(w,
        cls=widgets.IntSlider,
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
        cls=widgets.Text,
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
        cls=widgets.Text,
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
        cls=widgets.IntSlider,
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
        cls=widgets.Text,
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
        cls=widgets.Text,
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
        cls=widgets.Text,
        value='text',
        description='b',
    )

def test_default_description():
    c = interactive(f, b='text')
    w = c.children[0]
    check_widget(w,
        cls=widgets.Text,
        value='text',
        description='b',
    )

def test_custom_description():
    d = {}
    def record_kwargs(**kwargs):
        d.clear()
        d.update(kwargs)
    
    c = interactive(record_kwargs, b=widgets.Text(value='text', description='foo'))
    w = c.children[0]
    check_widget(w,
        cls=widgets.Text,
        value='text',
        description='foo',
    )
    w.value = 'different text'
    nt.assert_equal(d, {'b': 'different text'})

def test_interact_manual_button():
    c = interactive(f, __manual=True)
    w = c.children[0]
    check_widget(w, cls=widgets.Button)

def test_interact_manual_nocall():
    callcount = 0
    def calltest(testarg):
        callcount += 1
    c = interactive(calltest, testarg=5, __manual=True)
    c.children[0].value = 10
    nt.assert_equal(callcount, 0)

def test_int_range_logic():
    irsw = widgets.IntRangeSlider
    w = irsw(value=(2, 4), min=0, max=6)
    check_widget(w, cls=irsw, value=(2, 4), min=0, max=6)
    w.value = (4, 2)
    check_widget(w, cls=irsw, value=(2, 4), min=0, max=6)
    w.value = (-1, 7)
    check_widget(w, cls=irsw, value=(0, 6), min=0, max=6)
    w.min = 3
    check_widget(w, cls=irsw, value=(3, 6), min=3, max=6)
    w.max = 3
    check_widget(w, cls=irsw, value=(3, 3), min=3, max=3)
    
    w.min = 0
    w.max = 6
    w.lower = 2
    w.upper = 4
    check_widget(w, cls=irsw, value=(2, 4), min=0, max=6)
    w.value = (0, 1) #lower non-overlapping range
    check_widget(w, cls=irsw, value=(0, 1), min=0, max=6)
    w.value = (5, 6) #upper non-overlapping range
    check_widget(w, cls=irsw, value=(5, 6), min=0, max=6)
    w.value = (-1, 4) #semi out-of-range
    check_widget(w, cls=irsw, value=(0, 4), min=0, max=6)
    w.lower = 2
    check_widget(w, cls=irsw, value=(2, 4), min=0, max=6)
    w.value = (-2, -1) #wholly out of range
    check_widget(w, cls=irsw, value=(0, 0), min=0, max=6)
    w.value = (7, 8)
    check_widget(w, cls=irsw, value=(6, 6), min=0, max=6)
    
    with nt.assert_raises(ValueError):
        w.min = 7
    with nt.assert_raises(ValueError):
        w.max = -1
    with nt.assert_raises(ValueError):
        w.lower = 5
    with nt.assert_raises(ValueError):
        w.upper = 1
    
    w = irsw(min=2, max=3)
    check_widget(w, min=2, max=3)
    w = irsw(min=100, max=200)
    check_widget(w, lower=125, upper=175, value=(125, 175))
    
    with nt.assert_raises(ValueError):
        irsw(value=(2, 4), lower=3)
    with nt.assert_raises(ValueError):
        irsw(value=(2, 4), upper=3)
    with nt.assert_raises(ValueError):
        irsw(value=(2, 4), lower=3, upper=3)
    with nt.assert_raises(ValueError):
        irsw(min=2, max=1)
    with nt.assert_raises(ValueError):
        irsw(lower=5)
    with nt.assert_raises(ValueError):
        irsw(upper=5)
    

def test_float_range_logic():
    frsw = widgets.FloatRangeSlider
    w = frsw(value=(.2, .4), min=0., max=.6)
    check_widget(w, cls=frsw, value=(.2, .4), min=0., max=.6)
    w.value = (.4, .2)
    check_widget(w, cls=frsw, value=(.2, .4), min=0., max=.6)
    w.value = (-.1, .7)
    check_widget(w, cls=frsw, value=(0., .6), min=0., max=.6)
    w.min = .3
    check_widget(w, cls=frsw, value=(.3, .6), min=.3, max=.6)
    w.max = .3
    check_widget(w, cls=frsw, value=(.3, .3), min=.3, max=.3)
    
    w.min = 0.
    w.max = .6
    w.lower = .2
    w.upper = .4
    check_widget(w, cls=frsw, value=(.2, .4), min=0., max=.6)
    w.value = (0., .1) #lower non-overlapping range
    check_widget(w, cls=frsw, value=(0., .1), min=0., max=.6)
    w.value = (.5, .6) #upper non-overlapping range
    check_widget(w, cls=frsw, value=(.5, .6), min=0., max=.6)
    w.value = (-.1, .4) #semi out-of-range
    check_widget(w, cls=frsw, value=(0., .4), min=0., max=.6)
    w.lower = .2
    check_widget(w, cls=frsw, value=(.2, .4), min=0., max=.6)
    w.value = (-.2, -.1) #wholly out of range
    check_widget(w, cls=frsw, value=(0., 0.), min=0., max=.6)
    w.value = (.7, .8)
    check_widget(w, cls=frsw, value=(.6, .6), min=.0, max=.6)
    
    with nt.assert_raises(ValueError):
        w.min = .7
    with nt.assert_raises(ValueError):
        w.max = -.1
    with nt.assert_raises(ValueError):
        w.lower = .5
    with nt.assert_raises(ValueError):
        w.upper = .1
    
    w = frsw(min=2, max=3)
    check_widget(w, min=2, max=3)
    w = frsw(min=1., max=2.)
    check_widget(w, lower=1.25, upper=1.75, value=(1.25, 1.75))
    
    with nt.assert_raises(ValueError):
        frsw(value=(2, 4), lower=3)
    with nt.assert_raises(ValueError):
        frsw(value=(2, 4), upper=3)
    with nt.assert_raises(ValueError):
        frsw(value=(2, 4), lower=3, upper=3)
    with nt.assert_raises(ValueError):
        frsw(min=.2, max=.1)
    with nt.assert_raises(ValueError):
        frsw(lower=5)
    with nt.assert_raises(ValueError):
        frsw(upper=5)


def test_multiple_selection():
    smw = widgets.SelectMultiple

    # degenerate multiple select
    w = smw()
    check_widget(w, value=tuple(), options=None, selected_labels=tuple())

    # don't accept random other value when no options
    with nt.assert_raises(KeyError):
        w.value = (2,)
    check_widget(w, value=tuple(), selected_labels=tuple())

    # basic multiple select
    w = smw(options=[(1, 1)], value=[1])
    check_widget(w, cls=smw, value=(1,), options=[(1, 1)])

    # don't accept random other value
    with nt.assert_raises(KeyError):
        w.value = w.value + (2,)
    check_widget(w, value=(1,), selected_labels=(1,))

    # change options
    w.options = w.options + [(2, 2)]
    check_widget(w, options=[(1, 1), (2,2)])

    # change value
    w.value = w.value + (2,)
    check_widget(w, value=(1, 2), selected_labels=(1, 2))

    # change value name
    w.selected_labels = (1,)
    check_widget(w, value=(1,))

    # don't accept random other names when no options
    with nt.assert_raises(KeyError):
        w.selected_labels = (3,)
    check_widget(w, value=(1,))

    # don't accept selected_label (from superclass)
    with nt.assert_raises(AttributeError):
        w.selected_label = 3

    # don't return selected_label (from superclass)
    with nt.assert_raises(AttributeError):
        print(w.selected_label)

    # dict style
    w.options = {1: 1}
    check_widget(w, options={1: 1})

    # updating
    with nt.assert_raises(KeyError):
        w.value = (2,)
    check_widget(w, options={1: 1})
