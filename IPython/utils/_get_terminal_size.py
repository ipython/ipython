# vendored version of backports.get_terminal_size as nemesapece package are a
# mess and break, especially on ubuntu. This file is under MIT Licence.
# See https://pypi.python.org/pypi/backports.shutil_get_terminal_size
#
# commit: afc5714b1545a5a3aa44cfb5e078d39165bf76ab (Feb 20, 2016)
# from
# https://github.com/chrippa/backports.shutil_get_terminal_size
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Christopher Rosell
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
"""This is a backport of shutil.get_terminal_size from Python 3.3.

The original implementation is in C, but here we use the ctypes and
fcntl modules to create a pure Python version of os.get_terminal_size.
"""

import os
import struct
import sys

from collections import namedtuple

__all__ = ["get_terminal_size"]


terminal_size = namedtuple("terminal_size", "columns lines")

try:
    from ctypes import windll, create_string_buffer, WinError

    _handle_ids = {
        0: -10,
        1: -11,
        2: -12,
    }

    def _get_terminal_size(fd):
        handle = windll.kernel32.GetStdHandle(_handle_ids[fd])
        if handle == 0:
            raise OSError('handle cannot be retrieved')
        if handle == -1:
            raise WinError()
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(handle, csbi)
        if res:
            res = struct.unpack("hhhhHhhhhhh", csbi.raw)
            left, top, right, bottom = res[5:9]
            columns = right - left + 1
            lines = bottom - top + 1
            return terminal_size(columns, lines)
        else:
            raise WinError()

except ImportError:
    import fcntl
    import termios

    def _get_terminal_size(fd):
        try:
            res = fcntl.ioctl(fd, termios.TIOCGWINSZ, b"\x00" * 4)
        except IOError as e:
            raise OSError(e)
        lines, columns = struct.unpack("hh", res)

        return terminal_size(columns, lines)


def get_terminal_size(fallback=(80, 24)):
    """Get the size of the terminal window.

    For each of the two dimensions, the environment variable, COLUMNS
    and LINES respectively, is checked. If the variable is defined and
    the value is a positive integer, it is used.

    When COLUMNS or LINES is not defined, which is the common case,
    the terminal connected to sys.__stdout__ is queried
    by invoking os.get_terminal_size.

    If the terminal size cannot be successfully queried, either because
    the system doesn't support querying, or because we are not
    connected to a terminal, the value given in fallback parameter
    is used. Fallback defaults to (80, 24) which is the default
    size used by many terminal emulators.

    The value returned is a named tuple of type os.terminal_size.
    """
    # Try the environment first
    try:
        columns = int(os.environ["COLUMNS"])
    except (KeyError, ValueError):
        columns = 0

    try:
        lines = int(os.environ["LINES"])
    except (KeyError, ValueError):
        lines = 0

    # Only query if necessary
    if columns <= 0 or lines <= 0:
        try:
            size = _get_terminal_size(sys.__stdout__.fileno())
        except (NameError, OSError):
            size = terminal_size(*fallback)

        if columns <= 0:
            columns = size.columns
        if lines <= 0:
            lines = size.lines

    return terminal_size(columns, lines)

