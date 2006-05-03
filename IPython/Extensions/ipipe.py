# -*- coding: iso-8859-1 -*-

"""
``ipipe`` provides classes to be used in an interactive Python session. Doing a
``from ipipe import *`` is the preferred way to do this. The name of all
objects imported this way starts with ``i`` to minimize collisions.

``ipipe`` supports "pipeline expressions", which is something resembling Unix
pipes. An example is:

    >>> ienv | isort("key.lower()")

This gives a listing of all environment variables sorted by name.


There are three types of objects in a pipeline expression:

* ``Table``s: These objects produce items. Examples are ``ls`` (listing the
  current directory, ``ienv`` (listing environment variables), ``ipwd`` (listing
  user account) and ``igrp`` (listing user groups). A ``Table`` must be the
  first object in a pipe expression.

* ``Pipe``s: These objects sit in the middle of a pipe expression. They
  transform the input in some way (e.g. filtering or sorting it). Examples are:
  ``ifilter`` (which filters the input pipe), ``isort`` (which sorts the input
  pipe) and ``ieval`` (which evaluates a function or expression for each object
  in the input pipe).

* ``Display``s: These objects can be put as the last object in a pipeline
  expression. There are responsible for displaying the result of the pipeline
  expression. If a pipeline expression doesn't end in a display object a default
  display objects will be used. One example is ``browse`` which is a ``curses``
  based browser.


Adding support for pipeline expressions to your own objects can be done through
three extensions points (all of them optional):

* An object that will be displayed as a row by a ``Display`` object should
  implement the method ``__xattrs__(self, mode)``. This method must return a
  sequence of attribute names. This sequence may also contain integers, which
  will be treated as sequence indizes. Also supported is ``None``, which uses
  the object itself and callables which will be called with the object as the
  an argument. If ``__xattrs__()`` isn't implemented ``(None,)`` will be used as
  the attribute sequence (i.e. the object itself (it's ``repr()`` format) will
  be being displayed. The global function ``xattrs()`` implements this
  functionality.

* When an object ``foo`` is displayed in the header, footer or table cell of the
  browser ``foo.__xrepr__(mode)`` is called. Mode can be ``"header"`` or
  ``"footer"`` for the header or footer line and ``"cell"`` for a table cell.
  ``__xrepr__()```must return an iterable (e.g. by being a generator) which
  produces the following items: The first item should be a tuple containing
  the alignment (-1 left aligned, 0 centered and 1 right aligned) and whether
  the complete output must be displayed or if the browser is allowed to stop
  output after enough text has been produced (e.g. a syntax highlighted text
  line would use ``True``, but for a large data structure (i.e. a nested list,
  tuple or dictionary) ``False`` would be used). The other output ``__xrepr__()``
  may produce is tuples of ``Style```objects and text (which contain the text
  representation of the object). If ``__xrepr__()`` recursively outputs a data
  structure the function ``xrepr(object, mode)`` can be used and ``"default"``
  must be passed as the mode in these calls. This in turn calls the
  ``__xrepr__()`` method on ``object`` (or uses ``repr(object)`` as the string
  representation if ``__xrepr__()`` doesn't exist.

* Objects that can be iterated by ``Pipe``s must implement the method
``__xiter__(self, mode)``. ``mode`` can take the following values:

  - ``"default"``: This is the default value and ist always used by pipeline
    expressions. Other values are only used in the browser.
  - ``None``: This value is passed by the browser. The object must return an
    iterable of ``XMode`` objects describing all modes supported by the object.
    (This should never include ``"default"`` or ``None``).
  - Any other value that the object supports.

  The global function ``xiter()`` can be called to get such an iterator. If
  the method ``_xiter__`` isn't implemented, ``xiter()`` falls back to
  ``__iter__``. In addition to that, dictionaries and modules receive special
  treatment (returning an iterator over ``(key, value)`` pairs). This makes it
  possible to use dictionaries and modules in pipeline expressions, for example:

      >>> import sys
      >>> sys | ifilter("isinstance(value, int)") | idump
      key        |value
      api_version|      1012
      dllhandle  | 503316480
      hexversion |  33817328
      maxint     |2147483647
      maxunicode |     65535
      >>> sys.modules | ifilter("_.value is not None") | isort("_.key.lower()")
      ...

  Note: The expression strings passed to ``ifilter()`` and ``isort()`` can
  refer to the object to be filtered or sorted via the variable ``_`` and to any
  of the attributes of the object, i.e.:

      >>> sys.modules | ifilter("_.value is not None") | isort("_.key.lower()")

  does the same as

      >>> sys.modules | ifilter("value is not None") | isort("key.lower()")

  In addition to expression strings, it's possible to pass callables (taking
  the object as an argument) to ``ifilter()``, ``isort()`` and ``ieval()``:

      >>> sys | ifilter(lambda _:isinstance(_.value, int)) \
      ...     | ieval(lambda _: (_.key, hex(_.value))) | idump
      0          |1
      api_version|0x3f4
      dllhandle  |0x1e000000
      hexversion |0x20402f0
      maxint     |0x7fffffff
      maxunicode |0xffff
"""

import sys, os, os.path, stat, glob, new, csv, datetime, types
import textwrap, itertools, mimetypes

try: # Python 2.3 compatibility
    import collections
except ImportError:
    deque = list
else:
    deque = collections.deque

try: # Python 2.3 compatibility
    set
except NameError:
    import sets
    set = sets.Set

try: # Python 2.3 compatibility
    sorted
except NameError:
    def sorted(iterator, key=None, reverse=False):
        items = list(iterator)
        if key is not None:
            items.sort(lambda i1, i2: cmp(key(i1), key(i2)))
        else:
            items.sort()
        if reverse:
            items.reverse()
        return items

try:
    import pwd
except ImportError:
    pwd = None

try:
    import grp
except ImportError:
    grp = None

try:
    import curses
except ImportError:
    curses = None

import path
try:
    from IPython import genutils
except ImportError:
    pass


__all__ = [
    "ifile", "ils", "iglob", "iwalk", "ipwdentry", "ipwd", "igrpentry", "igrp",
    "icsv", "ix", "ichain", "isort", "ifilter", "ieval", "ienum", "ienv",
    "idump", "iless"
]


os.stat_float_times(True) # enable microseconds


class _AttrNamespace(object):
    """
    Internal helper class that is used for providing a namespace for evaluating
    expressions containg attribute names of an object.
    """
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getitem__(self, name):
        if name == "_":
            return self.wrapped
        try:
            return getattr(self.wrapped, name)
        except AttributeError:
            raise KeyError(name)

# Python 2.3 compatibility
# use eval workaround to find out which names are used in the
# eval string and put them into the locals. This works for most
# normal uses case, bizarre ones like accessing the locals()
# will fail
try:
    eval("_", None, _AttrNamespace(None))
except TypeError:
    real_eval = eval
    def eval(codestring, _globals, _locals):
        """
        eval(source[, globals[, locals]]) -> value

        Evaluate the source in the context of globals and locals.
        The source may be a string representing a Python expression
        or a code object as returned by compile().
        The globals must be a dictionary and locals can be any mappping.

        This function is a workaround for the shortcomings of
        Python 2.3's eval.
        """

        code = compile(codestring, "_eval", "eval")
        newlocals = {}
        for name in code.co_names:
            try:
                newlocals[name] = _locals[name]
            except KeyError:
                pass
        return real_eval(code, _globals, newlocals)


_default = object()

def item(iterator, index, default=_default):
    """
    Return the ``index``th item from the iterator ``iterator``.
    ``index`` must be an integer (negative integers are relative to the
    end (i.e. the last item produced by the iterator)).

    If ``default`` is given, this will be the default value when
    the iterator doesn't contain an item at this position. Otherwise an
    ``IndexError`` will be raised.

    Note that using this function will partially or totally exhaust the
    iterator.
    """
    i = index
    if i>=0:
        for item in iterator:
            if not i:
                return item
            i -= 1
    else:
        i = -index
        cache = deque()
        for item in iterator:
            cache.append(item)
            if len(cache)>i:
                cache.popleft()
        if len(cache)==i:
            return cache.popleft()
    if default is _default:
        raise IndexError(index)
    else:
        return default


class Table(object):
    """
    A ``Table`` is an object that produces items (just like a normal Python
    iterator/generator does) and can be used as the first object in a pipeline
    expression. The displayhook will open the default browser for such an object
    (instead of simply printing the ``repr()`` result).
    """

    # We want to support ``foo`` and ``foo()`` in pipeline expression:
    # So we implement the required operators (``|`` and ``+``) in the metaclass,
    # instantiate the class and forward the operator to the instance
    class __metaclass__(type):
        def __iter__(self):
            return iter(self())

        def __or__(self, other):
            return self() | other

        def __add__(self, other):
            return self() + other

        def __radd__(self, other):
            return other + self()

        def __getitem__(self, index):
            return self()[index]

    def __getitem__(self, index):
        return item(self, index)

    def __contains__(self, item):
        for haveitem in self:
            if item == haveitem:
                return True
        return False

    def __or__(self, other):
        # autoinstantiate right hand side
        if isinstance(other, type) and issubclass(other, (Table, Display)):
            other = other()
        # treat simple strings and functions as ``ieval`` instances
        elif not isinstance(other, Display) and not isinstance(other, Table):
            other = ieval(other)
        # forward operations to the right hand side
        return other.__ror__(self)

    def __add__(self, other):
        # autoinstantiate right hand side
        if isinstance(other, type) and issubclass(other, Table):
            other = other()
        return ichain(self, other)

    def __radd__(self, other):
        # autoinstantiate left hand side
        if isinstance(other, type) and issubclass(other, Table):
            other = other()
        return ichain(other, self)

    def __iter__(self):
        return xiter(self, "default")


class Pipe(Table):
    """
    A ``Pipe`` is an object that can be used in a pipeline expression. It
    processes the objects it gets from its input ``Table``/``Pipe``. Note that
    a ``Pipe`` object can't be used as the first object in a pipeline
    expression, as it doesn't produces items itself.
    """
    class __metaclass__(Table.__metaclass__):
        def __ror__(self, input):
            return input | self()

    def __ror__(self, input):
        # autoinstantiate left hand side
        if isinstance(input, type) and issubclass(input, Table):
            input = input()
        self.input = input
        return self


def _getattr(obj, name, default=_default):
    """
    Internal helper for getting an attribute of an item. If ``name`` is ``None``
    return the object itself. If ``name`` is an integer, use ``__getitem__``
    instead. If the attribute or item does not exist, return ``default``.
    """
    if name is None:
        return obj
    elif isinstance(name, basestring):
        if name.endswith("()"):
            return getattr(obj, name[:-2], default)()
        else:
            return getattr(obj, name, default)
    elif callable(name):
        try:
            return name(obj)
        except AttributeError:
            return default
    else:
        try:
            return obj[name]
        except IndexError:
            return default


