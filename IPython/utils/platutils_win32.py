# -*- coding: utf-8 -*-
""" Platform specific utility functions, win32 version

Importing this module directly is not portable - rather, import platutils 
to use these functions in platform agnostic fashion.
"""

#*****************************************************************************
#       Copyright (C) 2001-2006 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import os

ignore_termtitle = True

try:
    import ctypes

    SetConsoleTitleW = ctypes.windll.kernel32.SetConsoleTitleW
    SetConsoleTitleW.argtypes = [ctypes.c_wchar_p]
    
    def set_term_title(title):
        """Set terminal title using ctypes to access the Win32 APIs."""
        SetConsoleTitleW(title)

except ImportError:
    def set_term_title(title):
        """Set terminal title using the 'title' command."""
        global ignore_termtitle

        try:
            # Cannot be on network share when issuing system commands
            curr = os.getcwd()
            os.chdir("C:")
            ret = os.system("title " + title)
        finally:
            os.chdir(curr)
        if ret:
            # non-zero return code signals error, don't try again
            ignore_termtitle = True

def find_cmd(cmd):
    """Find the full path to a .bat or .exe using the win32api module."""
    try:
        import win32api
    except ImportError:
        raise ImportError('you need to have pywin32 installed for this to work')
    else:
        try:
            (path, offest) = win32api.SearchPath(os.environ['PATH'],cmd + '.exe')
        except:
            (path, offset) = win32api.SearchPath(os.environ['PATH'],cmd + '.bat')
    return path


def get_long_path_name(path):
    """Get a long path name (expand ~) on Windows using ctypes.

    Examples
    --------

    >>> get_long_path_name('c:\\docume~1')
    u'c:\\\\Documents and Settings'

    """
    try:
        import ctypes
    except ImportError:
        raise ImportError('you need to have ctypes installed for this to work')
    _GetLongPathName = ctypes.windll.kernel32.GetLongPathNameW
    _GetLongPathName.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p,
        ctypes.c_uint ]

    buf = ctypes.create_unicode_buffer(260)
    rv = _GetLongPathName(path, buf, 260)
    if rv == 0 or rv > 260:
        return path
    else:
        return buf.value
