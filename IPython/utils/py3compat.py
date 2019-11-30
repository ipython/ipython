# coding: utf-8
"""Compatibility tricks for Python 3. Mainly to do with unicode.

This file is deprecated and will be removed in a future version.
"""
import functools
import os
import sys
import re
import shutil
import types
import platform

from .encoding import DEFAULT_ENCODING

def no_code(x, encoding=None):
    return x

def decode(s, encoding=None):
    encoding = encoding or DEFAULT_ENCODING
    return s.decode(encoding, "replace")

def encode(u, encoding=None):
    encoding = encoding or DEFAULT_ENCODING
    return u.encode(encoding, "replace")


def cast_unicode(s, encoding=None):
    if isinstance(s, bytes):
        return decode(s, encoding)
    return s

def cast_bytes(s, encoding=None):
    if not isinstance(s, bytes):
        return encode(s, encoding)
    return s

def buffer_to_bytes(buf):
    """Cast a buffer object to bytes"""
    if not isinstance(buf, bytes):
        buf = bytes(buf)
    return buf

def _modify_str_or_docstring(str_change_func):
    @functools.wraps(str_change_func)
    def wrapper(func_or_str):
        if isinstance(func_or_str, string_types):
            func = None
            doc = func_or_str
        else:
            func = func_or_str
            doc = func.__doc__

        # PYTHONOPTIMIZE=2 strips docstrings, so they can disappear unexpectedly
        if doc is not None:
            doc = str_change_func(doc)

        if func:
            func.__doc__ = doc
            return func
        return doc
    return wrapper

def safe_unicode(e):
    """unicode(e) with various fallbacks. Used for exceptions, which may not be
    safe to call unicode() on.
    """
    try:
        return unicode_type(e)
    except UnicodeError:
        pass

    try:
        return str_to_unicode(str(e))
    except UnicodeError:
        pass

    try:
        return str_to_unicode(repr(e))
    except UnicodeError:
        pass

    return u'Unrecoverably corrupt evalue'


# keep reference to builtin_mod because the kernel overrides that value
# to forward requests to a frontend.
def input(prompt=''):
    return builtin_mod.input(prompt)

import builtins as builtin_mod

str_to_unicode = no_code
unicode_to_str = no_code
str_to_bytes = encode
bytes_to_str = decode
cast_bytes_py2 = no_code
cast_unicode_py2 = no_code
buffer_to_bytes_py2 = no_code

string_types = (str,)
unicode_type = str

which = shutil.which


# Abstract u'abc' syntax:
@_modify_str_or_docstring
def u_format(s):
    """"{u}'abc'" --> "'abc'" (Python 3)

    Accepts a string or a function, so it can be used as a decorator."""
    return s.format(u='')

PYPY = platform.python_implementation() == "PyPy"


