# -*- coding: utf-8 -*-
"""
Color schemes for exception handling code in IPython.
"""

#*****************************************************************************
#       Copyright (C) 2005-2006 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython.utils.coloransi import ColorSchemeTable, TermColors, ColorScheme

def exception_colors():
    """Return a color table with fields for exception reporting.

    The table is an instance of ColorSchemeTable with schemes added for
    'Linux', 'LightBG' and 'NoColor' and fields for exception handling filled
    in.

    Examples:

    >>> ec = exception_colors()
    >>> ec.active_scheme_name
    ''
    >>> print(ec.active_colors)
    None

    Now we activate a color scheme:
    >>> ec.set_active_scheme('NoColor')
    >>> ec.active_scheme_name
    'NoColor'
    >>> sorted(ec.active_colors.keys())
    ['Normal', 'caret', 'em', 'excName', 'filename', 'filenameEm', 'line',
    'lineno', 'linenoEm', 'name', 'nameEm', 'normalEm', 'topline', 'vName',
    'val', 'valEm']
    """

    ex_colors = ColorSchemeTable()

    # Populate it with color schemes
    C = TermColors # shorthand and local lookup
    ex_colors.add_scheme(ColorScheme(
        'NoColor',
        # The color to be used for the top line
        topline = C.NoColor,

        # The colors to be used in the traceback
        filename = C.NoColor,
        lineno = C.NoColor,
        name = C.NoColor,
        vName = C.NoColor,
        val = C.NoColor,
        em = C.NoColor,

        # Emphasized colors for the last frame of the traceback
        normalEm = C.NoColor,
        filenameEm = C.NoColor,
        linenoEm = C.NoColor,
        nameEm = C.NoColor,
        valEm = C.NoColor,

        # Colors for printing the exception
        excName = C.NoColor,
        line = C.NoColor,
        caret = C.NoColor,
        Normal = C.NoColor
        ))

    # make some schemes as instances so we can copy them for modification easily
    ex_colors.add_scheme(ColorScheme(
        'Linux',
        # The color to be used for the top line
        topline = C.LightRed,

        # The colors to be used in the traceback
        filename = C.Green,
        lineno = C.Green,
        name = C.Purple,
        vName = C.Cyan,
        val = C.Green,
        em = C.LightCyan,

        # Emphasized colors for the last frame of the traceback
        normalEm = C.LightCyan,
        filenameEm = C.LightGreen,
        linenoEm = C.LightGreen,
        nameEm = C.LightPurple,
        valEm = C.LightBlue,

        # Colors for printing the exception
        excName = C.LightRed,
        line = C.Yellow,
        caret = C.White,
        Normal = C.Normal
        ))

    # For light backgrounds, swap dark/light colors
    ex_colors.add_scheme(ColorScheme(
        'LightBG',
        # The color to be used for the top line
        topline = C.Red,

        # The colors to be used in the traceback
        filename = C.LightGreen,
        lineno = C.LightGreen,
        name = C.LightPurple,
        vName = C.Cyan,
        val = C.LightGreen,
        em = C.Cyan,

        # Emphasized colors for the last frame of the traceback
        normalEm = C.Cyan,
        filenameEm = C.Green,
        linenoEm = C.Green,
        nameEm = C.Purple,
        valEm = C.Blue,

        # Colors for printing the exception
        excName = C.Red,
        #line = C.Brown,  # brown often is displayed as yellow
        line = C.Red,
        caret = C.Normal,
        Normal = C.Normal,
        ))

    return ex_colors


# For backwards compatibility, keep around a single global object.  Note that
# this should NOT be used, the factory function should be used instead, since
# these objects are stateful and it's very easy to get strange bugs if any code
# modifies the module-level object's state.
ExceptionColors = exception_colors()
