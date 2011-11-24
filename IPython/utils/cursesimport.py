# encoding: utf-8
"""
See if we have curses.
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

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

# Curses and termios are Unix-only modules
try:
    import curses
    # We need termios as well, so if its import happens to raise, we bail on
    # using curses altogether.
    import termios
except ImportError:
    use_curses = False
else:
    # Curses on Solaris may not be complete, so we can't use it there
    use_curses = hasattr(curses,'initscr')