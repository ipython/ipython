"""
``astyle`` provides classes for adding style (foreground and background color;
bold; blink; etc.) to terminal and curses output.
"""


import sys, os

try:
    import curses
except ImportError:
    curses = None


COLOR_BLACK   = 0
COLOR_RED     = 1
COLOR_GREEN   = 2
COLOR_YELLOW  = 3
COLOR_BLUE    = 4
COLOR_MAGENTA = 5
COLOR_CYAN    = 6
COLOR_WHITE   = 7

A_BLINK     = 1<<0 # Blinking text
A_BOLD      = 1<<1 # Extra bright or bold text
A_DIM       = 1<<2 # Half bright text
A_REVERSE   = 1<<3 # Reverse-video text
A_STANDOUT  = 1<<4 # The best highlighting mode available
A_UNDERLINE = 1<<5 # Underlined text


class Style(object):
    """
    Store foreground color, background color and attribute (bold, underlined
    etc.).
    """
    __slots__ = ("fg", "bg", "attrs")

    COLORNAMES = {
        "black": COLOR_BLACK,
        "red": COLOR_RED,
        "green": COLOR_GREEN,
        "yellow": COLOR_YELLOW,
        "blue": COLOR_BLUE,
        "magenta": COLOR_MAGENTA,
        "cyan": COLOR_CYAN,
        "white": COLOR_WHITE,
    }
    ATTRNAMES = {
        "blink": A_BLINK,
        "bold": A_BOLD,
        "dim": A_DIM,
        "reverse": A_REVERSE,
        "standout": A_STANDOUT,
        "underline": A_UNDERLINE,
    }

    def __init__(self, fg, bg, attrs=0):
        """
        Create a ``Style`` object with ``fg`` as the foreground color,
        ``bg`` as the background color and ``attrs`` as the attributes.

        Examples:
        >>> Style(COLOR_RED, COLOR_BLACK)
        <Style fg=red bg=black attrs=0>

        >>> Style(COLOR_YELLOW, COLOR_BLUE, A_BOLD|A_UNDERLINE)
        <Style fg=yellow bg=blue attrs=bold|underline>
        """
        self.fg = fg
        self.bg = bg
        self.attrs = attrs

    def __call__(self, *args):
        text = Text()
        for arg in args:
            if isinstance(arg, Text):
                text.extend(arg)
            else:
                text.append((self, arg))
        return text

    def __eq__(self, other):
        return self.fg == other.fg and self.bg == other.bg and self.attrs == other.attrs

    def __neq__(self, other):
        return self.fg != other.fg or self.bg != other.bg or self.attrs != other.attrs

    def __repr__(self):
        color2name = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
        attrs2name = ("blink", "bold", "dim", "reverse", "standout", "underline")

        return "<%s fg=%s bg=%s attrs=%s>" % (
            self.__class__.__name__, color2name[self.fg], color2name[self.bg],
            "|".join([attrs2name[b] for b in xrange(6) if self.attrs&(1<<b)]) or 0)

    def fromstr(cls, value):
        """
        Create a ``Style`` object from a string. The format looks like this:
        ``"red:black:bold|blink"``.
        """
        # defaults
        fg = COLOR_WHITE
        bg = COLOR_BLACK
        attrs = 0

        parts = value.split(":")
        if len(parts) > 0:
            fg = cls.COLORNAMES[parts[0].lower()]
            if len(parts) > 1:
                bg = cls.COLORNAMES[parts[1].lower()]
                if len(parts) > 2:
                    for strattr in parts[2].split("|"):
                        attrs |= cls.ATTRNAMES[strattr.lower()]
        return cls(fg, bg, attrs)
    fromstr = classmethod(fromstr)

    def fromenv(cls, name, default):
        """
        Create a ``Style`` from an environment variable named ``name``
        (using ``default`` if the environment variable doesn't exist).
        """
        return cls.fromstr(os.environ.get(name, default))
    fromenv = classmethod(fromenv)


def switchstyle(s1, s2):
    """
    Return the ANSI escape sequence needed to switch from style ``s1`` to
    style ``s2``.
    """
    attrmask = (A_BLINK|A_BOLD|A_UNDERLINE|A_REVERSE)
    a1 = s1.attrs & attrmask
    a2 = s2.attrs & attrmask

    args = []
    if s1 != s2:
        # do we have to get rid of the bold/underline/blink bit?
        # (can only be done by a reset)
        # use reset when our target color is the default color
        # (this is shorter than 37;40)
        if (a1 & ~a2 or s2==style_default):
            args.append("0")
            s1 = style_default
            a1 = 0

        # now we know that old and new color have the same boldness,
        # or the new color is bold and the old isn't,
        # i.e. we only might have to switch bold on, not off
        if not (a1 & A_BOLD) and (a2 & A_BOLD):
            args.append("1")

        # Fix underline
        if not (a1 & A_UNDERLINE) and (a2 & A_UNDERLINE):
            args.append("4")

        # Fix blink
        if not (a1 & A_BLINK) and (a2 & A_BLINK):
            args.append("5")

        # Fix reverse
        if not (a1 & A_REVERSE) and (a2 & A_REVERSE):
            args.append("7")

        # Fix foreground color
        if s1.fg != s2.fg:
            args.append("3%d" % s2.fg)

        # Finally fix the background color
        if s1.bg != s2.bg:
            args.append("4%d" % s2.bg)

        if args:
            return "\033[%sm" % ";".join(args)
    return ""


