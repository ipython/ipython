# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import nose.tools as nt

from .. import link, dlink, ToggleButton
from .test_interaction import setup, teardown

def test_link_args():
    with nt.assert_raises(TypeError):
        link()
    w1 = ToggleButton()
    with nt.assert_raises(TypeError):
        link((w1, 'value'))
    
    w2 = ToggleButton()
    link((w1, 'value'), (w2, 'value'))

    with nt.assert_raises(TypeError):
        link((w1, 'value'), (w2, 'nosuchtrait'))

    with nt.assert_raises(TypeError):
        link((w1, 'value'), (w2, 'traits'))

def test_dlink_args():
    with nt.assert_raises(TypeError):
        dlink()
    w1 = ToggleButton()
    with nt.assert_raises(TypeError):
        dlink((w1, 'value'))
    
    w2 = ToggleButton()
    dlink((w1, 'value'), (w2, 'value'))

    with nt.assert_raises(TypeError):
        dlink((w1, 'value'), (w2, 'nosuchtrait'))

    with nt.assert_raises(TypeError):
        dlink((w1, 'value'), (w2, 'traits'))
