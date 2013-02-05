"""Utilities to manipulate JSON objects.
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
import math
import re
import types
from datetime import datetime

try:
    # base64.encodestring is deprecated in Python 3.x
    from base64 import encodebytes
except ImportError:
    # Python 2.x
    from base64 import encodestring as encodebytes

from IPython.utils import py3compat
from IPython.utils.encoding import DEFAULT_ENCODING
next_attr_name = '__next__' if py3compat.PY3 else 'next'

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

# timestamp formats
ISO8601="%Y-%m-%dT%H:%M:%S.%f"
ISO8601_PAT=re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+$")

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

def rekey(dikt):
    """Rekey a dict that has been forced to use str keys where there should be
    ints by json."""
    for k in dikt.iterkeys():
        if isinstance(k, basestring):
            ik=fk=None
            try:
                ik = int(k)
            except ValueError:
                try:
                    fk = float(k)
                except ValueError:
                    continue
            if ik is not None:
                nk = ik
            else:
                nk = fk
            if nk in dikt:
                raise KeyError("already have key %r"%nk)
            dikt[nk] = dikt.pop(k)
    return dikt


def extract_dates(obj):
    """extract ISO8601 dates from unpacked JSON"""
    if isinstance(obj, dict):
        obj = dict(obj) # don't clobber
        for k,v in obj.iteritems():
            obj[k] = extract_dates(v)
    elif isinstance(obj, (list, tuple)):
        obj = [ extract_dates(o) for o in obj ]
    elif isinstance(obj, basestring):
        if ISO8601_PAT.match(obj):
            obj = datetime.strptime(obj, ISO8601)
    return obj

def squash_dates(obj):
    """squash datetime objects into ISO8601 strings"""
    if isinstance(obj, dict):
        obj = dict(obj) # don't clobber
        for k,v in obj.iteritems():
            obj[k] = squash_dates(v)
    elif isinstance(obj, (list, tuple)):
        obj = [ squash_dates(o) for o in obj ]
    elif isinstance(obj, datetime):
        obj = obj.strftime(ISO8601)
    return obj

def date_default(obj):
    """default function for packing datetime objects in JSON."""
    if isinstance(obj, datetime):
        return obj.strftime(ISO8601)
    else:
        raise TypeError("%r is not JSON serializable"%obj)


# constants for identifying png/jpeg data
PNG = b'\x89PNG\r\n\x1a\n'
JPEG = b'\xff\xd8'

def encode_images(format_dict):
    """b64-encodes images in a displaypub format dict

    Perhaps this should be handled in json_clean itself?

    Parameters
    ----------

    format_dict : dict
        A dictionary of display data keyed by mime-type

    Returns
    -------

    format_dict : dict
        A copy of the same dictionary,
        but binary image data ('image/png' or 'image/jpeg')
        is base64-encoded.

    """
    encoded = format_dict.copy()
    pngdata = format_dict.get('image/png')
    if isinstance(pngdata, bytes) and pngdata[:8] == PNG:
        encoded['image/png'] = encodebytes(pngdata).decode('ascii')
    jpegdata = format_dict.get('image/jpeg')
    if isinstance(jpegdata, bytes) and jpegdata[:2] == JPEG:
        encoded['image/jpeg'] = encodebytes(jpegdata).decode('ascii')
    return encoded


def json_clean(obj):
    """Clean an object to ensure it's safe to encode in JSON.

    Atomic, immutable objects are returned unmodified.  Sets and tuples are
    converted to lists, lists are copied and dicts are also copied.

    Note: dicts whose keys could cause collisions upon encoding (such as a dict
    with both the number 1 and the string '1' as keys) will cause a ValueError
    to be raised.

    Parameters
    ----------
    obj : any python object

    Returns
    -------
    out : object

      A version of the input which will not cause an encoding error when
      encoded as JSON.  Note that this function does not *encode* its inputs,
      it simply sanitizes it so that there will be no encoding errors later.

    Examples
    --------
    >>> json_clean(4)
    4
    >>> json_clean(range(10))
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    >>> sorted(json_clean(dict(x=1, y=2)).items())
    [('x', 1), ('y', 2)]
    >>> sorted(json_clean(dict(x=1, y=2, z=[1,2,3])).items())
    [('x', 1), ('y', 2), ('z', [1, 2, 3])]
    >>> json_clean(True)
    True
    """
    # types that are 'atomic' and ok in json as-is.  bool doesn't need to be
    # listed explicitly because bools pass as int instances
    atomic_ok = (unicode, int, types.NoneType)

    # containers that we need to convert into lists
    container_to_list = (tuple, set, types.GeneratorType)

    if isinstance(obj, float):
        # cast out-of-range floats to their reprs
        if math.isnan(obj) or math.isinf(obj):
            return repr(obj)
        return obj

    if isinstance(obj, atomic_ok):
        return obj

    if isinstance(obj, bytes):
        return obj.decode(DEFAULT_ENCODING, 'replace')

    if isinstance(obj, container_to_list) or (
        hasattr(obj, '__iter__') and hasattr(obj, next_attr_name)):
        obj = list(obj)

    if isinstance(obj, list):
        return [json_clean(x) for x in obj]

    if isinstance(obj, dict):
        # First, validate that the dict won't lose data in conversion due to
        # key collisions after stringification.  This can happen with keys like
        # True and 'true' or 1 and '1', which collide in JSON.
        nkeys = len(obj)
        nkeys_collapsed = len(set(map(str, obj)))
        if nkeys != nkeys_collapsed:
            raise ValueError('dict can not be safely converted to JSON: '
                             'key collision would lead to dropped values')
        # If all OK, proceed by making the new dict that will be json-safe
        out = {}
        for k,v in obj.iteritems():
            out[str(k)] = json_clean(v)
        return out

    # If we get here, we don't know how to handle the object, so we just get
    # its repr and return that.  This will catch lambdas, open sockets, class
    # objects, and any other complicated contraption that json can't encode
    return repr(obj)
