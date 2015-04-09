# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import nose.tools as nt

from .. import jslink, jsdlink, ToggleButton
from .test_interaction import setup, teardown

def test_jslink_args():
    with nt.assert_raises(TypeError):
        jslink()
    w1 = ToggleButton()
    with nt.assert_raises(TypeError):
        jslink((w1, 'value'))
    
    w2 = ToggleButton()
    jslink((w1, 'value'), (w2, 'value'))

    with nt.assert_raises(TypeError):
        jslink((w1, 'value'), (w2, 'nosuchtrait'))

    with nt.assert_raises(TypeError):
        jslink((w1, 'value'), (w2, 'traits'))

def test_jsdlink_args():
    with nt.assert_raises(TypeError):
        jsdlink()
    w1 = ToggleButton()
    with nt.assert_raises(TypeError):
        jsdlink((w1, 'value'))
    
    w2 = ToggleButton()
    jsdlink((w1, 'value'), (w2, 'value'))

    with nt.assert_raises(TypeError):
        jsdlink((w1, 'value'), (w2, 'nosuchtrait'))

    with nt.assert_raises(TypeError):
        jsdlink((w1, 'value'), (w2, 'traits'))
