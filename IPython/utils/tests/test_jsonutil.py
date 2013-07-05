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
import datetime
import json
from base64 import decodestring

# third party
import nose.tools as nt

# our own
from IPython.testing import decorators as dec
from IPython.utils import jsonutil, tz
from ..jsonutil import json_clean, encode_images
from ..py3compat import unicode_to_str, str_to_bytes

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



@dec.parametric
def test_encode_images():
    # invalid data, but the header and footer are from real files
    pngdata = b'\x89PNG\r\n\x1a\nblahblahnotactuallyvalidIEND\xaeB`\x82'
    jpegdata = b'\xff\xd8\xff\xe0\x00\x10JFIFblahblahjpeg(\xa0\x0f\xff\xd9'
    
    fmt = {
        'image/png'  : pngdata,
        'image/jpeg' : jpegdata,
    }
    encoded = encode_images(fmt)
    for key, value in fmt.iteritems():
        # encoded has unicode, want bytes
        decoded = decodestring(encoded[key].encode('ascii'))
        yield nt.assert_equal(decoded, value)
    encoded2 = encode_images(encoded)
    yield nt.assert_equal(encoded, encoded2)
    
    b64_str = {}
    for key, encoded in encoded.iteritems():
        b64_str[key] = unicode_to_str(encoded)
    encoded3 = encode_images(b64_str)
    yield nt.assert_equal(encoded3, b64_str)
    for key, value in fmt.iteritems():
        # encoded3 has str, want bytes
        decoded = decodestring(str_to_bytes(encoded3[key]))
        yield nt.assert_equal(decoded, value)

def test_lambda():
    jc = json_clean(lambda : 1)
    assert isinstance(jc, str)
    assert '<lambda>' in jc
    json.dumps(jc)

def test_extract_dates():
    timestamps = [
        '2013-07-03T16:34:52.249482',
        '2013-07-03T16:34:52.249482Z',
        '2013-07-03T16:34:52.249482Z-0800',
        '2013-07-03T16:34:52.249482Z+0800',
        '2013-07-03T16:34:52.249482Z+08:00',
        '2013-07-03T16:34:52.249482Z-08:00',
        '2013-07-03T16:34:52.249482-0800',
        '2013-07-03T16:34:52.249482+0800',
        '2013-07-03T16:34:52.249482+08:00',
        '2013-07-03T16:34:52.249482-08:00',
    ]
    extracted = jsonutil.extract_dates(timestamps)
    ref = extracted[0]
    for dt in extracted:
        nt.assert_true(isinstance(dt, datetime.datetime))
        nt.assert_equal(dt, ref)

def test_date_default():
    data = dict(today=datetime.datetime.now(), utcnow=tz.utcnow())
    jsondata = json.dumps(data, default=jsonutil.date_default)
    nt.assert_in("+00", jsondata)
    nt.assert_equal(jsondata.count("+00"), 1)
    extracted = jsonutil.extract_dates(json.loads(jsondata))
    for dt in extracted.values():
        nt.assert_true(isinstance(dt, datetime.datetime))

def test_exception():
    bad_dicts = [{1:'number', '1':'string'},
                 {True:'bool', 'True':'string'},
                 ]
    for d in bad_dicts:
        nt.assert_raises(ValueError, json_clean, d)
    
