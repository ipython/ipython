# coding: utf-8
"""Compatibility tricks for Python 3. Mainly to do with unicode."""
import sys

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
    
    def isidentifier(s, dotted=False):
        if dotted:
            return all(isidentifier(a) for a in s.split("."))
        return s.isidentifier()
    
    open = orig_open

else:
    PY3 = False
    
    input = raw_input
    builtin_mod_name = "__builtin__"
    
    str_to_unicode = decode
    unicode_to_str = encode
    str_to_bytes = no_code
    bytes_to_str = no_code
    
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

def execfile(fname, glob, loc=None):
    loc = loc if (loc is not None) else glob
    exec compile(open(fname).read(), fname, 'exec') in glob, loc
