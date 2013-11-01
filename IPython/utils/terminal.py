# encoding: utf-8
"""
Utilities for working with terminals.

Authors:

* Brian E. Granger
* Fernando Perez
* Alexander Belchenko (e-mail: bialix AT ukr.net)
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

import os
import struct
import sys
import warnings

from . import py3compat

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

# This variable is part of the expected API of the module:
ignore_termtitle = True


def _term_clear():
    pass


if os.name == 'posix':
    def _term_clear():
        os.system('clear')


if sys.platform == 'win32':
    def _term_clear():
        os.system('cls')


def term_clear():
    _term_clear()


def toggle_set_term_title(val):
    """Control whether set_term_title is active or not.

    set_term_title() allows writing to the console titlebar.  In embedded
    widgets this can cause problems, so this call can be used to toggle it on
    or off as needed.

    The default state of the module is for the function to be disabled.

    Parameters
    ----------
      val : bool
        If True, set_term_title() actually writes to the terminal (using the
        appropriate platform-specific module).  If False, it is a no-op.
    """
    global ignore_termtitle
    ignore_termtitle = not(val)


def _set_term_title(*args,**kw):
    """Dummy no-op."""
    pass


def _set_term_title_xterm(title):
    """ Change virtual terminal title in xterm-workalikes """
    sys.stdout.write('\033]0;%s\007' % title)

if os.name == 'posix':
    TERM = os.environ.get('TERM','')
    if TERM.startswith('xterm'):
        _set_term_title = _set_term_title_xterm


if sys.platform == 'win32':
    try:
        import ctypes

        SetConsoleTitleW = ctypes.windll.kernel32.SetConsoleTitleW
        SetConsoleTitleW.argtypes = [ctypes.c_wchar_p]
    
        def _set_term_title(title):
            """Set terminal title using ctypes to access the Win32 APIs."""
            SetConsoleTitleW(title)
    except ImportError:
        def _set_term_title(title):
            """Set terminal title using the 'title' command."""
            global ignore_termtitle

            try:
                # Cannot be on network share when issuing system commands
                curr = py3compat.getcwd()
                os.chdir("C:")
                ret = os.system("title " + title)
            finally:
                os.chdir(curr)
            if ret:
                # non-zero return code signals error, don't try again
                ignore_termtitle = True


def set_term_title(title):
    """Set terminal title using the necessary platform-dependent calls."""
    if ignore_termtitle:
        return
    _set_term_title(title)


def freeze_term_title():
    warnings.warn("This function is deprecated, use toggle_set_term_title()")
    global ignore_termtitle
    ignore_termtitle = True


def get_terminal_size(defaultx=80, defaulty=25):
    return defaultx, defaulty


if sys.platform == 'win32':
    def get_terminal_size(defaultx=80, defaulty=25):
        """Return size of current terminal console.

        This function try to determine actual size of current working
        console window and return tuple (sizex, sizey) if success,
        or default size (defaultx, defaulty) otherwise.

        Dependencies: ctypes should be installed.

        Author: Alexander Belchenko (e-mail: bialix AT ukr.net)
        """
        try:
            import ctypes
        except ImportError:
            return defaultx, defaulty

        h = ctypes.windll.kernel32.GetStdHandle(-11)
        csbi = ctypes.create_string_buffer(22)
        res = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)

        if res:
            (bufx, bufy, curx, cury, wattr,
             left, top, right, bottom, maxx, maxy) = struct.unpack(
                "hhhhHhhhhhh", csbi.raw)
            sizex = right - left + 1
            sizey = bottom - top + 1
            return (sizex, sizey)
        else:
            return (defaultx, defaulty)

