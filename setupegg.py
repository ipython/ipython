#!/usr/bin/env python
"""Wrapper to run setup.py using setuptools."""

# Import setuptools and call the actual setup
import setuptools
with open(path, 'rb') as f:
    exec(compile(f.read(), 'setup.py', 'exec'))
