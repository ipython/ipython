# encoding: utf-8
"""
Utilities for warnings.  Shoudn't we just use the built in warnings module.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import sys

from IPython.utils import io


def warn(msg,level=2,exit_val=1):
    """Standard warning printer. Gives formatting consistency.

    Output is sent to io.stderr (sys.stderr by default).

    Options:

    -level(2): allows finer control:
      0 -> Do nothing, dummy function.
      1 -> Print message.
      2 -> Print 'WARNING:' + message. (Default level).
      3 -> Print 'ERROR:' + message.
      4 -> Print 'FATAL ERROR:' + message and trigger a sys.exit(exit_val).

    -exit_val (1): exit value returned by sys.exit() for a level 4
    warning. Ignored for all other levels."""

    if level>0:
        header = ['','','WARNING: ','ERROR: ','FATAL ERROR: ']
        print(header[level], msg, sep='', file=io.stderr)
        if level == 4:
            print('Exiting.\n', file=io.stderr)
            sys.exit(exit_val)

            
def info(msg):
    """Equivalent to warn(msg,level=1)."""

    warn(msg,level=1)

    
def error(msg):
    """Equivalent to warn(msg,level=3)."""

    warn(msg,level=3)

    
def fatal(msg,exit_val=1):
    """Equivalent to warn(msg,exit_val=exit_val,level=4)."""

    warn(msg,exit_val=exit_val,level=4)

