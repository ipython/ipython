# encoding: utf-8
"""A fancy version of Python's builtin :func:`dir` function.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from .py3compat import string_types

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


def safe_hasattr(obj, attr):
    """In recent versions of Python, hasattr() only catches AttributeError.
    This catches all errors.
    """
    try:
        getattr(obj, attr)
        return True
    except:
        return False


def get_class_members(cls):
    ret = dir(cls)
    if safe_hasattr(cls, '__bases__'):
        try:
            bases = cls.__bases__
        except AttributeError:
            # `obj` lied to hasattr (e.g. Pyro), ignore
            pass
        else:
            for base in bases:
                ret.extend(get_class_members(base))
    return ret


def dir2(obj):
    """dir2(obj) -> list of strings

    Extended version of the Python builtin dir(), which does a few extra
    checks, and supports common objects with unusual internals that confuse
    dir(), such as Traits and PyCrust.

    This version is guaranteed to return only a list of true strings, whereas
    dir() returns anything that objects inject into themselves, even if they
    are later not really valid for attribute access (many extension libraries
    have such bugs).
    """

    # Start building the attribute list via dir(), and then complete it
    # with a few extra special-purpose calls.

    try:
        words = set(dir(obj))
    except Exception:
        # TypeError: dir(obj) does not return a list
        words = set()

    if safe_hasattr(obj, '__class__'):
        #words.add('__class__')
        words |= set(get_class_members(obj.__class__))


    # for objects with Enthought's traits, add trait_names() list
    # for PyCrust-style, add _getAttributeNames() magic method list
    for attr in ('trait_names', '_getAttributeNames'):
        try:
            func = getattr(obj, attr)
            if callable(func):
                words |= set(func())
        except:
            # TypeError: obj is class not instance
            pass

    # filter out non-string attributes which may be stuffed by dir() calls
    # and poor coding in third-party modules

    words = [w for w in words if isinstance(w, string_types)]
    return sorted(words)
