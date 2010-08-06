# Standard library imports
import re

# System library imports
from PyQt4 import QtCore, QtGui


class AnsiCodeProcessor(object):
    """ Translates ANSI escape codes into readable attributes.
    """

    # Protected class variables.
    _ansi_commands = 'ABCDEFGHJKSTfmnsu'
    _ansi_pattern = re.compile('\x01?\x1b\[(.*?)([%s])\x02?' % _ansi_commands)

    def __init__(self):
        self.reset()

    def reset(self):
        """ Reset attributs to their default values.
        """
        self.intensity = 0
        self.italic = False
        self.bold = False
        self.underline = False
        self.foreground_color = None
        self.background_color = None

    def split_string(self, string):
        """ Yields substrings for which the same escape code applies.
        """
        start = 0

        for match in self._ansi_pattern.finditer(string):
            substring = string[start:match.start()]
            if substring:
                yield substring
            start = match.end()

            params = map(int, match.group(1).split(';'))
            self.set_csi_code(match.group(2), params)

        substring = string[start:]
        if substring:
            yield substring

    def set_csi_code(self, command, params=[]):
        """ Set attributes based on CSI (Control Sequence Introducer) code.

        Parameters
        ----------
        command : str
            The code identifier, i.e. the final character in the sequence.
        
        params : sequence of integers, optional
            The parameter codes for the command.
        """
        if command == 'm': # SGR - Select Graphic Rendition
            for code in params:
                self.set_sgr_code(code)
        
    def set_sgr_code(self, code):
        """ Set attributes based on SGR (Select Graphic Rendition) code.
        """
        if code == 0:
            self.reset()
        elif code == 1:
            self.intensity = 1
            self.bold = True
        elif code == 2:
            self.intensity = 0
        elif code == 3:
            self.italic = True
        elif code == 4:
            self.underline = True
        elif code == 22:
            self.intensity = 0
            self.bold = False
        elif code == 23:
            self.italic = False
        elif code == 24:
            self.underline = False
        elif code >= 30 and code <= 37:
            self.foreground_color = code - 30
        elif code == 39:
            self.foreground_color = None
        elif code >= 40 and code <= 47:
            self.background_color = code - 40
        elif code == 49:
            self.background_color = None
        

class QtAnsiCodeProcessor(AnsiCodeProcessor):
    """ Translates ANSI escape codes into QTextCharFormats.
    """

    # A map from color codes to RGB colors.
    ansi_colors = ( # Normal, Bright/Light
                   ('#000000', '#7f7f7f'), # 0: black
                   ('#cd0000', '#ff0000'), # 1: red
                   ('#00cd00', '#00ff00'), # 2: green
                   ('#cdcd00', '#ffff00'), # 3: yellow
                   ('#0000ee', '#0000ff'), # 4: blue
                   ('#cd00cd', '#ff00ff'), # 5: magenta
                   ('#00cdcd', '#00ffff'), # 6: cyan
                   ('#e5e5e5', '#ffffff')) # 7: white
    
    def get_format(self):
        """ Returns a QTextCharFormat that encodes the current style attributes.
        """
        format = QtGui.QTextCharFormat()

        # Set foreground color
        if self.foreground_color is not None:
            color = self.ansi_colors[self.foreground_color][self.intensity]
            format.setForeground(QtGui.QColor(color))

        # Set background color
        if self.background_color is not None:
            color = self.ansi_colors[self.background_color][self.intensity]
            format.setBackground(QtGui.QColor(color))

        # Set font weight/style options
        if self.bold:
            format.setFontWeight(QtGui.QFont.Bold)
        else:
            format.setFontWeight(QtGui.QFont.Normal)
        format.setFontItalic(self.italic)
        format.setFontUnderline(self.underline)

        return format
