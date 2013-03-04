"""Tests for IPython.lib.pretty.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2011, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Third-party imports
import nose.tools as nt

# Our own imports
from IPython.lib import pretty
from IPython.testing.decorators import skip_without

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class MyList(object):
    def __init__(self, content):
        self.content = content
    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text("MyList(...)")
        else:
            with p.group(3, "MyList(", ")"):
                for (i, child) in enumerate(self.content):
                    if i:
                        p.text(",")
                        p.breakable()
                    else:
                        p.breakable("")
                    p.pretty(child)


class MyDict(dict):
    def _repr_pretty_(self, p, cycle):
        p.text("MyDict(...)")


def test_indentation():
    """Test correct indentation in groups"""
    count = 40
    gotoutput = pretty.pretty(MyList(range(count)))
    expectedoutput = "MyList(\n" + ",\n".join("   %d" % i for i in range(count)) + ")"

    nt.assert_equals(gotoutput, expectedoutput)


def test_dispatch():
    """
    Test correct dispatching: The _repr_pretty_ method for MyDict
    must be found before the registered printer for dict.
    """
    gotoutput = pretty.pretty(MyDict())
    expectedoutput = "MyDict(...)"

    nt.assert_equals(gotoutput, expectedoutput)

@skip_without('xxlimited')
def test_pprint_heap_allocated_type():
    """
    Test that pprint works for heap allocated types.
    """
    import xxlimited
    output = pretty.pretty(xxlimited.Null)
    nt.assert_equal(output, 'xxlimited.Null')
