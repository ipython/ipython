#!/usr/bin/env python
"""Wrapper to run setup.py using setuptools."""

# Python 3 compatibility
try:
    execfile
except:
    def execfile(filename, globals, locals=None):
        locals = locals or globals
        exec(compile(open(filename).read(), filename, "exec"), globals, locals)

# Import setuptools and call the actual setup
import setuptools
execfile('setup.py', globals())
