#!/usr/bin/env python
"""Wrapper to run setup.py using setuptools."""

# Import setuptools and call the actual setup
import setuptools
from pathlib import Path

f = Path('setup.py')
exec(compile(f.read_text(), 'setup.py', 'exec'))
