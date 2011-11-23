"""Test suite for our JSON utilities.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# stdlib
import json

# third party
import nose.tools as nt

# our own
from ..jsonutil import json_clean

#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------

def test():
    # list of input/expected output.  Use None for the expected output if it
    # can be the same as the input.
    pairs = [(1, None), # start with scalars
             (1.0, None),
             ('a', None),
             (True, None),
             (False, None),
             (None, None),
             # complex numbers for now just go to strings, as otherwise they
             # are unserializable
             (1j, '1j'),
             # Containers
             ([1, 2], None),
             ((1, 2), [1, 2]),
             (set([1, 2]), [1, 2]),
             (dict(x=1), None),
             ({'x': 1, 'y':[1,2,3], '1':'int'}, None),
             # More exotic objects
             ((x for x in range(3)), [0, 1, 2]),
             (iter([1, 2]), [1, 2]),
             ]
    
    for val, jval in pairs:
        if jval is None:
            jval = val
        out = json_clean(val)
        # validate our cleanup
        nt.assert_equal(out, jval)
        # and ensure that what we return, indeed encodes cleanly
        json.loads(json.dumps(out))


def test_lambda():
    jc = json_clean(lambda : 1)
    nt.assert_true(jc.startswith('<function <lambda> at '))
    json.dumps(jc)


def test_exception():
    bad_dicts = [{1:'number', '1':'string'},
                 {True:'bool', 'True':'string'},
                 ]
    for d in bad_dicts:
        nt.assert_raises(ValueError, json_clean, d)
    
