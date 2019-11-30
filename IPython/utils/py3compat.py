"""Compatibility tricks for Python 3. Mainly to do with unicode.

This file is deprecated and will be removed in a future version.
"""
import platform
import builtins as builtin_mod

from .encoding import DEFAULT_ENCODING

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


def safe_unicode(e):
    """unicode(e) with various fallbacks. Used for exceptions, which may not be
    safe to call unicode() on.
    """
    try:
        return str(e)
    except UnicodeError:
        pass

    try:
        return repr(e)
    except UnicodeError:
        pass

    return u'Unrecoverably corrupt evalue'


# keep reference to builtin_mod because the kernel overrides that value
# to forward requests to a frontend.
def input(prompt=''):
    return builtin_mod.input(prompt)

u_format = lambda s:s

PYPY = platform.python_implementation() == "PyPy"


