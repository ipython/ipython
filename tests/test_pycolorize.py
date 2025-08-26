# coding: utf-8
"""Test suite for our color utilities.

Authors
-------

* Min RK
"""
# -----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# our own
import sys
from IPython.utils.PyColorize import Parser
import io
import pytest


@pytest.fixture(scope="module", params=("linux", "nocolor", "lightbg", "neutral"))
def theme_name(request):
    yield request.param


# -----------------------------------------------------------------------------
# Test functions
# -----------------------------------------------------------------------------

sample = """
def function(arg, *args, kwarg=True, **kwargs):
    '''
    this is docs
    '''
    pass is True
    False == None

    with io.open(rf'unicode {1}', encoding='utf-8'):
        raise ValueError("escape \r sequence")

    print("wěird ünicoðe")

class Bar(Super):

    def __init__(self):
        super(Bar, self).__init__(1**2, 3^4, 5 or 6)
"""


def test_parse_sample(theme_name):
    """and test writing to a buffer"""
    buf = io.StringIO()
    p = Parser(theme_name=theme_name)
    p.format(sample, buf)
    buf.seek(0)
    f1 = buf.read()

    assert "ERROR" not in f1


def test_parse_error(theme_name):
    p = Parser(theme_name=theme_name)
    f1 = p.format(r"\ " if sys.version_info >= (3, 12) else ")", "str")
    if theme_name != "nocolor":
        assert "ERROR" in f1
