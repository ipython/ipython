""" Utilities for processing ANSI escape codes and special ASCII characters.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports
from collections import namedtuple
import re

# System library imports
from IPython.external.qt import QtCore, QtGui

#-----------------------------------------------------------------------------
# Constants and datatypes
#-----------------------------------------------------------------------------

# An action for erase requests (ED and EL commands).
EraseAction = namedtuple('EraseAction', ['action', 'area', 'erase_to'])

# An action for cursor move requests (CUU, CUD, CUF, CUB, CNL, CPL, CHA, CUP,
# and HVP commands).
# FIXME: Not implemented in AnsiCodeProcessor.
MoveAction = namedtuple('MoveAction', ['action', 'dir', 'unit', 'count'])

# An action for scroll requests (SU and ST) and form feeds.
ScrollAction = namedtuple('ScrollAction', ['action', 'dir', 'unit', 'count'])

# An action for the carriage return character
CarriageReturnAction = namedtuple('CarriageReturnAction', ['action'])

# An action for the \n character
NewLineAction = namedtuple('NewLineAction', ['action'])

# An action for the beep character
BeepAction = namedtuple('BeepAction', ['action'])

# An action for backspace
BackSpaceAction = namedtuple('BackSpaceAction', ['action'])

# Regular expressions.
CSI_COMMANDS = 'ABCDEFGHJKSTfmnsu'
CSI_SUBPATTERN = '\[(.*?)([%s])' % CSI_COMMANDS
OSC_SUBPATTERN = '\](.*?)[\x07\x1b]'
ANSI_PATTERN = ('\x01?\x1b(%s|%s)\x02?' % \
                (CSI_SUBPATTERN, OSC_SUBPATTERN))
ANSI_OR_SPECIAL_PATTERN = re.compile('(\a|\b|\r(?!\n)|\r?\n)|(?:%s)' % ANSI_PATTERN)
SPECIAL_PATTERN = re.compile('([\f])')

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class AnsiCodeProcessor(object):
    """ Translates special ASCII characters and ANSI escape codes into readable
        attributes. It also supports a few non-standard, xterm-specific codes.
    """

    # Whether to increase intensity or set boldness for SGR code 1.
    # (Different terminals handle this in different ways.)
    bold_text_enabled = False

    # We provide an empty default color map because subclasses will likely want
    # to use a custom color format.
    default_color_map = {}

    #---------------------------------------------------------------------------
    # AnsiCodeProcessor interface
    #---------------------------------------------------------------------------

    def __init__(self):
        self.actions = []
        self.color_map = self.default_color_map.copy()
        self.reset_sgr()

    def reset_sgr(self):
        """ Reset graphics attributs to their default values.
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
        self.actions = []
        start = 0

        # strings ending with \r are assumed to be ending in \r\n since
        # \n is appended to output strings automatically.  Accounting
        # for that, here.
        last_char = '\n' if len(string) > 0 and string[-1] == '\n' else None
        string = string[:-1] if last_char is not None else string

        for match in ANSI_OR_SPECIAL_PATTERN.finditer(string):
            raw = string[start:match.start()]
            substring = SPECIAL_PATTERN.sub(self._replace_special, raw)
            if substring or self.actions:
                yield substring
                self.actions = []
            start = match.end()

            groups = filter(lambda x: x is not None, match.groups())
            g0 = groups[0]
            if g0 == '\a':
                self.actions.append(BeepAction('beep'))
                yield None
                self.actions = []
            elif g0 == '\r':
                self.actions.append(CarriageReturnAction('carriage-return'))
                yield None
                self.actions = []
            elif g0 == '\b':
                self.actions.append(BackSpaceAction('backspace'))
                yield None
                self.actions = []
            elif g0 == '\n' or g0 == '\r\n':
                self.actions.append(NewLineAction('newline'))
                yield g0
                self.actions = []
            else:
                params = [ param for param in groups[1].split(';') if param ]
                if g0.startswith('['):
                    # Case 1: CSI code.
                    try:
                        params = map(int, params)
                    except ValueError:
                        # Silently discard badly formed codes.
                        pass
                    else:
                        self.set_csi_code(groups[2], params)

                elif g0.startswith(']'):
                    # Case 2: OSC code.
                    self.set_osc_code(params)

        raw = string[start:]
        substring = SPECIAL_PATTERN.sub(self._replace_special, raw)
        if substring or self.actions:
            yield substring

        if last_char is not None:
            self.actions.append(NewLineAction('newline'))
            yield last_char

    def set_csi_code(self, command, params=[]):
        """ Set attributes based on CSI (Control Sequence Introducer) code.

        Parameters
        ----------
        command : str
            The code identifier, i.e. the final character in the sequence.

        params : sequence of integers, optional
            The parameter codes for the command.
        """
        if command == 'm':   # SGR - Select Graphic Rendition
            if params:
                self.set_sgr_code(params)
            else:
                self.set_sgr_code([0])

        elif (command == 'J' or # ED - Erase Data
              command == 'K'):  # EL - Erase in Line
            code = params[0] if params else 0
            if 0 <= code <= 2:
                area = 'screen' if command == 'J' else 'line'
                if code == 0:
                    erase_to = 'end'
                elif code == 1:
                    erase_to = 'start'
                elif code == 2:
                    erase_to = 'all'
                self.actions.append(EraseAction('erase', area, erase_to))

        elif (command == 'S' or # SU - Scroll Up
              command == 'T'):  # SD - Scroll Down
            dir = 'up' if command == 'S' else 'down'
            count = params[0] if params else 1
            self.actions.append(ScrollAction('scroll', dir, 'line', count))

    def set_osc_code(self, params):
        """ Set attributes based on OSC (Operating System Command) parameters.

        Parameters
        ----------
        params : sequence of str
            The parameters for the command.
        """
        try:
            command = int(params.pop(0))
        except (IndexError, ValueError):
            return

        if command == 4:
            # xterm-specific: set color number to color spec.
            try:
                color = int(params.pop(0))
                spec = params.pop(0)
                self.color_map[color] = self._parse_xterm_color_spec(spec)
            except (IndexError, ValueError):
                pass

    def set_sgr_code(self, params):
        """ Set attributes based on SGR (Select Graphic Rendition) codes.

        Parameters
        ----------
        params : sequence of ints
            A list of SGR codes for one or more SGR commands. Usually this
            sequence will have one element per command, although certain
            xterm-specific commands requires multiple elements.
        """
        # Always consume the first parameter.
        if not params:
            return
        code = params.pop(0)

        if code == 0:
            self.reset_sgr()
        elif code == 1:
            if self.bold_text_enabled:
                self.bold = True
            else:
                self.intensity = 1
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
        elif code == 38 and params and params.pop(0) == 5:
            # xterm-specific: 256 color support.
            if params:
                self.foreground_color = params.pop(0)
        elif code == 39:
            self.foreground_color = None
        elif code >= 40 and code <= 47:
            self.background_color = code - 40
        elif code == 48 and params and params.pop(0) == 5:
            # xterm-specific: 256 color support.
            if params:
                self.background_color = params.pop(0)
        elif code == 49:
            self.background_color = None

        # Recurse with unconsumed parameters.
        self.set_sgr_code(params)

    #---------------------------------------------------------------------------
    # Protected interface
    #---------------------------------------------------------------------------

    def _parse_xterm_color_spec(self, spec):
        if spec.startswith('rgb:'):
            return tuple(map(lambda x: int(x, 16), spec[4:].split('/')))
        elif spec.startswith('rgbi:'):
            return tuple(map(lambda x: int(float(x) * 255),
                             spec[5:].split('/')))
        elif spec == '?':
            raise ValueError('Unsupported xterm color spec')
        return spec

    def _replace_special(self, match):
        special = match.group(1)
        if special == '\f':
            self.actions.append(ScrollAction('scroll', 'down', 'page', 1))
        return ''


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
        if isinstance(constructor, basestring):
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
            for i in xrange(8):
                self.default_color_map[i + 8] = self.default_color_map[i]

            # ...and replace white with black.
            self.default_color_map[7] = self.default_color_map[15] = 'black'

        # Update the current color map with the new defaults.
        self.color_map.update(self.default_color_map)