class Text(list):
    """
    A colored string. A ``Text`` object is a sequence, the sequence
    items will be ``(style, string)`` tuples.
    """

    def __init__(self, *args):
        list.__init__(self)
        self.append(*args)

    def __repr__(self):
        return "%s.%s(%s)" % (
            self.__class__.__module__, self.__class__.__name__,
            list.__repr__(self)[1:-1])

    def append(self, *args):
        for arg in args:
            if isinstance(arg, Text):
                self.extend(arg)
            elif isinstance(arg, tuple): # must be (style, string)
                list.append(self, arg)
            elif isinstance(arg, unicode):
                list.append(self, (style_default, arg))
            else:
                list.append(self, (style_default, str(arg)))

    def insert(self, index, *args):
        self[index:index] = Text(*args)

    def __add__(self, other):
        new = Text()
        new.append(self)
        new.append(other)
        return new

    def __iadd__(self, other):
        self.append(other)
        return self

    def format(self, styled=True):
        """
        This generator yields the strings that will make up the final
        colorized string.
        """
        if styled:
            oldstyle = style_default
            for (style, string) in self:
                if not isinstance(style, (int, long)):
                    switch = switchstyle(oldstyle, style)
                    if switch:
                        yield switch
                    if string:
                        yield string
                    oldstyle = style
            switch = switchstyle(oldstyle, style_default)
            if switch:
                yield switch
        else:
            for (style, string) in self:
                if not isinstance(style, (int, long)):
                    yield string

    def string(self, styled=True):
        """
        Return the resulting string (with escape sequences, if ``styled``
        is true).
        """
        return "".join(self.format(styled))

    def __str__(self):
        """
        Return ``self`` as a string (without ANSI escape sequences).
        """
        return self.string(False)

    def write(self, stream, styled=True):
        """
        Write ``self`` to the output stream ``stream`` (with escape sequences,
        if ``styled`` is true).
        """
        for part in self.format(styled):
            stream.write(part)


try:
    import ipipe
except ImportError:
    pass
else:
    def xrepr_astyle_text(self, mode="default"):
        yield (-1, True)
        for info in self:
            yield info
    ipipe.xrepr.when_type(Text)(xrepr_astyle_text)


def streamstyle(stream, styled=None):
    """
    If ``styled`` is ``None``, return whether ``stream`` refers to a terminal.
    If this can't be determined (either because ``stream`` doesn't refer to a
    real OS file, or because you're on Windows) return ``False``. If ``styled``
    is not ``None`` ``styled`` will be returned unchanged.
    """
    if styled is None:
        try:
            styled = os.isatty(stream.fileno())
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            styled = False
    return styled


def write(stream, styled, *texts):
    """
    Write ``texts`` to ``stream``.
    """
    text = Text(*texts)
    text.write(stream, streamstyle(stream, styled))


def writeln(stream, styled, *texts):
    """
    Write ``texts`` to ``stream`` and finish with a line feed.
    """
    write(stream, styled, *texts)
    stream.write("\n")


class Stream(object):
    """
    Stream wrapper that adds color output.
    """
    def __init__(self, stream, styled=None):
        self.stream = stream
        self.styled = streamstyle(stream, styled)

    def write(self, *texts):
        write(self.stream, self.styled, *texts)

    def writeln(self, *texts):
        writeln(self.stream, self.styled, *texts)

    def __getattr__(self, name):
        return getattr(self.stream, name)


class stdout(object):
    """
    Stream wrapper for ``sys.stdout`` that adds color output.
    """
    def write(self, *texts):
        write(sys.stdout, None, *texts)

    def writeln(self, *texts):
        writeln(sys.stdout, None, *texts)

    def __getattr__(self, name):
        return getattr(sys.stdout, name)
stdout = stdout()


class stderr(object):
    """
    Stream wrapper for ``sys.stderr`` that adds color output.
    """
    def write(self, *texts):
        write(sys.stderr, None, *texts)

    def writeln(self, *texts):
        writeln(sys.stderr, None, *texts)

    def __getattr__(self, name):
        return getattr(sys.stdout, name)
stderr = stderr()


if curses is not None:
    # This is probably just range(8)
    COLOR2CURSES = [
        COLOR_BLACK,
        COLOR_RED,
        COLOR_GREEN,
        COLOR_YELLOW,
        COLOR_BLUE,
        COLOR_MAGENTA,
        COLOR_CYAN,
        COLOR_WHITE,
    ]

    A2CURSES = {
        A_BLINK: curses.A_BLINK,
        A_BOLD: curses.A_BOLD,
        A_DIM: curses.A_DIM,
        A_REVERSE: curses.A_REVERSE,
        A_STANDOUT: curses.A_STANDOUT,
        A_UNDERLINE: curses.A_UNDERLINE,
    }


# default style
style_default = Style.fromstr("white:black")

# Styles for datatypes
style_type_none = Style.fromstr("magenta:black")
style_type_bool = Style.fromstr("magenta:black")
style_type_number = Style.fromstr("yellow:black")
style_type_datetime = Style.fromstr("magenta:black")
style_type_type = Style.fromstr("cyan:black")

# Style for URLs and file/directory names
style_url = Style.fromstr("green:black")
style_dir = Style.fromstr("cyan:black")
style_file = Style.fromstr("green:black")

# Style for ellipsis (when an output has been shortened
style_ellisis = Style.fromstr("red:black")

# Style for displaying exceptions
style_error = Style.fromstr("red:black")

# Style for displaying non-existing attributes
style_nodata = Style.fromstr("red:black")
