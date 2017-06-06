"""Test widgets."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2014 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from IPython.kernel.comm.tests.mock_comm import MockComm
from IPython.html.widgets import IntSlider, Box
from IPython.html.widgets import Widget
from IPython.display import display
import nose.tools as nt

_widget_attrs = {}

def construct_state(msgs, current_state=None):
    """Construct the current state of the object, based on update messages"""
    if current_state is None:
        current_state = {}
    for m in msgs:
        if m.data['method'] == 'update':
            current_state.update(m.data['state'])
    return current_state

def widget_open(self):
    """Open a MockComm."""
    if self.comm is None:
        if self._model_id is None:
            self.comm = MockComm(target_name=self._model_name)
            self._model_id = self.model_id
        else:
            self.comm = MockComm(target_name=self._model_name, comm_id=self._model_id)
        self.comm.on_msg(self._handle_msg)
        Widget.widgets[self.model_id] = self

        # first update
        self.send_state()

def setup():
    _widget_attrs['open'] = Widget.open
    Widget.open = widget_open

    _widget_attrs['_ipython_display_'] = Widget._ipython_display_
    def raise_not_implemented(*args, **kwargs):
        raise NotImplementedError()
    Widget._ipython_display_ = raise_not_implemented

def teardown():
    for attr, value in _widget_attrs.items():
        setattr(Widget, attr, value)

def test_initialize():
    """Test that a widget's model is instantiated on creation, before display."""
    a = IntSlider(min=-50, max=50, step=10)
    nt.assert_equal(len(a.comm.messages), 1)
    state = construct_state(a.comm.messages)
    nt.assert_equal(state['min'], -50)
    nt.assert_equal(state['max'], 50)
    nt.assert_equal(state['step'], 10)

def test_model_id_from_python():
    """Test that a widget correctly constructs an update message involving submodels."""
    a = IntSlider()
    b = Box([a])
    state = construct_state(b.comm.messages)
    nt.assert_equal(state['children'][0], 'IPY_MODEL_'+a.model_id)

def test_model_id_to_python():
    """Test that a widget correctly parses an update message involving submodels."""
    a = IntSlider()
    b = Box()
    msg = {'content': {'data': {'method': 'backbone', 
                                'sync_data': {'children': ['IPY_MODEL_'+a.model_id]}}}}
    b.comm.handle_msg(msg)
    nt.assert_is(b.children[0], a)

