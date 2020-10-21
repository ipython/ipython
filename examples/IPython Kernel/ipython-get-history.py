#!/usr/bin/env python
"""Extract a session from the IPython input history.

Usage:
  ipython-get-history.py sessionnumber [outputfile]

If outputfile is not given, the relevant history is written to stdout. If
outputfile has a .py extension, the translated history (without IPython's
special syntax) will be extracted.

Example:
  ./ipython-get-history.py 57 record.ipy


This script is a simple demonstration of HistoryAccessor. It should be possible
to build much more flexible and powerful tools to browse and pull from the
history database.
"""
import sys
from pathlib import Path

from IPython.core.history import HistoryAccessor

session_number = int(sys.argv[1])
if len(sys.argv) > 2:
    filepath = Path(sys.argv[2])
    dest = open(filepath, "w")
    raw = not filepath.name.endswith(".py")
else:
    dest = sys.stdout
    raw = True

with dest:
    dest.write("# coding: utf-8\n")

    # Profiles other than 'default' can be specified here with a profile= argument:
    hist = HistoryAccessor()

    for session, lineno, cell in hist.get_range(session=session_number, raw=raw):
      dest.write(cell + '\n')