def _attrname(name):
    """
    Internal helper that gives a proper name for the attribute ``name``
    (which might be ``None`` or an ``int``).
    """
    if name is None:
        return "_"
    elif isinstance(name, basestring):
        return name
    elif callable(name):
        return getattr(name, "__xname__", name.__name__)
    else:
        return str(name)


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
            >>> Style(COLOR_YELLOW, COLOR_BLUE, A_BOLD|A_UNDERLINE)
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
        Return the resulting string with ANSI escape sequences.
        """
        return self.string(False)

    def write(self, stream, styled=True):
        for part in self.format(styled):
            stream.write(part)

    def __xrepr__(self, mode="default"):
        yield (-1, True)
        for info in self:
            yield info


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
style_default = Style(COLOR_WHITE, COLOR_BLACK)

# Styles for datatypes
style_type_none = Style(COLOR_MAGENTA, COLOR_BLACK)
style_type_bool = Style(COLOR_MAGENTA, COLOR_BLACK)
style_type_number = Style(COLOR_YELLOW, COLOR_BLACK)
style_type_datetime = Style(COLOR_MAGENTA, COLOR_BLACK)

# Style for URLs and file/directory names
style_url = Style(COLOR_GREEN, COLOR_BLACK)
style_dir = Style(COLOR_CYAN, COLOR_BLACK)
style_file = Style(COLOR_GREEN, COLOR_BLACK)

# Style for ellipsis (when an output has been shortened
style_ellisis = Style(COLOR_RED, COLOR_BLACK)

# Style for displaying exceptions
style_error = Style(COLOR_RED, COLOR_BLACK)

# Style for displaying non-existing attributes
style_nodata = Style(COLOR_RED, COLOR_BLACK)


def xrepr(item, mode):
    try:
        func = item.__xrepr__
    except AttributeError:
        pass
    else:
        try:
            for x in func(mode):
                yield x
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            yield (-1, True)
            yield (style_default, repr(item))
        return
    if item is None:
        yield (-1, True)
        yield (style_type_none, repr(item))
    elif isinstance(item, bool):
        yield (-1, True)
        yield (style_type_bool, repr(item))
    elif isinstance(item, str):
        yield (-1, True)
        if mode == "cell":
            yield (style_default, repr(item.expandtabs(tab))[1:-1])
        else:
            yield (style_default, repr(item))
    elif isinstance(item, unicode):
        yield (-1, True)
        if mode == "cell":
            yield (style_default, repr(item.expandtabs(tab))[2:-1])
        else:
            yield (style_default, repr(item))
    elif isinstance(item, (int, long, float)):
        yield (1, True)
        yield (style_type_number, repr(item))
    elif isinstance(item, complex):
        yield (-1, True)
        yield (style_type_number, repr(item))
    elif isinstance(item, datetime.datetime):
        yield (-1, True)
        if mode == "cell":
            # Don't use strftime() here, as this requires year >= 1900
            yield (style_type_datetime,
                   "%04d-%02d-%02d %02d:%02d:%02d.%06d" % \
                        (item.year, item.month, item.day,
                         item.hour, item.minute, item.second,
                         item.microsecond),
                    )
        else:
            yield (style_type_datetime, repr(item))
    elif isinstance(item, datetime.date):
        yield (-1, True)
        if mode == "cell":
            yield (style_type_datetime,
                   "%04d-%02d-%02d" % (item.year, item.month, item.day))
        else:
            yield (style_type_datetime, repr(item))
    elif isinstance(item, datetime.time):
        yield (-1, True)
        if mode == "cell":
            yield (style_type_datetime,
                    "%02d:%02d:%02d.%06d" % \
                        (item.hour, item.minute, item.second, item.microsecond))
        else:
            yield (style_type_datetime, repr(item))
    elif isinstance(item, datetime.timedelta):
        yield (-1, True)
        yield (style_type_datetime, repr(item))
    elif isinstance(item, Exception):
        yield (-1, True)
        if item.__class__.__module__ == "exceptions":
            classname = item.__class__.__name__
        else:
            classname = "%s.%s: %s" % \
                (item.__class__.__module__, item.__class__.__name__)
        if mode == "header" or mode == "footer":
            yield (style_error, "%s: %s" % (classname, item))
        else:
            yield (style_error, classname)
    elif isinstance(item, (list, tuple)):
        yield (-1, False)
        if mode == "header" or mode == "footer":
            if item.__class__.__module__ == "__builtin__":
                classname = item.__class__.__name__
            else:
                classname = "%s.%s" % \
                    (item.__class__.__module__,item.__class__.__name__)
            yield (style_default,
                   "<%s object with %d items at 0x%x>" % \
                       (classname, len(item), id(item)))
        else:
            if isinstance(item, list):
                yield (style_default, "[")
                end = "]"
            else:
                yield (style_default, "(")
                end = ")"
            for (i, subitem) in enumerate(item):
                if i:
                    yield (style_default, ", ")
                for part in xrepr(subitem, "default"):
                    yield part
            yield (style_default, end)
    elif isinstance(item, (dict, types.DictProxyType)):
        yield (-1, False)
        if mode == "header" or mode == "footer":
            if item.__class__.__module__ == "__builtin__":
                classname = item.__class__.__name__
            else:
                classname = "%s.%s" % \
                    (item.__class__.__module__,item.__class__.__name__)
            yield (style_default,
                   "<%s object with %d items at 0x%x>" % \
                    (classname, len(item), id(item)))
        else:
            if isinstance(item, dict):
                yield (style_default, "{")
                end = "}"
            else:
                yield (style_default, "dictproxy((")
                end = "})"
            for (i, (key, value)) in enumerate(item.iteritems()):
                if i:
                    yield (style_default, ", ")
                for part in xrepr(key, "default"):
                    yield part
                yield (style_default, ": ")
                for part in xrepr(value, "default"):
                    yield part
            yield (style_default, end)
    else:
        yield (-1, True)
        yield (style_default, repr(item))


def xattrs(item, mode):
    try:
        func = item.__xattrs__
    except AttributeError:
        if mode == "detail":
            return dir(item)
        else:
            return (None,)
    else:
        try:
            return func(mode)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            return (None,)


def xiter(item, mode):
    if mode == "detail":
        def items():
            for name in xattrs(item, mode):
                yield XAttr(item, name)
        return items()
    try:
        func = item.__xiter__
    except AttributeError:
        if isinstance(item, (dict, types.DictProxyType)):
            def items(item):
                fields = ("key", "value")
                for (key, value) in item.iteritems():
                    yield Fields(fields, key=key, value=value)
            return items(item)
        elif isinstance(item, new.module):
            def items(item):
                fields = ("key", "value")
                for key in sorted(item.__dict__):
                    yield Fields(fields, key=key, value=getattr(item, key))
            return items(item)
        elif isinstance(item, basestring):
            if not len(item):
                raise ValueError("can't enter empty string")
            lines = item.splitlines()
            if len(lines) <= 1:
                raise ValueError("can't enter one line string")
            return iter(lines)
        return iter(item)
    else:
        return iter(func(mode)) # iter() just to be safe


class ichain(Pipe):
    """
    Chains multiple ``Table``s into one.
    """

    def __init__(self, *iters):
        self.iters = iters

    def __xiter__(self, mode):
        return itertools.chain(*self.iters)

    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "header" or mode == "footer":
            for (i, item) in enumerate(self.iters):
                if i:
                    yield (style_default, "+")
                if isinstance(item, Pipe):
                    yield (style_default, "(")
                for part in xrepr(item, mode):
                    yield part
                if isinstance(item, Pipe):
                    yield (style_default, ")")
        else:
            yield (style_default, repr(self))

    def __repr__(self):
        args = ", ".join([repr(it) for it in self.iters])
        return "%s.%s(%s)" % \
            (self.__class__.__module__, self.__class__.__name__, args)


class ifile(path.path):
    """
    file (or directory) object.
    """

    def __add_(self, other):
        return ifile(path._base(self) + other)

    def __radd_(self, other):
        return ifile(other + path._base(self))

    def __div_(self, other):
        return ifile(path.__div__(self, other))

    def getcwd():
        """ Return the current working directory as a path object. """
        return ifile(path.path.getcwd())
    getcwd = staticmethod(getcwd)

    def abspath(self):
        return ifile(path.path.abspath(self))

    def normcase(self):
        return ifile(path.path.normcase(self))

    def normpath(self):
        return ifile(path.path.normpath(self))

    def realpath(self):
        return ifile(path.path.realpath(self))

    def expanduser(self):
        return ifile(path.path.expanduser(self))

    def expandvars(self):
        return ifile(path.path.expandvars(self))

    def dirname(self):
        return ifile(path.path.dirname(self))

    parent = property(dirname, None, None, path.path.parent.__doc__)

    def splitpath(self):
        (parent, child) = path.path.splitpath(self)
        return (ifile(parent), child)

    def splitdrive(self):
        (drive, rel) = path.path.splitdrive(self)
        return (ifile(drive), rel)

    def splitext(self):
        (filename, ext) = path.path.splitext(self)
        return (ifile(filename), ext)

    if hasattr(path.path, "splitunc"):
        def splitunc(self):
            (unc, rest) = path.path.splitunc(self)
            return (ifile(unc), rest)

        def _get_uncshare(self):
            unc, r = os.path.splitunc(self)
            return ifile(unc)

        uncshare = property(
            _get_uncshare, None, None,
            """ The UNC mount point for this path.
            This is empty for paths on local drives. """)

    def joinpath(self, *args):
        return ifile(path.path.joinpath(self, *args))

    def splitall(self):
        return map(ifile, path.path.splitall(self))

    def relpath(self):
        return ifile(path.path.relpath(self))

    def relpathto(self, dest):
        return ifile(path.path.relpathto(self, dest))

    def listdir(self, pattern=None):
        return [ifile(child) for child in path.path.listdir(self, pattern)]

    def dirs(self, pattern=None):
        return [ifile(child) for child in path.path.dirs(self, pattern)]

    def files(self, pattern=None):
        return [ifile(child) for child in path.path.files(self, pattern)]

    def walk(self, pattern=None):
        for child in path.path.walk(self, pattern):
            yield ifile(child)

    def walkdirs(self, pattern=None):
        for child in path.path.walkdirs(self, pattern):
            yield ifile(child)

    def walkfiles(self, pattern=None):
        for child in path.path.walkfiles(self, pattern):
            yield ifile(child)

    def glob(self, pattern):
        return map(ifile, path.path.glob(self, pattern))

    if hasattr(os, 'readlink'):
        def readlink(self):
            return ifile(path.path.readlink(self))

        def readlinkabs(self):
            return ifile(path.path.readlinkabs(self))

    def getmode(self):
        return self.stat().st_mode
    mode = property(getmode, None, None, "Access mode")

    def gettype(self):
        data = [
            (stat.S_ISREG, "file"),
            (stat.S_ISDIR, "dir"),
            (stat.S_ISCHR, "chardev"),
            (stat.S_ISBLK, "blockdev"),
            (stat.S_ISFIFO, "fifo"),
            (stat.S_ISLNK, "symlink"),
            (stat.S_ISSOCK,"socket"),
        ]
        lstat = self.lstat()
        if lstat is not None:
            types = set([text for (func, text) in data if func(lstat.st_mode)])
        else:
            types = set()
        m = self.mode
        types.update([text for (func, text) in data if func(m)])
        return ", ".join(types)
    type = property(gettype, None, None, "file type (file, directory, link, etc.)")

    def getmodestr(self):
        m = self.mode
        data = [
            (stat.S_IRUSR, "-r"),
            (stat.S_IWUSR, "-w"),
            (stat.S_IXUSR, "-x"),
            (stat.S_IRGRP, "-r"),
            (stat.S_IWGRP, "-w"),
            (stat.S_IXGRP, "-x"),
            (stat.S_IROTH, "-r"),
            (stat.S_IWOTH, "-w"),
            (stat.S_IXOTH, "-x"),
        ]
        return "".join([text[bool(m&bit)] for (bit, text) in data])

    modestr = property(getmodestr, None, None, "Access mode as string")

    def getblocks(self):
        return self.stat().st_blocks
    blocks = property(getblocks, None, None, "File size in blocks")

    def getblksize(self):
        return self.stat().st_blksize
    blksize = property(getblksize, None, None, "Filesystem block size")

    def getdev(self):
        return self.stat().st_dev
    dev = property(getdev)

    def getnlink(self):
        return self.stat().st_nlink
    nlink = property(getnlink, None, None, "Number of links")

    def getuid(self):
        return self.stat().st_uid
    uid = property(getuid, None, None, "User id of file owner")

    def getgid(self):
        return self.stat().st_gid
    gid = property(getgid, None, None, "Group id of file owner")

    def getowner(self):
        stat = self.stat()
        try:
            return pwd.getpwuid(stat.st_uid).pw_name
        except KeyError:
            return stat.st_uid
    owner = property(getowner, None, None, "Owner name (or id)")

    def getgroup(self):
        stat = self.stat()
        try:
            return grp.getgrgid(stat.st_gid).gr_name
        except KeyError:
            return stat.st_gid
    group = property(getgroup, None, None, "Group name (or id)")

    def getadate(self):
        return datetime.datetime.utcfromtimestamp(self.atime)
    adate = property(getadate, None, None, "Access date")

    def getcdate(self):
        return datetime.datetime.utcfromtimestamp(self.ctime)
    cdate = property(getcdate, None, None, "Creation date")

    def getmdate(self):
        return datetime.datetime.utcfromtimestamp(self.mtime)
    mdate = property(getmdate, None, None, "Modification date")

    def getmimetype(self):
        return mimetypes.guess_type(self.basename())[0]
    mimetype = property(getmimetype, None, None, "MIME type")

    def getencoding(self):
        return mimetypes.guess_type(self.basename())[1]
    encoding = property(getencoding, None, None, "Compression")

    def __repr__(self):
        return "ifile(%s)" % path._base.__repr__(self)

    defaultattrs = (None, "type", "size", "modestr", "owner", "group", "mdate")

    def __xattrs__(self, mode):
        if mode == "detail":
            return (
                "name", "basename()", "abspath()", "realpath()",
                "type", "mode", "modestr", "stat()", "lstat()",
                "uid", "gid", "owner", "group", "dev", "nlink",
                "ctime", "mtime", "atime", "cdate", "mdate", "adate",
                "size", "blocks", "blksize", "isdir()", "islink()",
                "mimetype", "encoding"
            )
        return self.defaultattrs

    def __xrepr__(self, mode):
        yield (-1, True)
        try:
            if self.isdir():
                name = "idir"
                style = style_dir
            else:
                name = "ifile"
                style = style_file
        except IOError:
            name = "ifile"
            style = style_default
        if mode == "cell" or mode in "header" or mode == "footer":
            abspath = repr(path._base(self.normpath()))
            if abspath.startswith("u"):
                abspath = abspath[2:-1]
            else:
                abspath = abspath[1:-1]
            if mode == "cell":
                yield (style, abspath)
            else:
                yield (style, "%s(%s)" % (name, abspath))
        else:
            yield (style, repr(self))

    def __xiter__(self, mode):
        if self.isdir():
            yield iparentdir(self / os.pardir)
            for child in sorted(self.listdir()):
                yield child
        else:
            f = self.open("rb")
            for line in f:
                yield line
            f.close()


class iparentdir(ifile):
    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "cell":
            yield (style_dir, os.pardir)
        else:
            for part in ifile.__xrepr__(self, mode):
                yield part


class ils(Table):
    """
    List the current (or a specific) directory.

    Examples:

        >>> ils
        >>> ils("/usr/local/lib/python2.4")
        >>> ils("~")
    """
    def __init__(self, base=os.curdir):
        self.base = os.path.expanduser(base)

    def __xiter__(self, mode):
        return xiter(ifile(self.base), mode)

    def __xrepr__(self, mode):
       return ifile(self.base).__xrepr__(mode)

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self.base)


class iglob(Table):
    """
    List all files and directories matching a specified pattern.
    (See ``glob.glob()`` for more info.).

    Examples:

        >>> iglob("*.py")
    """
    def __init__(self, glob):
        self.glob = glob

    def __xiter__(self, mode):
        for name in glob.glob(self.glob):
            yield ifile(name)

    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "header" or mode == "footer" or mode == "cell":
            yield (style_default, "%s(%r)" % (self.__class__.__name__, self.glob))
        else:
            yield (style_default, repr(self))

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self.glob)


class iwalk(Table):
    """
    List all files and directories in a directory and it's subdirectory.

        >>> iwalk
        >>> iwalk("/usr/local/lib/python2.4")
        >>> iwalk("~")
    """
    def __init__(self, base=os.curdir, dirs=True, files=True):
        self.base = os.path.expanduser(base)
        self.dirs = dirs
        self.files = files

    def __xiter__(self, mode):
        for (dirpath, dirnames, filenames) in os.walk(self.base):
            if self.dirs:
                for name in sorted(dirnames):
                    yield ifile(os.path.join(dirpath, name))
            if self.files:
                for name in sorted(filenames):
                    yield ifile(os.path.join(dirpath, name))

    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "header" or mode == "footer" or mode == "cell":
            yield (style_default, "%s(%r)" % (self.__class__.__name__, self.base))
        else:
            yield (style_default, repr(self))

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self.base)


class ipwdentry(object):
    """
    ``ipwdentry`` objects encapsulate entries in the Unix user account and
    password database.
    """
    def __init__(self, id):
        self._id = id
        self._entry = None

    def _getentry(self):
        if self._entry is None:
            if isinstance(self._id, basestring):
                self._entry = pwd.getpwnam(self._id)
            else:
                self._entry = pwd.getpwuid(self._id)
        return self._entry

    def getname(self):
        if isinstance(self._id, basestring):
            return self._id
        else:
            return self._getentry().pw_name
    name = property(getname, None, None, "User name")

    def getpasswd(self):
        return self._getentry().pw_passwd
    passwd = property(getpasswd, None, None, "Password")

    def getuid(self):
        if isinstance(self._id, basestring):
            return self._getentry().pw_uid
        else:
            return self._id
    uid = property(getuid, None, None, "User id")

    def getgid(self):
        return self._getentry().pw_gid
    gid = property(getgid, None, None, "Primary group id")

    def getgroup(self):
        return igrpentry(self.gid)
    group = property(getgroup, None, None, "Group")

    def getgecos(self):
        return self._getentry().pw_gecos
    gecos = property(getgecos, None, None, "Information (e.g. full user name)")

    def getdir(self):
        return self._getentry().pw_dir
    dir = property(getdir, None, None, "$HOME directory")

    def getshell(self):
        return self._getentry().pw_shell
    shell = property(getshell, None, None, "Login shell")

    def __xattrs__(self, mode):
        return ("name", "passwd", "uid", "gid", "gecos", "dir", "shell")

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self._id)


class ipwd(Table):
    """
    List all entries in the Unix user account and password database.

    Example:

        >>> ipwd | isort("uid")
    """
    def __iter__(self):
        for entry in pwd.getpwall():
            yield ipwdentry(entry.pw_name)

    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "header" or mode == "footer" or mode == "cell":
            yield (style_default, "%s()" % self.__class__.__name__)
        else:
            yield (style_default, repr(self))


class igrpentry(object):
    """
    ``igrpentry`` objects encapsulate entries in the Unix group database.
    """
    def __init__(self, id):
        self._id = id
        self._entry = None

    def _getentry(self):
        if self._entry is None:
            if isinstance(self._id, basestring):
                self._entry = grp.getgrnam(self._id)
            else:
                self._entry = grp.getgrgid(self._id)
        return self._entry

    def getname(self):
        if isinstance(self._id, basestring):
            return self._id
        else:
            return self._getentry().gr_name
    name = property(getname, None, None, "Group name")

    def getpasswd(self):
        return self._getentry().gr_passwd
    passwd = property(getpasswd, None, None, "Password")

    def getgid(self):
        if isinstance(self._id, basestring):
            return self._getentry().gr_gid
        else:
            return self._id
    gid = property(getgid, None, None, "Group id")

    def getmem(self):
        return self._getentry().gr_mem
    mem = property(getmem, None, None, "Members")

    def __xattrs__(self, mode):
        return ("name", "passwd", "gid", "mem")

    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "header" or mode == "footer" or mode == "cell":
            yield (style_default, "group ")
            try:
                yield (style_default, self.name)
            except KeyError:
                if isinstance(self._id, basestring):
                    yield (style_default, self.name_id)
                else:
                    yield (style_type_number, str(self._id))
        else:
            yield (style_default, repr(self))

    def __xiter__(self, mode):
        for member in self.mem:
            yield ipwdentry(member)

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self._id)


class igrp(Table):
    """
    This ``Table`` lists all entries in the Unix group database.
    """
    def __xiter__(self, mode):
        for entry in grp.getgrall():
            yield igrpentry(entry.gr_name)

    def __xrepr__(self, mode):
        yield (-1, False)
        if mode == "header" or mode == "footer":
            yield (style_default, "%s()" % self.__class__.__name__)
        else:
            yield (style_default, repr(self))


class Fields(object):
    def __init__(self, fieldnames, **fields):
        self.__fieldnames = fieldnames
        for (key, value) in fields.iteritems():
            setattr(self, key, value)

    def __xattrs__(self, mode):
        return self.__fieldnames

    def __xrepr__(self, mode):
        yield (-1, False)
        if mode == "header" or mode == "cell":
            yield (style_default, self.__class__.__name__)
            yield (style_default, "(")
            for (i, f) in enumerate(self.__fieldnames):
                if i:
                    yield (style_default, ", ")
                yield (style_default, f)
                yield (style_default, "=")
                for part in xrepr(getattr(self, f), "default"):
                    yield part
            yield (style_default, ")")
        elif mode == "footer":
            yield (style_default, self.__class__.__name__)
            yield (style_default, "(")
            for (i, f) in enumerate(self.__fieldnames):
                if i:
                    yield (style_default, ", ")
                yield (style_default, f)
            yield (style_default, ")")
        else:
            yield (style_default, repr(self))


class FieldTable(Table, list):
    def __init__(self, *fields):
        Table.__init__(self)
        list.__init__(self)
        self.fields = fields

    def add(self, **fields):
        self.append(Fields(self.fields, **fields))

    def __xiter__(self, mode):
        return list.__iter__(self)

    def __xrepr__(self, mode):
        yield (-1, False)
        if mode == "header" or mode == "footer":
            yield (style_default, self.__class__.__name__)
            yield (style_default, "(")
            for (i, f) in enumerate(self.__fieldnames):
                if i:
                    yield (style_default, ", ")
                yield (style_default, f)
            yield (style_default, ")")
        else:
            yield (style_default, repr(self))

    def __repr__(self):
        return "<%s.%s object with fields=%r at 0x%x>" % \
            (self.__class__.__module__, self.__class__.__name__,
             ", ".join(map(repr, self.fields)), id(self))


class List(list):
    def __xattrs__(self, mode):
        return xrange(len(self))

    def __xrepr__(self, mode):
        yield (-1, False)
        if mode == "header" or mode == "cell" or mode == "footer" or mode == "default":
            yield (style_default, self.__class__.__name__)
            yield (style_default, "(")
            for (i, item) in enumerate(self):
                if i:
                    yield (style_default, ", ")
                for part in xrepr(item, "default"):
                    yield part
            yield (style_default, ")")
        else:
            yield (style_default, repr(self))


class ienv(Table):
    """
    List environment variables.

    Example:

        >>> ienv
    """

    def __xiter__(self, mode):
        fields = ("key", "value")
        for (key, value) in os.environ.iteritems():
            yield Fields(fields, key=key, value=value)

    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "header" or mode == "cell":
            yield (style_default, "%s()" % self.__class__.__name__)
        else:
            yield (style_default, repr(self))


class icsv(Pipe):
    """
    This ``Pipe`` lists turn the input (with must be a pipe outputting lines
    or an ``ifile``) into lines of CVS columns.
    """
    def __init__(self, **csvargs):
        """
        Create an ``icsv`` object. ``cvsargs`` will be passed through as
        keyword arguments to ``cvs.reader()``.
        """
        self.csvargs = csvargs

    def __xiter__(self, mode):
        input = self.input
        if isinstance(input, ifile):
            input = input.open("rb")
        reader = csv.reader(input, **self.csvargs)
        for line in reader:
            yield List(line)

    def __xrepr__(self, mode):
        yield (-1, False)
        if mode == "header" or mode == "footer":
            input = getattr(self, "input", None)
            if input is not None:
                for part in xrepr(input, mode):
                    yield part
                yield (style_default, " | ")
            yield (style_default, "%s(" % self.__class__.__name__)
            for (i, (name, value)) in enumerate(self.csvargs.iteritems()):
                if i:
                    yield (style_default, ", ")
                yield (style_default, name)
                yield (style_default, "=")
                for part in xrepr(value, "default"):
                    yield part
            yield (style_default, ")")
        else:
            yield (style_default, repr(self))

    def __repr__(self):
        args = ", ".join(["%s=%r" % item for item in self.csvargs.iteritems()])
        return "<%s.%s %s at 0x%x>" % \
        (self.__class__.__module__, self.__class__.__name__, args, id(self))


class ix(Table):
    """
    Execute a system command and list its output as lines
    (similar to ``os.popen()``).

    Examples:

        >>> ix("ps x")
        >>> ix("find .") | ifile
    """
    def __init__(self, cmd):
        self.cmd = cmd
        self._pipe = None

    def __xiter__(self, mode):
        self._pipe = os.popen(self.cmd)
        for l in self._pipe:
            yield l.rstrip("\r\n")
        self._pipe.close()
        self._pipe = None

    def __del__(self):
        if self._pipe is not None and not self._pipe.closed:
            self._pipe.close()
        self._pipe = None

    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "header" or mode == "footer":
            yield (style_default, "%s(%r)" % (self.__class__.__name__, self.cmd))
        else:
            yield (style_default, repr(self))

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self.cmd)


class ifilter(Pipe):
    """
    Filter an input pipe. Only objects where an expression evaluates to true
    (and doesn't raise an exception) are listed.

    Examples:

        >>> ils | ifilter("_.isfile() and size>1000")
        >>> igrp | ifilter("len(mem)")
        >>> sys.modules | ifilter(lambda _:_.value is not None)
    """

    def __init__(self, expr, errors="raiseifallfail"):
        """
        Create an ``ifilter`` object. ``expr`` can be a callable or a string
        containing an expression. ``errors`` specifies how exception during
        evaluation of ``expr`` are handled:

        * ``drop``: drop all items that have errors;

        * ``keep``: keep all items that have errors;

        * ``keeperror``: keep the exception of all items that have errors;

        * ``raise``: raise the exception;

        * ``raiseifallfail``: raise the first exception if all items have errors;
          otherwise drop those with errors (this is the default).
        """
        self.expr = expr
        self.errors = errors

    def __xiter__(self, mode):
        if callable(self.expr):
            def test(item):
                return self.expr(item)
        else:
            def test(item):
                return eval(self.expr, globals(), _AttrNamespace(item))

        ok = 0
        exc_info = None
        for item in xiter(self.input, mode):
            try:
                if test(item):
                    yield item
                ok += 1
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception, exc:
                if self.errors == "drop":
                    pass # Ignore errors
                elif self.errors == "keep":
                    yield item
                elif self.errors == "keeperror":
                    yield exc
                elif self.errors == "raise":
                    raise
                elif self.errors == "raiseifallfail":
                    if exc_info is None:
                        exc_info = sys.exc_info()
        if not ok and exc_info is not None:
            raise exc_info[0], exc_info[1], exc_info[2]

    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "header" or mode == "footer":
            input = getattr(self, "input", None)
            if input is not None:
                for part in xrepr(input, mode):
                    yield part
                yield (style_default, " | ")
            yield (style_default, "%s(" % self.__class__.__name__)
            for part in xrepr(self.expr, "default"):
                yield part
            yield (style_default, ")")
        else:
            yield (style_default, repr(self))

    def __repr__(self):
        return "<%s.%s expr=%r at 0x%x>" % \
            (self.__class__.__module__, self.__class__.__name__,
             self.expr, id(self))


class ieval(Pipe):
    """
    Evaluate an expression for each object in the input pipe.

    Examples:

        >>> ils | ieval("_.abspath()")
        >>> sys.path | ieval(ifile)
    """

    def __init__(self, expr, errors="raiseifallfail"):
        """
        Create an ``ieval`` object. ``expr`` can be a callable or a string
        containing an expression. For the meaning of ``errors`` see ``ifilter``.
        """
        self.expr = expr
        self.errors = errors

    def __xiter__(self, mode):
        if callable(self.expr):
            def do(item):
                return self.expr(item)
        else:
            def do(item):
                return eval(self.expr, globals(), _AttrNamespace(item))

        ok = 0
        exc_info = None
        for item in xiter(self.input, mode):
            try:
                yield do(item)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception, exc:
                if self.errors == "drop":
                    pass # Ignore errors
                elif self.errors == "keep":
                    yield item
                elif self.errors == "keeperror":
                    yield exc
                elif self.errors == "raise":
                    raise
                elif self.errors == "raiseifallfail":
                    if exc_info is None:
                        exc_info = sys.exc_info()
        if not ok and exc_info is not None:
            raise exc_info[0], exc_info[1], exc_info[2]

    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "header" or mode == "footer":
            input = getattr(self, "input", None)
            if input is not None:
                for part in xrepr(input, mode):
                    yield part
                yield (style_default, " | ")
            yield (style_default, "%s(" % self.__class__.__name__)
            for part in xrepr(self.expr, "default"):
                yield part
            yield (style_default, ")")
        else:
            yield (style_default, repr(self))

    def __repr__(self):
        return "<%s.%s expr=%r at 0x%x>" % \
            (self.__class__.__module__, self.__class__.__name__,
             self.expr, id(self))


class ienum(Pipe):
    """
    Enumerate the input pipe (i.e. wrap each input object in an object
    with ``index`` and ``object`` attributes).

    Examples:

        >>> xrange(20) | ieval("_,_*_") | ienum | ifilter("index % 2 == 0") | ieval("object")
    """
    def __xiter__(self, mode):
        fields = ("index", "object")
        for (index, object) in enumerate(xiter(self.input, mode)):
            yield Fields(fields, index=index, object=object)


class isort(Pipe):
    """
    Sorts the input pipe.

    Examples:

        >>> ils | isort("size")
        >>> ils | isort("_.isdir(), _.lower()", reverse=True)
    """

    def __init__(self, key, reverse=False):
        """
        Create an ``isort`` object. ``key`` can be a callable or a string
        containing an expression. If ``reverse`` is true the sort order will
        be reversed.
        """
        self.key = key
        self.reverse = reverse

    def __xiter__(self, mode):
        if callable(self.key):
            items = sorted(
                xiter(self.input, mode),
                key=self.key,
                reverse=self.reverse
            )
        else:
            def key(item):
                return eval(self.key, globals(), _AttrNamespace(item))
            items = sorted(
                xiter(self.input, mode),
                key=key,
                reverse=self.reverse
            )
        for item in items:
            yield item

    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "header" or mode == "footer":
            input = getattr(self, "input", None)
            if input is not None:
                for part in xrepr(input, mode):
                    yield part
                yield (style_default, " | ")
            yield (style_default, "%s(" % self.__class__.__name__)
            for part in xrepr(self.key, "default"):
                yield part
            if self.reverse:
                yield (style_default, ", ")
                for part in xrepr(True, "default"):
                    yield part
            yield (style_default, ")")
        else:
            yield (style_default, repr(self))

    def __repr__(self):
        return "<%s.%s key=%r reverse=%r at 0x%x>" % \
            (self.__class__.__module__, self.__class__.__name__,
             self.key, self.reverse, id(self))


tab = 3 # for expandtabs()

def _format(field):
    if isinstance(field, str):
        text = repr(field.expandtabs(tab))[1:-1]
    elif isinstance(field, unicode):
        text = repr(field.expandtabs(tab))[2:-1]
    elif isinstance(field, datetime.datetime):
        # Don't use strftime() here, as this requires year >= 1900
        text = "%04d-%02d-%02d %02d:%02d:%02d.%06d" % \
            (field.year, field.month, field.day,
             field.hour, field.minute, field.second, field.microsecond)
    elif isinstance(field, datetime.date):
        text = "%04d-%02d-%02d" % (field.year, field.month, field.day)
    else:
        text = repr(field)
    return text


class Display(object):
    class __metaclass__(type):
        def __ror__(self, input):
            return input | self()

    def __ror__(self, input):
        self.input = input
        return self

    def display(self):
        pass


class iless(Display):
    cmd = "less --quit-if-one-screen --LONG-PROMPT --LINE-NUMBERS --chop-long-lines --shift=8 --RAW-CONTROL-CHARS"

    def display(self):
        try:
            pager = os.popen(self.cmd, "w")
            try:
                for item in xiter(self.input, "default"):
                    attrs = xattrs(item, "default")
                    attrs = ["%s=%s" % (a, _format(_getattr(item, a))) for a in attrs]
                    pager.write(" ".join(attrs))
                    pager.write("\n")
            finally:
                pager.close()
        except Exception, exc:
            print "%s: %s" % (exc.__class__.__name__, str(exc))


def xformat(value, mode, maxlength):
    align = None
    full = False
    width = 0
    text = Text()
    for part in xrepr(value, mode):
        # part is (alignment, stop)
        if isinstance(part[0], int):
            # only consider the first occurence
            if align is None:
                align = part[0]
                full = part[1]
        # part is (style, text)
        else:
            text.append(part)
            width += len(part[1])
            if width >= maxlength and not full:
                text.append((style_ellisis, "..."))
                width += 3
                break
    if align is None: # default to left alignment
        align = -1
    return (align, width, text)


class idump(Display):
    # The approximate maximum length of a column entry
    maxattrlength = 200

    # Style for column names
    style_header = Style(COLOR_WHITE, COLOR_BLACK, A_BOLD)

    def __init__(self, *attrs):
        self.attrs = attrs
        self.headerpadchar = " "
        self.headersepchar = "|"
        self.datapadchar = " "
        self.datasepchar = "|"

    def display(self):
        stream = genutils.Term.cout
        allattrs = []
        allattrset = set()
        colwidths = {}
        rows = []
        for item in xiter(self.input, "default"):
            row = {}
            attrs = self.attrs
            if not attrs:
                attrs = xattrs(item, "default")
            for attrname in attrs:
                if attrname not in allattrset:
                    allattrs.append(attrname)
                    allattrset.add(attrname)
                    colwidths[attrname] = len(_attrname(attrname))
                try:
                    value = _getattr(item, attrname, None)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception, exc:
                    value = exc
                (align, width, text) = xformat(value, "cell", self.maxattrlength)
                colwidths[attrname] = max(colwidths[attrname], width)
                # remember alignment, length and colored parts
                row[attrname] = (align, width, text)
            rows.append(row)

        stream.write("\n")
        for (i, attrname) in enumerate(allattrs):
            self.style_header(_attrname(attrname)).write(stream)
            spc = colwidths[attrname] - len(_attrname(attrname))
            if i < len(colwidths)-1:
                stream.write(self.headerpadchar*spc)
                stream.write(self.headersepchar)
        stream.write("\n")

        for row in rows:
            for (i, attrname) in enumerate(allattrs):
                (align, width, text) = row[attrname]
                spc = colwidths[attrname] - width
                if align == -1:
                    text.write(stream)
                    if i < len(colwidths)-1:
                        stream.write(self.datapadchar*spc)
                elif align == 0:
                    spc = colwidths[attrname] - width
                    spc1 = spc//2
                    spc2 = spc-spc1
                    stream.write(self.datapadchar*spc1)
                    text.write(stream)
                    if i < len(colwidths)-1:
                        stream.write(self.datapadchar*spc2)
                else:
                    stream.write(self.datapadchar*spc)
                    text.write(stream)
                if i < len(colwidths)-1:
                    stream.write(self.datasepchar)
            stream.write("\n")


class XMode(object):
    """
    An ``XMode`` object describes one enter mode available for an object
    """
    def __init__(self, object, mode, title=None, description=None):
        """
        Create a new ``XMode`` object for the object ``object``. This object
        must support the enter mode ``mode`` (i.e. ``object.__xiter__(mode)``
        must return an iterable). ``title`` and ``description`` will be
        displayed in the browser when selecting among the available modes.
        """
        self.object = object
        self.mode = mode
        self.title = title
        self.description = description

    def __repr__(self):
        return "<%s.%s object mode=%r at 0x%x>" % \
            (self.__class__.__module__, self.__class__.__name__,
             self.mode, id(self))

    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "header" or mode == "footer":
            yield (style_default, self.title)
        else:
            yield (style_default, repr(self))

    def __xattrs__(self, mode):
        if mode == "detail":
            return ("object", "mode", "title", "description")
        return ("title", "description")

    def __xiter__(self, mode):
        return xiter(self.object, self.mode)


class XAttr(object):
    def __init__(self, object, name):
        self.name = _attrname(name)

        try:
            self.value = _getattr(object, name)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, exc:
            if exc.__class__.__module__ == "exceptions":
                self.value = exc.__class__.__name__
            else:
                self.value = "%s.%s" % \
                    (exc.__class__.__module__, exc.__class__.__name__)
            self.type = self.value
        else:
            t = type(self.value)
            if t.__module__ == "__builtin__":
                self.type = t.__name__
            else:
                self.type = "%s.%s" % (t.__module__, t.__name__)

        doc = None
        if isinstance(name, basestring):
            if name.endswith("()"):
                doc = getattr(getattr(object, name[:-2]), "__doc__", None)
            else:
                try:
                    meta = getattr(type(object), name)
                except AttributeError:
                    pass
                else:
                    if isinstance(meta, property):
                        doc = getattr(meta, "__doc__", None)
        elif callable(name):
            doc = getattr(name, "__doc__", None)
        if isinstance(doc, basestring):
            doc = doc.strip()
        self.doc = doc

    def __xattrs__(self, mode):
        return ("name", "type", "doc", "value")


_ibrowse_help = """
down
Move the cursor to the next line.

up
Move the cursor to the previous line.

pagedown
Move the cursor down one page (minus overlap).

pageup
Move the cursor up one page (minus overlap).

left
Move the cursor left.

right
Move the cursor right.

home
Move the cursor to the first column.

end
Move the cursor to the last column.

prevattr
Move the cursor one attribute column to the left.

nextattr
Move the cursor one attribute column to the right.

pick
'Pick' the object under the cursor (i.e. the row the cursor is on). This
leaves the browser and returns the picked object to the caller. (In IPython
this object will be available as the '_' variable.)

pickattr
'Pick' the attribute under the cursor (i.e. the row/column the cursor is on).

pickallattrs
Pick' the complete column under the cursor (i.e. the attribute under the
cursor) from all currently fetched objects. These attributes will be returned
as a list.

