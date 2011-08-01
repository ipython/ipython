import sys

def no_code(x, encoding=None):
    return x

def decode(s, encoding=None):
    encoding = encoding or sys.stdin.encoding or sys.getdefaultencoding()
    return s.decode(encoding, "replace")

def encode(u, encoding=None):
    encoding = encoding or sys.stdin.encoding or sys.getdefaultencoding()
    return u.encode(encoding, "replace")

if sys.version_info[0] >= 3:
    PY3 = True
    
    input = input
    builtin_mod_name = "builtins"
    
    str_to_unicode = no_code
    unicode_to_str = no_code
    str_to_bytes = encode
    bytes_to_str = decode
    
else:
    PY3 = False
    
    input = raw_input
    builtin_mod_name = "__builtin__"
    
    str_to_unicode = decode
    unicode_to_str = encode
    str_to_bytes = no_code
    bytes_to_str = no_code

def execfile(fname, glob, loc):
    exec compile(open(fname).read(), fname, 'exec') in glob, loc
