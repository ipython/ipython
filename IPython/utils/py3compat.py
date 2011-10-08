# coding: utf-8
"""Compatibility tricks for Python 3. Mainly to do with unicode."""
import sys
import re
import types

orig_open = open

def no_code(x, encoding=None):
    return x

def decode(s, encoding=None):
    encoding = encoding or sys.stdin.encoding or sys.getdefaultencoding()
    return s.decode(encoding, "replace")

def encode(u, encoding=None):
    encoding = encoding or sys.stdin.encoding or sys.getdefaultencoding()
    return u.encode(encoding, "replace")
    
def cast_unicode(s, encoding=None):
    if isinstance(s, bytes):
        return decode(s, encoding)
    return s

def cast_bytes(s, encoding=None):
    if not isinstance(s, bytes):
        return encode(s, encoding)
    return s

if sys.version_info[0] >= 3:
    PY3 = True
    
    input = input
    builtin_mod_name = "builtins"
    
    str_to_unicode = no_code
    unicode_to_str = no_code
    str_to_bytes = encode
    bytes_to_str = decode
    cast_bytes_py2 = no_code
    
    def isidentifier(s, dotted=False):
        if dotted:
            return all(isidentifier(a) for a in s.split("."))
        return s.isidentifier()
    
    open = orig_open
    
    MethodType = types.MethodType
    
    def execfile(fname, glob, loc=None):
        loc = loc if (loc is not None) else glob
        exec compile(open(fname).read(), fname, 'exec') in glob, loc
    
    # Refactor print statements in doctests.
    _print_statement_re = re.compile(r"\bprint (?P<expr>.*)$", re.MULTILINE)
    def _print_statement_sub(match):
        expr = match.groups('expr')
        return "print(%s)" % expr
    def doctest_refactor_print(func_or_str):
        """Refactor 'print x' statements in a doctest to print(x) style. 2to3
        unfortunately doesn't pick up on our doctests.
        
        Can accept a string or a function, so it can be used as a decorator."""
        if isinstance(func_or_str, str):
            func = None
            doc = func_or_str
        else:
            func = func_or_str
            doc = func.__doc__
        doc = _print_statement_re.sub(_print_statement_sub, doc)
        
        if func:
            func.__doc__ = doc
            return func
        return doc
        

else:
    PY3 = False
    
    input = raw_input
    builtin_mod_name = "__builtin__"
    
    str_to_unicode = decode
    unicode_to_str = encode
    str_to_bytes = no_code
    bytes_to_str = no_code
    cast_bytes_py2 = cast_bytes
    
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
    
    def MethodType(func, instance):
        return types.MethodType(func, instance, type(instance))
    
    # don't override system execfile on 2.x:
    execfile = execfile
    
    def doctest_refactor_print(func_or_str):
        return func_or_str

