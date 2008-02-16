"""Set of functions to work with console on Windows.
"""

#*****************************************************************************
#       Copyright (C) 2005 Alexander Belchenko <bialix@ukr.net>
#
#                This file is placed in the public domain.
#
#*****************************************************************************

__author__  = 'Alexander Belchenko (e-mail: bialix AT ukr.net)'
__license__ = 'Public domain'

import struct

try:
    import ctypes
except ImportError:
    ctypes = None

def get_console_size(defaultx=80, defaulty=25):
    """ Return size of current console.

    This function try to determine actual size of current working
    console window and return tuple (sizex, sizey) if success,
    or default size (defaultx, defaulty) otherwise.

    Dependencies: ctypes should be installed.
    """
    if ctypes is None:
        # no ctypes is found
        return (defaultx, defaulty)

    h = ctypes.windll.kernel32.GetStdHandle(-11)
    csbi = ctypes.create_string_buffer(22)
    res = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
    
    if res:
        (bufx, bufy, curx, cury, wattr,
         left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh",
                                                               csbi.raw)
        sizex = right - left + 1
        sizey = bottom - top + 1
        return (sizex, sizey)
    else:
        return (defaultx, defaulty)