tooglemark
Mark/unmark the object under the cursor. Marked objects have a '!' after the
row number).

pickmarked
'Pick' marked objects. Marked objects will be returned as a list.

pickmarkedattr
'Pick' the attribute under the cursor from all marked objects (This returns a
list).

enterdefault
Enter the object under the cursor. (what this mean depends on the object
itself (i.e. how it implements the '__xiter__' method). This opens a new
browser 'level'.

enter
Enter the object under the cursor. If the object provides different enter
modes a menu of all modes will be presented; choose one and enter it (via the
'enter' or 'enterdefault' command).

enterattr
Enter the attribute under the cursor.

leave
Leave the current browser level and go back to the previous one.

detail
Show a detail view of the object under the cursor. This shows the name, type,
doc string and value of the object attributes (and it might show more
attributes than in the list view, depending on the object).

detailattr
Show a detail view of the attribute under the cursor.

markrange
Mark all objects from the last marked object before the current cursor
position to the cursor position.

sortattrasc
Sort the objects (in ascending order) using the attribute under the cursor as
the sort key.

sortattrdesc
Sort the objects (in descending order) using the attribute under the cursor as
the sort key.

goto
Jump to a row. The row number can be entered at the bottom of the screen.

find
Search forward for a row. At the bottom of the screen the condition can be
entered.

findbackwards
Search backward for a row. At the bottom of the screen the condition can be
entered.

help
This screen.
"""


if curses is not None:
    class UnassignedKeyError(Exception):
        """
        Exception that is used for reporting unassigned keys.
        """


    class UnknownCommandError(Exception):
        """
        Exception that is used for reporting unknown command (this should never
        happen).
        """


    class CommandError(Exception):
        """
        Exception that is used for reporting that a command can't be executed.
        """


    class _BrowserCachedItem(object):
        # This is used internally by ``ibrowse`` to store a item together with its
        # marked status.
        __slots__ = ("item", "marked")

        def __init__(self, item):
            self.item = item
            self.marked = False


    class _BrowserHelp(object):
        style_header = Style(COLOR_RED, COLOR_BLACK)
        # This is used internally by ``ibrowse`` for displaying the help screen.
        def __init__(self, browser):
            self.browser = browser

        def __xrepr__(self, mode):
            yield (-1, True)
            if mode == "header" or mode == "footer":
                yield (style_default, "ibrowse help screen")
            else:
                yield (style_default, repr(self))

        def __xiter__(self, mode):
            # Get reverse key mapping
            allkeys = {}
            for (key, cmd) in self.browser.keymap.iteritems():
                allkeys.setdefault(cmd, []).append(key)

            fields = ("key", "description")

            for (i, command) in enumerate(_ibrowse_help.strip().split("\n\n")):
                if i:
                    yield Fields(fields, key="", description="")

                (name, description) = command.split("\n", 1)
                keys = allkeys.get(name, [])
                lines = textwrap.wrap(description, 60)

                yield Fields(fields, description=Text((self.style_header, name)))
                for i in xrange(max(len(keys), len(lines))):
                    try:
                        key = self.browser.keylabel(keys[i])
                    except IndexError:
                        key = ""
                    try:
                        line = lines[i]
                    except IndexError:
                        line = ""
                    yield Fields(fields, key=key, description=line)


    class _BrowserLevel(object):
        # This is used internally to store the state (iterator, fetch items,
        # position of cursor and screen, etc.) of one browser level
        # An ``ibrowse`` object keeps multiple ``_BrowserLevel`` objects in
        # a stack.
        def __init__(self, browser, input, iterator, mainsizey, *attrs):
            self.browser = browser
            self.input = input
            self.header = [x for x in xrepr(input, "header") if not isinstance(x[0], int)]
            # iterator for the input
            self.iterator = iterator

            # is the iterator exhausted?
            self.exhausted = False

            # attributes to be display (autodetected if empty)
            self.attrs = attrs

            # fetched items (+ marked flag)
            self.items = deque()

            # Number of marked objects
            self.marked = 0

            # Vertical cursor position
            self.cury = 0

            # Horizontal cursor position
            self.curx = 0

            # Index of first data column
            self.datastartx = 0

            # Index of first data line
            self.datastarty = 0

            # height of the data display area
            self.mainsizey = mainsizey

            # width of the data display area (changes when scrolling)
            self.mainsizex = 0

            # Size of row number (changes when scrolling)
            self.numbersizex = 0

            # Attribute names to display (in this order)
            self.displayattrs = []

            # index and name of attribute under the cursor
            self.displayattr = (None, _default)

            # Maps attribute names to column widths
            self.colwidths = {}

            self.fetch(mainsizey)
            self.calcdisplayattrs()
            # formatted attributes for the items on screen
            # (i.e. self.items[self.datastarty:self.datastarty+self.mainsizey])
            self.displayrows = [self.getrow(i) for i in xrange(len(self.items))]
            self.calcwidths()
            self.calcdisplayattr()

        def fetch(self, count):
            # Try to fill ``self.items`` with at least ``count`` objects.
            have = len(self.items)
            while not self.exhausted and have < count:
                try:
                    item = self.iterator.next()
                except StopIteration:
                    self.exhausted = True
                    break
                else:
                    have += 1
                    self.items.append(_BrowserCachedItem(item))

        def calcdisplayattrs(self):
            # Calculate which attributes are available from the objects that are
            # currently visible on screen (and store it in ``self.displayattrs``)
            attrnames = set()
            # If the browser object specifies a fixed list of attributes,
            # simply use it.
            if self.attrs:
                self.displayattrs = self.attrs
            else:
                self.displayattrs = []
                endy = min(self.datastarty+self.mainsizey, len(self.items))
                for i in xrange(self.datastarty, endy):
                    for attrname in xattrs(self.items[i].item, "default"):
                        if attrname not in attrnames:
                            self.displayattrs.append(attrname)
                            attrnames.add(attrname)

        def getrow(self, i):
            # Return a dictinary with the attributes for the object
            # ``self.items[i]``. Attribute names are taken from
            # ``self.displayattrs`` so ``calcdisplayattrs()`` must have been
            # called before.
            row = {}
            item = self.items[i].item
            for attrname in self.displayattrs:
                try:
                    value = _getattr(item, attrname, _default)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception, exc:
                    value = exc
                # only store attribute if it exists (or we got an exception)
                if value is not _default:
                    parts = []
                    totallength = 0
                    align = None
                    full = False
                    # Collect parts until we have enough
                    for part in xrepr(value, "cell"):
                        # part gives (alignment, stop)
                        # instead of (style, text)
                        if isinstance(part[0], int):
                            # only consider the first occurence
                            if align is None:
                                align = part[0]
                                full = part[1]
                        else:
                            parts.append(part)
                            totallength += len(part[1])
                            if totallength >= self.browser.maxattrlength and not full:
                                parts.append((style_ellisis, "..."))
                                totallength += 3
                                break
                    # remember alignment, length and colored parts
                    row[attrname] = (align, totallength, parts)
            return row

        def calcwidths(self):
            # Recalculate the displayed fields and their width.
            # ``calcdisplayattrs()'' must have been called and the cache
            # for attributes of the objects on screen (``self.displayrows``)
            # must have been filled. This returns a dictionary mapping
            # colmn names to width.
            self.colwidths = {}
            for row in self.displayrows:
                for attrname in self.displayattrs:
                    try:
                        length = row[attrname][1]
                    except KeyError:
                        length = 0
                    # always add attribute to colwidths, even if it doesn't exist
                    if attrname not in self.colwidths:
                        self.colwidths[attrname] = len(_attrname(attrname))
                    newwidth = max(self.colwidths[attrname], length)
                    self.colwidths[attrname] = newwidth

            # How many characters do we need to paint the item number?
            self.numbersizex = len(str(self.datastarty+self.mainsizey-1))
            # How must space have we got to display data?
            self.mainsizex = self.browser.scrsizex-self.numbersizex-3
            # width of all columns
            self.datasizex = sum(self.colwidths.itervalues()) + len(self.colwidths)

        def calcdisplayattr(self):
            # Find out on which attribute the cursor is on and store this
            # information in ``self.displayattr``.
            pos = 0
            for (i, attrname) in enumerate(self.displayattrs):
                if pos+self.colwidths[attrname] >= self.curx:
                    self.displayattr = (i, attrname)
                    break
                pos += self.colwidths[attrname]+1
            else:
                self.displayattr = (None, _default)

        def moveto(self, x, y, refresh=False):
            # Move the cursor to the position ``(x,y)`` (in data coordinates,
            # not in screen coordinates). If ``refresh`` is true, all cached
            # values will be recalculated (e.g. because the list has been
            # resorted, so screen positions etc. are no longer valid).
            olddatastarty = self.datastarty
            oldx = self.curx
            oldy = self.cury
            x = int(x+0.5)
            y = int(y+0.5)
            newx = x # remember where we wanted to move
            newy = y # remember where we wanted to move

            scrollbordery = min(self.browser.scrollbordery, self.mainsizey//2)
            scrollborderx = min(self.browser.scrollborderx, self.mainsizex//2)

            # Make sure that the cursor didn't leave the main area vertically
            if y < 0:
                y = 0
            self.fetch(y+scrollbordery+1) # try to get more items
            if y >= len(self.items):
                y = max(0, len(self.items)-1)

            # Make sure that the cursor stays on screen vertically
            if y < self.datastarty+scrollbordery:
                self.datastarty = max(0, y-scrollbordery)
            elif y >= self.datastarty+self.mainsizey-scrollbordery:
                self.datastarty = max(0, min(y-self.mainsizey+scrollbordery+1,
                                             len(self.items)-self.mainsizey))

            if refresh: # Do we need to refresh the complete display?
                self.calcdisplayattrs()
                endy = min(self.datastarty+self.mainsizey, len(self.items))
                self.displayrows = map(self.getrow, xrange(self.datastarty, endy))
                self.calcwidths()
            # Did we scroll vertically => update displayrows
            # and various other attributes
            elif self.datastarty != olddatastarty:
                # Recalculate which attributes we have to display
                olddisplayattrs = self.displayattrs
                self.calcdisplayattrs()
                # If there are new attributes, recreate the cache
                if self.displayattrs != olddisplayattrs:
                    endy = min(self.datastarty+self.mainsizey, len(self.items))
                    self.displayrows = map(self.getrow, xrange(self.datastarty, endy))
                elif self.datastarty<olddatastarty: # we did scroll up
                    # drop rows from the end
                    del self.displayrows[self.datastarty-olddatastarty:]
                    # fetch new items
                    for i in xrange(olddatastarty-1,
                                    self.datastarty-1, -1):
                        try:
                            row = self.getrow(i)
                        except IndexError:
                            # we didn't have enough objects to fill the screen
                            break
                        self.displayrows.insert(0, row)
                else: # we did scroll down
                    # drop rows from the start
                    del self.displayrows[:self.datastarty-olddatastarty]
                    # fetch new items
                    for i in xrange(olddatastarty+self.mainsizey,
                                    self.datastarty+self.mainsizey):
                        try:
                            row = self.getrow(i)
                        except IndexError:
                            # we didn't have enough objects to fill the screen
                            break
                        self.displayrows.append(row)
                self.calcwidths()

            # Make sure that the cursor didn't leave the data area horizontally
            if x < 0:
                x = 0
            elif x >= self.datasizex:
                x = max(0, self.datasizex-1)

            # Make sure that the cursor stays on screen horizontally
            if x < self.datastartx+scrollborderx:
                self.datastartx = max(0, x-scrollborderx)
            elif x >= self.datastartx+self.mainsizex-scrollborderx:
                self.datastartx = max(0, min(x-self.mainsizex+scrollborderx+1,
                                             self.datasizex-self.mainsizex))

            if x == oldx and y == oldy and (x != newx or y != newy): # couldn't move
                self.browser.beep()
            else:
                self.curx = x
                self.cury = y
                self.calcdisplayattr()

        def sort(self, key, reverse=False):
            """
            Sort the currently list of items using the key function ``key``. If
            ``reverse`` is true the sort order is reversed.
            """
            curitem = self.items[self.cury] # Remember where the cursor is now

            # Sort items
            def realkey(item):
                return key(item.item)
            self.items = deque(sorted(self.items, key=realkey, reverse=reverse))

            # Find out where the object under the cursor went
            cury = self.cury
            for (i, item) in enumerate(self.items):
                if item is curitem:
                    cury = i
                    break

            self.moveto(self.curx, cury, refresh=True)


    class ibrowse(Display):
        # Show this many lines from the previous screen when paging horizontally
        pageoverlapx = 1

        # Show this many lines from the previous screen when paging vertically
        pageoverlapy = 1

        # Start scrolling when the cursor is less than this number of columns
        # away from the left or right screen edge
        scrollborderx = 10

        # Start scrolling when the cursor is less than this number of lines
        # away from the top or bottom screen edge
        scrollbordery = 5

        # Accelerate by this factor when scrolling horizontally
        acceleratex = 1.05

        # Accelerate by this factor when scrolling vertically
        acceleratey = 1.05

        # The maximum horizontal scroll speed
        # (as a factor of the screen width (i.e. 0.5 == half a screen width)
        maxspeedx = 0.5

        # The maximum vertical scroll speed
        # (as a factor of the screen height (i.e. 0.5 == half a screen height)
        maxspeedy = 0.5

        # The maximum number of header lines for browser level
        # if the nesting is deeper, only the innermost levels are displayed
        maxheaders = 5

        # The approximate maximum length of a column entry
        maxattrlength = 200

        # Styles for various parts of the GUI
        style_objheadertext = Style(COLOR_WHITE, COLOR_BLACK, A_BOLD|A_REVERSE)
        style_objheadernumber = Style(COLOR_WHITE, COLOR_BLUE, A_BOLD|A_REVERSE)
        style_objheaderobject = Style(COLOR_WHITE, COLOR_BLACK, A_REVERSE)
        style_colheader = Style(COLOR_BLUE, COLOR_WHITE, A_REVERSE)
        style_colheaderhere = Style(COLOR_GREEN, COLOR_BLACK, A_BOLD|A_REVERSE)
        style_colheadersep = Style(COLOR_BLUE, COLOR_BLACK, A_REVERSE)
        style_number = Style(COLOR_BLUE, COLOR_WHITE, A_REVERSE)
        style_numberhere = Style(COLOR_GREEN, COLOR_BLACK, A_BOLD|A_REVERSE)
        style_sep = Style(COLOR_BLUE, COLOR_BLACK)
        style_data = Style(COLOR_WHITE, COLOR_BLACK)
        style_datapad = Style(COLOR_BLUE, COLOR_BLACK, A_BOLD)
        style_footer = Style(COLOR_BLACK, COLOR_WHITE)
        style_report = Style(COLOR_WHITE, COLOR_BLACK)

        # Column separator in header
        headersepchar = "|"

        # Character for padding data cell entries
        datapadchar = "."

        # Column separator in data area
        datasepchar = "|"

        # Character to use for "empty" cell (i.e. for non-existing attributes)
        nodatachar = "-"

        # Prompts for modes that require keyboard input
        prompts = {
            "goto": "goto object #: ",
            "find": "find expression: ",
            "findbackwards": "find backwards expression: "
        }

        # Maps curses key codes to "function" names
        keymap = {
            ord("q"): "quit",
            curses.KEY_UP: "up",
            curses.KEY_DOWN: "down",
            curses.KEY_PPAGE: "pageup",
            curses.KEY_NPAGE: "pagedown",
            curses.KEY_LEFT: "left",
            curses.KEY_RIGHT: "right",
            curses.KEY_HOME: "home",
            curses.KEY_END: "end",
            ord("<"): "prevattr",
            0x1b:     "prevattr", # SHIFT-TAB
            ord(">"): "nextattr",
            ord("\t"):"nextattr", # TAB
            ord("p"): "pick",
            ord("P"): "pickattr",
            ord("C"): "pickallattrs",
            ord("m"): "pickmarked",
            ord("M"): "pickmarkedattr",
            ord("\n"): "enterdefault",
            # FIXME: What's happening here?
            8: "leave",
            127: "leave",
            curses.KEY_BACKSPACE: "leave",
            ord("x"): "leave",
            ord("h"): "help",
            ord("e"): "enter",
            ord("E"): "enterattr",
            ord("d"): "detail",
            ord("D"): "detailattr",
            ord(" "): "tooglemark",
            ord("r"): "markrange",
            ord("v"): "sortattrasc",
            ord("V"): "sortattrdesc",
            ord("g"): "goto",
            ord("f"): "find",
            ord("b"): "findbackwards",
        }

        def __init__(self, *attrs):
            """
            Create a new browser. If ``attrs`` is not empty, it is the list
            of attributes that will be displayed in the browser, otherwise
            these will be determined by the objects on screen.
            """
            self.attrs = attrs

            # Stack of browser levels
            self.levels = []
            # how many colums to scroll (Changes when accelerating)
            self.stepx = 1.

            # how many rows to scroll (Changes when accelerating)
            self.stepy = 1.

            # Beep on the edges of the data area? (Will be set to ``False``
            # once the cursor hits the edge of the screen, so we don't get
            # multiple beeps).
            self._dobeep = True

            # Cache for registered ``curses`` colors and styles.
            self._styles = {}
            self._colors = {}
            self._maxcolor = 1

            # How many header lines do we want to paint (the numbers of levels
            # we have, but with an upper bound)
            self._headerlines = 1

            # Index of first header line
            self._firstheaderline = 0

            # curses window
            self.scr = None
            # report in the footer line (error, executed command etc.)
            self._report = None

            # value to be returned to the caller (set by commands)
            self.returnvalue = None

            # The mode the browser is in
            # e.g. normal browsing or entering an argument for a command
            self.mode = "default"

            # The partially entered row number for the goto command
            self.goto = ""

        def nextstepx(self, step):
            """
            Accelerate horizontally.
            """
            return max(1., min(step*self.acceleratex,
                               self.maxspeedx*self.levels[-1].mainsizex))

        def nextstepy(self, step):
            """
            Accelerate vertically.
            """
            return max(1., min(step*self.acceleratey,
                               self.maxspeedy*self.levels[-1].mainsizey))

        def getstyle(self, style):
            """
            Register the ``style`` with ``curses`` or get it from the cache,
            if it has been registered before.
            """
            try:
                return self._styles[style.fg, style.bg, style.attrs]
            except KeyError:
                attrs = 0
                for b in A2CURSES:
                    if style.attrs & b:
                        attrs |= A2CURSES[b]
                try:
                    color = self._colors[style.fg, style.bg]
                except KeyError:
                    curses.init_pair(
                        self._maxcolor,
                        COLOR2CURSES[style.fg],
                        COLOR2CURSES[style.bg]
                    )
                    color = curses.color_pair(self._maxcolor)
                    self._colors[style.fg, style.bg] = color
                    self._maxcolor += 1
                c = color | attrs
                self._styles[style.fg, style.bg, style.attrs] = c
                return c

        def addstr(self, y, x, begx, endx, text, style):
            """
            A version of ``curses.addstr()`` that can handle ``x`` coordinates
            that are outside the screen.
            """
            text2 = text[max(0, begx-x):max(0, endx-x)]
            if text2:
                self.scr.addstr(y, max(x, begx), text2, self.getstyle(style))
            return len(text)

        def addchr(self, y, x, begx, endx, c, l, style):
            x0 = max(x, begx)
            x1 = min(x+l, endx)
            if x1>x0:
                self.scr.addstr(y, x0, c*(x1-x0), self.getstyle(style))
            return l

        def _calcheaderlines(self, levels):
            # Calculate how many headerlines do we have to display, if we have
            # ``levels`` browser levels
            if levels is None:
                levels = len(self.levels)
            self._headerlines = min(self.maxheaders, levels)
            self._firstheaderline = levels-self._headerlines

        def getstylehere(self, style):
            """
            Return a style for displaying the original style ``style``
            in the row the cursor is on.
            """
            return Style(style.fg, style.bg, style.attrs | A_BOLD)

        def report(self, msg):
            """
            Store the message ``msg`` for display below the footer line. This
            will be displayed as soon as the screen is redrawn.
            """
            self._report = msg

        def enter(self, item, mode, *attrs):
            """
            Enter the object ``item`` in the mode ``mode``. If ``attrs`` is
            specified, it will be used as a fixed list of attributes to display.
            """
            try:
                iterator = xiter(item, mode)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception, exc:
                curses.beep()
                self.report(exc)
            else:
                self._calcheaderlines(len(self.levels)+1)
                level = _BrowserLevel(
                    self,
                    item,
                    iterator,
                    self.scrsizey-1-self._headerlines-2,
                    *attrs
                )
                self.levels.append(level)

        def startkeyboardinput(self, mode):
            """
            Enter mode ``mode``, which requires keyboard input.
            """
            self.mode = mode
            self.keyboardinput = ""
            self.cursorpos = 0

        def executekeyboardinput(self, mode):
            exe = getattr(self, "exe_%s" % mode, None)
            if exe is not None:
               exe()
               self.mode = "default"

        def keylabel(self, keycode):
            """
            Return a pretty name for the ``curses`` key ``keycode`` (used in the
            help screen and in reports about unassigned keys).
            """
            if keycode <= 0xff:
                specialsnames = {
                    ord("\n"): "RETURN",
                    ord(" "): "SPACE",
                    ord("\t"): "TAB",
                    ord("\x7f"): "DELETE",
                    ord("\x08"): "BACKSPACE",
                }
                if keycode in specialsnames:
                    return specialsnames[keycode]
                return repr(chr(keycode))
            for name in dir(curses):
                if name.startswith("KEY_") and getattr(curses, name) == keycode:
                    return name
            return str(keycode)

        def beep(self, force=False):
            if force or self._dobeep:
                curses.beep()
                # don't beep again (as long as the same key is pressed)
                self._dobeep = False

        def cmd_quit(self):
            self.returnvalue = None
            return True

        def cmd_up(self):
            level = self.levels[-1]
            self.report("up")
            level.moveto(level.curx, level.cury-self.stepy)

        def cmd_down(self):
            level = self.levels[-1]
            self.report("down")
            level.moveto(level.curx, level.cury+self.stepy)

        def cmd_pageup(self):
            level = self.levels[-1]
            self.report("page up")
            level.moveto(level.curx, level.cury-level.mainsizey+self.pageoverlapy)

        def cmd_pagedown(self):
            level = self.levels[-1]
            self.report("page down")
            level.moveto(level.curx, level.cury+level.mainsizey-self.pageoverlapy)

        def cmd_left(self):
            level = self.levels[-1]
            self.report("left")
            level.moveto(level.curx-self.stepx, level.cury)

        def cmd_right(self):
            level = self.levels[-1]
            self.report("right")
            level.moveto(level.curx+self.stepx, level.cury)

        def cmd_home(self):
            level = self.levels[-1]
            self.report("home")
            level.moveto(0, level.cury)

        def cmd_end(self):
            level = self.levels[-1]
            self.report("end")
            level.moveto(level.datasizex+level.mainsizey-self.pageoverlapx, level.cury)

        def cmd_prevattr(self):
            level = self.levels[-1]
            if level.displayattr[0] is None or level.displayattr[0] == 0:
                self.beep()
            else:
                self.report("prevattr")
                pos = 0
                for (i, attrname) in enumerate(level.displayattrs):
                    if i == level.displayattr[0]-1:
                        break
                    pos += level.colwidths[attrname] + 1
                level.moveto(pos, level.cury)

        def cmd_nextattr(self):
            level = self.levels[-1]
            if level.displayattr[0] is None or level.displayattr[0] == len(level.displayattrs)-1:
                self.beep()
            else:
                self.report("nextattr")
                pos = 0
                for (i, attrname) in enumerate(level.displayattrs):
                    if i == level.displayattr[0]+1:
                        break
                    pos += level.colwidths[attrname] + 1
                level.moveto(pos, level.cury)

        def cmd_pick(self):
            level = self.levels[-1]
            self.returnvalue = level.items[level.cury].item
            return True

        def cmd_pickattr(self):
            level = self.levels[-1]
            attrname = level.displayattr[1]
            if attrname is _default:
                curses.beep()
                self.report(AttributeError(_attrname(attrname)))
                return
            attr = _getattr(level.items[level.cury].item, attrname)
            if attr is _default:
                curses.beep()
                self.report(AttributeError(_attrname(attrname)))
            else:
                self.returnvalue = attr
                return True

        def cmd_pickallattrs(self):
            level = self.levels[-1]
            attrname = level.displayattr[1]
            if attrname is _default:
                curses.beep()
                self.report(AttributeError(_attrname(attrname)))
                return
            result = []
            for cache in level.items:
                attr = _getattr(cache.item, attrname)
                if attr is not _default:
                    result.append(attr)
            self.returnvalue = result
            return True

        def cmd_pickmarked(self):
            level = self.levels[-1]
            self.returnvalue = [cache.item for cache in level.items if cache.marked]
            return True

        def cmd_pickmarkedattr(self):
            level = self.levels[-1]
            attrname = level.displayattr[1]
            if attrname is _default:
                curses.beep()
                self.report(AttributeError(_attrname(attrname)))
                return
            result = []
            for cache in level.items:
                if cache.marked:
                    attr = _getattr(cache.item, attrname)
                    if attr is not _default:
                        result.append(attr)
            self.returnvalue = result
            return True

        def cmd_markrange(self):
            level = self.levels[-1]
            self.report("markrange")
            start = None
            if level.items:
                for i in xrange(level.cury, -1, -1):
                    if level.items[i].marked:
                        start = i
                        break
            if start is None:
                self.report(CommandError("no mark before cursor"))
                curses.beep()
            else:
                for i in xrange(start, level.cury+1):
                    cache = level.items[i]
                    if not cache.marked:
                        cache.marked = True
                        level.marked += 1

        def cmd_enterdefault(self):
            level = self.levels[-1]
            try:
                item = level.items[level.cury].item
            except IndexError:
                self.report(CommandError("No object"))
                curses.beep()
            else:
                self.report("entering object (default mode)...")
                self.enter(item, "default")

        def cmd_leave(self):
            self.report("leave")
            if len(self.levels) > 1:
                self._calcheaderlines(len(self.levels)-1)
                self.levels.pop(-1)
            else:
                self.report(CommandError("This is the last level"))
                curses.beep()

        def cmd_enter(self):
            level = self.levels[-1]
            try:
                item = level.items[level.cury].item
            except IndexError:
                self.report(CommandError("No object"))
                curses.beep()
            else:
                self.report("entering object...")
                self.enter(item, None)

        def cmd_enterattr(self):
            level = self.levels[-1]
            attrname = level.displayattr[1]
            if attrname is _default:
                curses.beep()
                self.report(AttributeError(_attrname(attrname)))
                return
            try:
                item = level.items[level.cury].item
            except IndexError:
                self.report(CommandError("No object"))
                curses.beep()
            else:
                attr = _getattr(item, attrname)
                if attr is _default:
                    self.report(AttributeError(_attrname(attrname)))
                else:
                    self.report("entering object attribute %s..." % _attrname(attrname))
                    self.enter(attr, None)

        def cmd_detail(self):
            level = self.levels[-1]
            try:
                item = level.items[level.cury].item
            except IndexError:
                self.report(CommandError("No object"))
                curses.beep()
            else:
                self.report("entering detail view for object...")
                self.enter(item, "detail")

        def cmd_detailattr(self):
            level = self.levels[-1]
            attrname = level.displayattr[1]
            if attrname is _default:
                curses.beep()
                self.report(AttributeError(_attrname(attrname)))
                return
            try:
                item = level.items[level.cury].item
            except IndexError:
                self.report(CommandError("No object"))
                curses.beep()
            else:
                attr = _getattr(item, attrname)
                if attr is _default:
                    self.report(AttributeError(_attrname(attrname)))
                else:
                    self.report("entering detail view for attribute...")
                    self.enter(attr, "detail")

        def cmd_tooglemark(self):
            level = self.levels[-1]
            self.report("toggle mark")
            try:
                item = level.items[level.cury]
            except IndexError: # no items?
                pass
            else:
                if item.marked:
                    item.marked = False
                    level.marked -= 1
                else:
                    item.marked = True
                    level.marked += 1

        def cmd_sortattrasc(self):
            level = self.levels[-1]
            attrname = level.displayattr[1]
            if attrname is _default:
                curses.beep()
                self.report(AttributeError(_attrname(attrname)))
                return
            self.report("sort by %s (ascending)" % _attrname(attrname))
            def key(item):
                try:
                    return _getattr(item, attrname, None)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception:
                    return None
            level.sort(key)

        def cmd_sortattrdesc(self):
            level = self.levels[-1]
            attrname = level.displayattr[1]
            if attrname is _default:
                curses.beep()
                self.report(AttributeError(_attrname(attrname)))
                return
            self.report("sort by %s (descending)" % _attrname(attrname))
            def key(item):
                try:
                    return _getattr(item, attrname, None)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception:
                    return None
            level.sort(key, reverse=True)

        def cmd_goto(self):
            self.startkeyboardinput("goto")

        def exe_goto(self):
            level = self.levels[-1]
            if self.keyboardinput:
                level.moveto(level.curx, int(self.keyboardinput))

        def cmd_find(self):
            self.startkeyboardinput("find")

        def exe_find(self):
            level = self.levels[-1]
            if self.keyboardinput:
                while True:
                    cury = level.cury
                    level.moveto(level.curx, cury+1)
                    if cury == level.cury:
                        curses.beep()
                        break
                    item = level.items[level.cury].item
                    try:
                        if eval(self.keyboardinput, globals(), _AttrNamespace(item)):
                            break
                    except (KeyboardInterrupt, SystemExit):
                        raise
                    except Exception, exc:
                        self.report(exc)
                        curses.beep()
                        break # break on error

        def cmd_findbackwards(self):
            self.startkeyboardinput("findbackwards")

        def exe_findbackwards(self):
            level = self.levels[-1]
            if self.keyboardinput:
                while level.cury:
                    level.moveto(level.curx, level.cury-1)
                    item = level.items[level.cury].item
                    try:
                        if eval(self.keyboardinput, globals(), _AttrNamespace(item)):
                            break
                    except (KeyboardInterrupt, SystemExit):
                        raise
                    except Exception, exc:
                        self.report(exc)
                        curses.beep()
                        break # break on error
                else:
                    curses.beep()

        def cmd_help(self):
            """
            The help command
            """
            for level in self.levels:
                if isinstance(level.input, _BrowserHelp):
                    curses.beep()
                    self.report(CommandError("help already active"))
                    return

            self.enter(_BrowserHelp(self), "default")

        def _dodisplay(self, scr):
            """
            This method is the workhorse of the browser. It handles screen
            drawing and the keyboard.
            """
            self.scr = scr
            curses.halfdelay(1)
            footery = 2

            keys = []
            for (key, cmd) in self.keymap.iteritems():
                if cmd == "quit":
                    keys.append("%s=%s" % (self.keylabel(key), cmd))
            for (key, cmd) in self.keymap.iteritems():
                if cmd == "help":
                    keys.append("%s=%s" % (self.keylabel(key), cmd))
            helpmsg = " | %s" % " ".join(keys)

            scr.clear()
            msg = "Fetching first batch of objects..."
            (self.scrsizey, self.scrsizex) = scr.getmaxyx()
            scr.addstr(self.scrsizey//2, (self.scrsizex-len(msg))//2, msg)
            scr.refresh()

            lastc = -1

            self.levels = []
            # enter the first level
            self.enter(self.input, xiter(self.input, "default"), *self.attrs)

            self._calcheaderlines(None)

            while True:
                level = self.levels[-1]
                (self.scrsizey, self.scrsizex) = scr.getmaxyx()
                level.mainsizey = self.scrsizey-1-self._headerlines-footery

                # Paint object header
                for i in xrange(self._firstheaderline, self._firstheaderline+self._headerlines):
                    lv = self.levels[i]
                    posx = 0
                    posy = i-self._firstheaderline
                    endx = self.scrsizex
                    if i: # not the first level
                        msg = " (%d/%d" % (self.levels[i-1].cury, len(self.levels[i-1].items))
                        if not self.levels[i-1].exhausted:
                            msg += "+"
                        msg += ") "
                        endx -= len(msg)+1
                    posx += self.addstr(posy, posx, 0, endx, " ibrowse #%d: " % i, self.style_objheadertext)
                    for (style, text) in lv.header:
                        posx += self.addstr(posy, posx, 0, endx, text, self.style_objheaderobject)
                        if posx >= endx:
                            break
                    if i:
                        posx += self.addstr(posy, posx, 0, self.scrsizex, msg, self.style_objheadernumber)
                    posx += self.addchr(posy, posx, 0, self.scrsizex, " ", self.scrsizex-posx, self.style_objheadernumber)

                if not level.items:
                    self.addchr(self._headerlines, 0, 0, self.scrsizex, " ", self.scrsizex, self.style_colheader)
                    self.addstr(self._headerlines+1, 0, 0, self.scrsizex, " <empty>", style_error)
                    scr.clrtobot()
                else:
                    # Paint column headers
                    scr.move(self._headerlines, 0)
                    scr.addstr(" %*s " % (level.numbersizex, "#"), self.getstyle(self.style_colheader))
                    scr.addstr(self.headersepchar, self.getstyle(self.style_colheadersep))
                    begx = level.numbersizex+3
                    posx = begx-level.datastartx
                    for attrname in level.displayattrs:
                        strattrname = _attrname(attrname)
                        cwidth = level.colwidths[attrname]
                        header = strattrname.ljust(cwidth)
                        if attrname == level.displayattr[1]:
                            style = self.style_colheaderhere
                        else:
                            style = self.style_colheader
                        posx += self.addstr(self._headerlines, posx, begx, self.scrsizex, header, style)
                        posx += self.addstr(self._headerlines, posx, begx, self.scrsizex, self.headersepchar, self.style_colheadersep)
                        if posx >= self.scrsizex:
                            break
                    else:
                        scr.addstr(" "*(self.scrsizex-posx), self.getstyle(self.style_colheader))

                    # Paint rows
                    posy = self._headerlines+1+level.datastarty
                    for i in xrange(level.datastarty, min(level.datastarty+level.mainsizey, len(level.items))):
                        cache = level.items[i]
                        if i == level.cury:
                            style = self.style_numberhere
                        else:
                            style = self.style_number

                        posy = self._headerlines+1+i-level.datastarty
                        posx = begx-level.datastartx

                        scr.move(posy, 0)
                        scr.addstr(" %*d%s" % (level.numbersizex, i, " !"[cache.marked]), self.getstyle(style))
                        scr.addstr(self.headersepchar, self.getstyle(self.style_sep))

                        for attrname in level.displayattrs:
                            cwidth = level.colwidths[attrname]
                            try:
                                (align, length, parts) = level.displayrows[i-level.datastarty][attrname]
                            except KeyError:
                                align = 2
                                style = style_nodata
                            padstyle = self.style_datapad
                            sepstyle = self.style_sep
                            if i == level.cury:
                                padstyle = self.getstylehere(padstyle)
                                sepstyle = self.getstylehere(sepstyle)
                            if align == 2:
                                posx += self.addchr(posy, posx, begx, self.scrsizex, self.nodatachar, cwidth, style)
                            else:
                                if align == 1:
                                    posx += self.addchr(posy, posx, begx, self.scrsizex, self.datapadchar, cwidth-length, padstyle)
                                elif align == 0:
                                    pad1 = (cwidth-length)//2
                                    pad2 = cwidth-length-len(pad1)
                                    posx += self.addchr(posy, posx, begx, self.scrsizex, self.datapadchar, pad1, padstyle)
                                for (style, text) in parts:
                                    if i == level.cury:
                                        style = self.getstylehere(style)
                                    posx += self.addstr(posy, posx, begx, self.scrsizex, text, style)
                                    if posx >= self.scrsizex:
                                        break
                                if align == -1:
                                    posx += self.addchr(posy, posx, begx, self.scrsizex, self.datapadchar, cwidth-length, padstyle)
                                elif align == 0:
                                    posx += self.addchr(posy, posx, begx, self.scrsizex, self.datapadchar, pad2, padstyle)
                            posx += self.addstr(posy, posx, begx, self.scrsizex, self.datasepchar, sepstyle)
                        else:
                            scr.clrtoeol()

                    # Add blank row headers for the rest of the screen
                    for posy in xrange(posy+1, self.scrsizey-2):
                        scr.addstr(posy, 0, " " * (level.numbersizex+2), self.getstyle(self.style_colheader))
                        scr.clrtoeol()

                posy = self.scrsizey-footery
                # Display footer
                scr.addstr(posy, 0, " "*self.scrsizex, self.getstyle(self.style_footer))

                if level.exhausted:
                    flag = ""
                else:
                    flag = "+"

                endx = self.scrsizex-len(helpmsg)-1
                scr.addstr(posy, endx, helpmsg, self.getstyle(self.style_footer))

                posx = 0
                msg = " %d%s objects (%d marked): " % (len(level.items), flag, level.marked)
                posx += self.addstr(posy, posx, 0, endx, msg, self.style_footer)
                try:
                    item = level.items[level.cury].item
                except IndexError: # empty
                    pass
                else:
                    for (nostyle, text) in xrepr(item, "footer"):
                        if not isinstance(nostyle, int):
                            posx += self.addstr(posy, posx, 0, endx, text, self.style_footer)
                            if posx >= endx:
                                break

                    attrstyle = [(style_default, "no attribute")]
                    attrname = level.displayattr[1]
                    if attrname is not _default and attrname is not None:
                        posx += self.addstr(posy, posx, 0, endx, " | ", self.style_footer)
                        posx += self.addstr(posy, posx, 0, endx, _attrname(attrname), self.style_footer)
                        posx += self.addstr(posy, posx, 0, endx, ": ", self.style_footer)
                        try:
                            attr = _getattr(item, attrname)
                        except (SystemExit, KeyboardInterrupt):
                            raise
                        except Exception, exc:
                            attr = exc
                        if attr is not _default:
                            attrstyle = xrepr(attr, "footer")
                        for (nostyle, text) in attrstyle:
                            if not isinstance(nostyle, int):
                                posx += self.addstr(posy, posx, 0, endx, text, self.style_footer)
                                if posx >= endx:
                                    break

                try:
                    # Display input prompt
                    if self.mode in self.prompts:
                        scr.addstr(self.scrsizey-1, 0,
                                   self.prompts[self.mode] + self.keyboardinput,
                                   self.getstyle(style_default))
                    # Display report
                    else:
                        if self._report is not None:
                            if isinstance(self._report, Exception):
                                style = self.getstyle(style_error)
                                if self._report.__class__.__module__ == "exceptions":
                                    msg = "%s: %s" % \
                                          (self._report.__class__.__name__, self._report)
                                else:
                                    msg = "%s.%s: %s" % \
                                          (self._report.__class__.__module__,
                                           self._report.__class__.__name__, self._report)
                            else:
                                style = self.getstyle(self.style_report)
                                msg = self._report
                            scr.addstr(self.scrsizey-1, 0, msg[:self.scrsizex], style)
                            self._report = None
                        else:
                            scr.move(self.scrsizey-1, 0)
                except curses.error:
                    # Protect against error from writing to the last line
                    pass
                scr.clrtoeol()

                # Position cursor
                if self.mode in self.prompts:
                    scr.move(self.scrsizey-1, len(self.prompts[self.mode])+self.cursorpos)
                else:
                    scr.move(
                        1+self._headerlines+level.cury-level.datastarty,
                        level.numbersizex+3+level.curx-level.datastartx
                    )
                scr.refresh()

                # Check keyboard
                while True:
                    c = scr.getch()
                    if self.mode in self.prompts:
                        if c in (8, 127, curses.KEY_BACKSPACE):
                            if self.cursorpos:
                                self.keyboardinput = self.keyboardinput[:self.cursorpos-1] + self.keyboardinput[self.cursorpos:]
                                self.cursorpos -= 1
                                break
                            else:
                                curses.beep()
                        elif c == curses.KEY_LEFT:
                            if self.cursorpos:
                                self.cursorpos -= 1
                                break
                            else:
                                curses.beep()
                        elif c == curses.KEY_RIGHT:
                            if self.cursorpos < len(self.keyboardinput):
                                self.cursorpos += 1
                                break
                            else:
                                curses.beep()
                        elif c in (curses.KEY_UP, curses.KEY_DOWN): # cancel
                            self.mode = "default"
                            break
                        elif c == ord("\n"):
                            self.executekeyboardinput(self.mode)
                            break
                        elif c != -1:
                           try:
                               c = chr(c)
                           except ValueError:
                               curses.beep()
                           else:
                               if (self.mode == "goto" and not "0" <= c <= "9"):
                                   curses.beep()
                               else:
                                   self.keyboardinput = self.keyboardinput[:self.cursorpos] + c + self.keyboardinput[self.cursorpos:]
                                   self.cursorpos += 1
                                   break # Redisplay
                    else:
                        # if no key is pressed slow down and beep again
                        if c == -1:
                            self.stepx = 1.
                            self.stepy = 1.
                            self._dobeep = True
                        else:
                            # if a different key was pressed slow down and beep too
                            if c != lastc:
                                lastc = c
                                self.stepx = 1.
                                self.stepy = 1.
                                self._dobeep = True
                            cmdname = self.keymap.get(c, None)
                            if cmdname is None:
                                self.report(
                                    UnassignedKeyError("Unassigned key %s" %
                                                       self.keylabel(c)))
                            else:
                                cmdfunc = getattr(self, "cmd_%s" % cmdname, None)
                                if cmdfunc is None:
                                    self.report(
                                        UnknownCommandError("Unknown command %r" %
                                                            (cmdname,)))
                                elif cmdfunc():
                                    returnvalue = self.returnvalue
                                    self.returnvalue = None
                                    return returnvalue
                            self.stepx = self.nextstepx(self.stepx)
                            self.stepy = self.nextstepy(self.stepy)
                            curses.flushinp() # get rid of type ahead
                            break # Redisplay
            self.scr = None

        def display(self):
            return curses.wrapper(self._dodisplay)

    defaultdisplay = ibrowse
    __all__.append("ibrowse")
else:
    # No curses (probably Windows) => use ``idump`` as the default display.
    defaultdisplay = idump


# If we're running under IPython, install an IPython displayhook that
# returns the object from Display.display(), else install a displayhook
# directly as sys.displayhook
try:
    from IPython import ipapi
    api = ipapi.get()
except (ImportError, AttributeError):
    api = None

if api is not None:
    def displayhook(self, obj):
        if isinstance(obj, type) and issubclass(obj, Table):
            obj = obj()
        if isinstance(obj, Table):
            obj = obj | defaultdisplay
        if isinstance(obj, Display):
            return obj.display()
        else:
            raise ipapi.TryNext
    api.set_hook("result_display", displayhook)
else:
    def installdisplayhook():
        _originalhook = sys.displayhook
        def displayhook(obj):
            if isinstance(obj, type) and issubclass(obj, Table):
                obj = obj()
            if isinstance(obj, Table):
                obj = obj | defaultdisplay
            if isinstance(obj, Display):
                return obj.display()
            else:
                _originalhook(obj)
        sys.displayhook = displayhook
    installdisplayhook()
