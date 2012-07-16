"""Utilities for working with Python source files.

Exposes various functions from recent Python standard libraries, along with
equivalents for older Python versions.
"""
import os.path

try:    # Python 3.2
    from imp import source_from_cache, cache_from_source
except ImportError:
    # Python <= 3.1: .pyc files go next to .py
    def source_from_cache(path):
        basename, ext = os.path.splitext(path)
        if ext not in ('.pyc', '.pyo'):
            raise ValueError('Not a cached Python file extension', ext)
        # Should we look for .pyw files?
        return basename + '.py'
    
    def cache_from_source(path, debug_override=None):
        if debug_override is None:
            debug_override = __debug__
        basename, ext = os.path.splitext(path)
        return basename + '.pyc' if debug_override else '.pyo'
