"""Add some assert methods to nose.tools. These were added in Python 2.7/3.1, so
once we stop testing on Python 2.6, this file can be removed.
"""

import nose.tools as nt

def assert_in(item, collection):
    assert item in collection, '%r not in %r' % (item, collection)

if not hasattr(nt, 'assert_in'):
    nt.assert_in = assert_in

def assert_not_in(item, collection):
    assert item not in collection, '%r in %r' % (item, collection)

if not hasattr(nt, 'assert_not_in'):
    nt.assert_not_in = assert_not_in

def assert_is_none(obj):
    assert obj is None, '%r is not None' % obj

if not hasattr(nt, 'assert_is_none'):
    nt.assert_is_none = assert_is_none

def assert_is_not_none(obj):
    assert obj is not None, '%r is None' % obj

if not hasattr(nt, 'assert_is_not_none'):
    nt.assert_is_not_none = assert_is_not_none
