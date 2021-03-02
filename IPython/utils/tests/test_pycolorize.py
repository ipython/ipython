# coding: utf-8
"""Test suite for our color utilities.

Authors
-------

* Min RK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# our own
from IPython.utils.PyColorize import Parser
import io

import pytest

#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------

sample = u"""
def function(arg, *args, kwarg=True, **kwargs):
    '''
    this is docs
    '''
    pass is True
    False == None

    with io.open(ru'unicode'):
        raise ValueError("\n escape \r sequence")

    print("wěird ünicoðe")

class Bar(Super):

    def __init__(self):
        super(Bar, self).__init__(1**2, 3^4, 5 or 6)
"""

@pytest.mark.parametrize("style", ('Linux', 'NoColor','LightBG', 'Neutral'))
def test_loop_colors(style):
    def test_unicode_colorize():
        p = Parser(style=style)
        f1 = p.format('1/0', 'str')
        f2 = p.format(u'1/0', 'str')
        assert f1 == f2

    def test_parse_sample():
        """and test writing to a buffer"""
        buf = io.StringIO()
        p = Parser(style=style)
        p.format(sample, buf)
        buf.seek(0)
        f1 = buf.read()

        assert 'ERROR' not in f1

    def test_parse_error():
        p = Parser(style=style)
        f1 = p.format(')', 'str')
        if style != 'NoColor':
            assert 'ERROR' in f1

    test_unicode_colorize()
    test_parse_sample()
    test_parse_error()
