# encoding: utf-8
"""
Utilities for working with external processes.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib
import os
import sys
import shlex

# Our own
if sys.platform == 'win32':
    from ._process_win32 import _find_cmd, system, getoutput, AvoidUNCPath, arg_split
else:
    from ._process_posix import _find_cmd, system, getoutput, arg_split


from ._process_common import getoutputerror, get_output_error_code

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class FindCmdError(Exception):
    pass


def find_cmd(cmd):
    """Find absolute path to executable cmd in a cross platform manner.

    This function tries to determine the full path to a command line program
    using `which` on Unix/Linux/OS X and `win32api` on Windows.  Most of the
    time it will use the version that is first on the users `PATH`.

    Warning, don't use this to find IPython command line programs as there
    is a risk you will find the wrong one.  Instead find those using the
    following code and looking for the application itself::

        from IPython.utils.path import get_ipython_module_path
        from IPython.utils.process import pycmd2argv
        argv = pycmd2argv(get_ipython_module_path('IPython.terminal.ipapp'))

    Parameters
    ----------
    cmd : str
        The command line program to look for.
    """
    try:
        path = _find_cmd(cmd).rstrip()
    except OSError:
        raise FindCmdError('command could not be found: %s' % cmd)
    # which returns empty if not found
    if path == '':
        raise FindCmdError('command could not be found: %s' % cmd)
    return os.path.abspath(path)


def is_cmd_found(cmd):
    """Check whether executable `cmd` exists or not and return a bool."""
    try:
        find_cmd(cmd)
        return True
    except FindCmdError:
        return False


def pycmd2argv(cmd):
    r"""Take the path of a python command and return a list (argv-style).

    This only works on Python based command line programs and will find the
    location of the ``python`` executable using ``sys.executable`` to make
    sure the right version is used.

    For a given path ``cmd``, this returns [cmd] if cmd's extension is .exe,
    .com or .bat, and [, cmd] otherwise.

    Parameters
    ----------
    cmd : string
      The path of the command.

    Returns
    -------
    argv-style list.
    """
    ext = os.path.splitext(cmd)[1]
    if ext in ['.exe', '.com', '.bat']:
        return [cmd]
    else:
        return [sys.executable, cmd]


def abbrev_cwd():
    """ Return abbreviated version of cwd, e.g. d:mydir """
    cwd = os.getcwdu().replace('\\','/')
    drivepart = ''
    tail = cwd
    if sys.platform == 'win32':
        if len(cwd) < 4:
            return cwd
        drivepart,tail = os.path.splitdrive(cwd)


    parts = tail.split('/')
    if len(parts) > 2:
        tail = '/'.join(parts[-2:])

    return (drivepart + (
        cwd == '/' and '/' or tail))
