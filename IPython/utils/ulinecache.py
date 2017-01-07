"""
Wrapper around linecache which decodes files to unicode according to PEP 263.
"""
import functools
import linecache
import sys

from IPython.utils import py3compat
from IPython.utils import openpy

getline = linecache.getline

# getlines has to be looked up at runtime, because doctests monkeypatch it.
@functools.wraps(linecache.getlines)
def getlines(filename, module_globals=None):
    return linecache.getlines(filename, module_globals=module_globals)
