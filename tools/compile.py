#!/usr/bin/env python
"""Script to check that all code in a directory compiles correctly.

Usage:

  compile.py

This script verifies that all Python files in the directory where run, and all
of its subdirectories, compile correctly.

Before a release, call this script from the top-level directory.
"""

import sys

from toollib import compile_tree

if __name__ == '__main__':
    compile_tree()
