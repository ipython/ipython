# coding: utf-8
"""Compatibility tricks for Python 3. Mainly to do with unicode."""
import functools
import os
import sys
import re
import types

from .encoding import DEFAULT_ENCODING

orig_open = open

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

def _modify_str_or_docstring(str_change_func):
    @functools.wraps(str_change_func)
    def wrapper(func_or_str):
        if isinstance(func_or_str, string_types):
            func = None
            doc = func_or_str
        else:
            func = func_or_str
            doc = func.__doc__
        
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

if sys.version_info[0] >= 3:
    PY3 = True
    
    # keep reference to builtin_mod because the kernel overrides that value
    # to forward requests to a frontend.
    def input(prompt=''):
        return builtin_mod.input(prompt)
    
    builtin_mod_name = "builtins"
    import builtins as builtin_mod
    
    str_to_unicode = no_code
    unicode_to_str = no_code
    str_to_bytes = encode
    bytes_to_str = decode
    cast_bytes_py2 = no_code
    cast_unicode_py2 = no_code
    
    string_types = (str,)
    unicode_type = str
    
    def isidentifier(s, dotted=False):
        if dotted:
            return all(isidentifier(a) for a in s.split("."))
        return s.isidentifier()
    
    open = orig_open
    xrange = range
    def iteritems(d): return iter(d.items())
    def itervalues(d): return iter(d.values())
    getcwd = os.getcwd
    
    MethodType = types.MethodType
    
    def execfile(fname, glob, loc=None):
        loc = loc if (loc is not None) else glob
        with open(fname, 'rb') as f:
            exec(compile(f.read(), fname, 'exec'), glob, loc)
    
    # Refactor print statements in doctests.
    _print_statement_re = re.compile(r"\bprint (?P<expr>.*)$", re.MULTILINE)
    def _print_statement_sub(match):
        expr = match.groups('expr')
        return "print(%s)" % expr
    
    @_modify_str_or_docstring
    def doctest_refactor_print(doc):
        """Refactor 'print x' statements in a doctest to print(x) style. 2to3
        unfortunately doesn't pick up on our doctests.
        
        Can accept a string or a function, so it can be used as a decorator."""
        return _print_statement_re.sub(_print_statement_sub, doc)
    
    # Abstract u'abc' syntax:
    @_modify_str_or_docstring
    def u_format(s):
        """"{u}'abc'" --> "'abc'" (Python 3)
        
        Accepts a string or a function, so it can be used as a decorator."""
        return s.format(u='')

else:
    PY3 = False
    
    # keep reference to builtin_mod because the kernel overrides that value
    # to forward requests to a frontend.
    def input(prompt=''):
        return builtin_mod.raw_input(prompt)
    
    builtin_mod_name = "__builtin__"
    import __builtin__ as builtin_mod
    
    str_to_unicode = decode
    unicode_to_str = encode
    str_to_bytes = no_code
    bytes_to_str = no_code
    cast_bytes_py2 = cast_bytes
    cast_unicode_py2 = cast_unicode
    
    string_types = (str, unicode)
    unicode_type = unicode
    
    import re
    _name_re = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*$")
    def isidentifier(s, dotted=False):
        if dotted:
            return all(isidentifier(a) for a in s.split("."))
        return bool(_name_re.match(s))
    
    class open(object):
        """Wrapper providing key part of Python 3 open() interface."""
        def __init__(self, fname, mode="r", encoding="utf-8"):
            self.f = orig_open(fname, mode)
            self.enc = encoding
        
        def write(self, s):
            return self.f.write(s.encode(self.enc))
        
        def read(self, size=-1):
            return self.f.read(size).decode(self.enc)
        
        def close(self):
            return self.f.close()
        
        def __enter__(self):
            return self
        
        def __exit__(self, etype, value, traceback):
            self.f.close()
    
    xrange = xrange
    def iteritems(d): return d.iteritems()
    def itervalues(d): return d.itervalues()
    getcwd = os.getcwdu

    def MethodType(func, instance):
        return types.MethodType(func, instance, type(instance))
    
    def doctest_refactor_print(func_or_str):
        return func_or_str


    # Abstract u'abc' syntax:
    @_modify_str_or_docstring
    def u_format(s):
        """"{u}'abc'" --> "u'abc'" (Python 2)
        
        Accepts a string or a function, so it can be used as a decorator."""
        return s.format(u='u')

    if sys.platform == 'win32':
        def execfile(fname, glob=None, loc=None):
            loc = loc if (loc is not None) else glob
            # The rstrip() is necessary b/c trailing whitespace in files will
            # cause an IndentationError in Python 2.6 (this was fixed in 2.7,
            # but we still support 2.6).  See issue 1027.
            scripttext = builtin_mod.open(fname).read().rstrip() + '\n'
            # compile converts unicode filename to str assuming
            # ascii. Let's do the conversion before calling compile
            if isinstance(fname, unicode):
                filename = unicode_to_str(fname)
            else:
                filename = fname
            exec(compile(scripttext, filename, 'exec'), glob, loc)
    else:
        def execfile(fname, *where):
            if isinstance(fname, unicode):
                filename = fname.encode(sys.getfilesystemencoding())
            else:
                filename = fname
            builtin_mod.execfile(filename, *where)


def annotate(**kwargs):
    """Python 3 compatible function annotation for Python 2."""
    if not kwargs:
        raise ValueError('annotations must be provided as keyword arguments')
    def dec(f):
        if hasattr(f, '__annotations__'):
            for k, v in kwargs.items():
                f.__annotations__[k] = v
        else:
            f.__annotations__ = kwargs
        return f
    return dec


# Parts below taken from six:
# Copyright (c) 2010-2013 Benjamin Peterson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    return meta("_NewBase", bases, {})
