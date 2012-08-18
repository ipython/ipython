"""Wrapper around linecache which decodes files to unicode according to PEP 263.

This is only needed for Python 2 - linecache in Python 3 does the same thing
itself.
"""
import functools
import linecache

from IPython.utils import py3compat
from IPython.utils import openpy

if py3compat.PY3:
    getline = linecache.getline
    
    # getlines has to be looked up at runtime, because doctests monkeypatch it.
    @functools.wraps(linecache.getlines)
    def getlines(filename, module_globals=None):
        return linecache.getlines(filename, module_globals=module_globals)

else:
    def getlines(filename, module_globals=None):
        """Get the lines (as unicode) for a file from the cache.
        Update the cache if it doesn't contain an entry for this file already."""
        linesb = linecache.getlines(filename, module_globals=module_globals)
        readline = openpy._list_readline(linesb)
        try:
            encoding, _ = openpy.detect_encoding(readline)
        except SyntaxError:
            encoding = 'ascii'
        return [l.decode(encoding, 'replace') for l in linesb]

    # This is a straight copy of linecache.getline
    def getline(filename, lineno, module_globals=None):
        lines = getlines(filename, module_globals)
        if 1 <= lineno <= len(lines):
            return lines[lineno-1]
        else:
            return ''
