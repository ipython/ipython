""" Utilities for processing ANSI escape codes and special ASCII characters in the qt client
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# System library imports
from IPython.external.qt import QtGui

# Local imports
from IPython.terminal.ansi_code_processor import AnsiCodeProcessor
from IPython.utils.py3compat import string_types

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class QtAnsiCodeProcessor(AnsiCodeProcessor):
    """ Translates ANSI escape codes into QTextCharFormats.
    """

    # A map from ANSI color codes to SVG color names or RGB(A) tuples.
    darkbg_color_map = {
        0  : 'black',       # black
        1  : 'darkred',     # red
        2  : 'darkgreen',   # green
        3  : 'brown',       # yellow
        4  : 'darkblue',    # blue
        5  : 'darkviolet',  # magenta
        6  : 'steelblue',   # cyan
        7  : 'grey',        # white
        8  : 'grey',        # black (bright)
        9  : 'red',         # red (bright)
        10 : 'lime',        # green (bright)
        11 : 'yellow',      # yellow (bright)
        12 : 'deepskyblue', # blue (bright)
        13 : 'magenta',     # magenta (bright)
        14 : 'cyan',        # cyan (bright)
        15 : 'white' }      # white (bright)

    # Set the default color map for super class.
    default_color_map = darkbg_color_map.copy()

    def get_color(self, color, intensity=0):
        """ Returns a QColor for a given color code, or None if one cannot be
            constructed.
        """
        if color is None:
            return None

        # Adjust for intensity, if possible.
        if color < 8 and intensity > 0:
            color += 8

        constructor = self.color_map.get(color, None)
        if isinstance(constructor, string_types):
            # If this is an X11 color name, we just hope there is a close SVG
            # color name. We could use QColor's static method
            # 'setAllowX11ColorNames()', but this is global and only available
            # on X11. It seems cleaner to aim for uniformity of behavior.
            return QtGui.QColor(constructor)

        elif isinstance(constructor, (tuple, list)):
            return QtGui.QColor(*constructor)

        return None

    def get_format(self):
        """ Returns a QTextCharFormat that encodes the current style attributes.
        """
        format = QtGui.QTextCharFormat()

        # Set foreground color
        qcolor = self.get_color(self.foreground_color, self.intensity)
        if qcolor is not None:
            format.setForeground(qcolor)

        # Set background color
        qcolor = self.get_color(self.background_color, self.intensity)
        if qcolor is not None:
            format.setBackground(qcolor)

        # Set font weight/style options
        if self.bold:
            format.setFontWeight(QtGui.QFont.Bold)
        else:
            format.setFontWeight(QtGui.QFont.Normal)
        format.setFontItalic(self.italic)
        format.setFontUnderline(self.underline)

        return format

    def set_background_color(self, color):
        """ Given a background color (a QColor), attempt to set a color map
            that will be aesthetically pleasing.
        """
        # Set a new default color map.
        self.default_color_map = self.darkbg_color_map.copy()

        if color.value() >= 127:
            # Colors appropriate for a terminal with a light background. For
            # now, only use non-bright colors...
            for i in range(8):
                self.default_color_map[i + 8] = self.default_color_map[i]

            # ...and replace white with black.
            self.default_color_map[7] = self.default_color_map[15] = 'black'

        # Update the current color map with the new defaults.
        self.color_map.update(self.default_color_map)
