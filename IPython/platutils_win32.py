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

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Ville']
__license__ = Release.license

import os

ignore_termtitle = False

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
