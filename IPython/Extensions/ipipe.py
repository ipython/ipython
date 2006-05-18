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
  representation of the object; see the ``astyle`` module). If ``__xrepr__()``
  recursively outputs a data structure the function ``xrepr(object, mode)`` can
  be used and ``"default"`` must be passed as the mode in these calls. This in
  turn calls the ``__xrepr__()`` method on ``object`` (or uses ``repr(object)``
  as the string representation if ``__xrepr__()`` doesn't exist).

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

import path
try:
    from IPython import genutils, ipapi
except ImportError:
    genutils = None
    ipapi = None

import astyle


__all__ = [
    "ifile", "ils", "iglob", "iwalk", "ipwdentry", "ipwd", "igrpentry", "igrp",
    "icsv", "ix", "ichain", "isort", "ifilter", "ieval", "ienum", "ienv",
    "idump", "iless"
]


os.stat_float_times(True) # enable microseconds


class AttrNamespace(object):
    """
    Helper class that is used for providing a namespace for evaluating
    expressions containing attribute names of an object.
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
    eval("_", None, AttrNamespace(None))
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


noitem = object()

def item(iterator, index, default=noitem):
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
    if default is noitem:
        raise IndexError(index)
    else:
        return default


def getglobals(g):
    if g is None:
        if ipapi is not None:
            return ipapi.get().user_ns()
        else:
            return globals()
    return g


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


def _getattr(obj, name, default=noitem):
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
            yield (astyle.style_default, repr(item))
        return
    if item is None:
        yield (-1, True)
        yield (astyle.style_type_none, repr(item))
    elif isinstance(item, bool):
        yield (-1, True)
        yield (astyle.style_type_bool, repr(item))
    elif isinstance(item, str):
        yield (-1, True)
        if mode == "cell":
            yield (astyle.style_default, repr(item.expandtabs(tab))[1:-1])
        else:
            yield (astyle.style_default, repr(item))
    elif isinstance(item, unicode):
        yield (-1, True)
        if mode == "cell":
            yield (astyle.style_default, repr(item.expandtabs(tab))[2:-1])
        else:
            yield (astyle.style_default, repr(item))
    elif isinstance(item, (int, long, float)):
        yield (1, True)
        yield (astyle.style_type_number, repr(item))
    elif isinstance(item, complex):
        yield (-1, True)
        yield (astyle.style_type_number, repr(item))
    elif isinstance(item, datetime.datetime):
        yield (-1, True)
        if mode == "cell":
            # Don't use strftime() here, as this requires year >= 1900
            yield (astyle.style_type_datetime,
                   "%04d-%02d-%02d %02d:%02d:%02d.%06d" % \
                        (item.year, item.month, item.day,
                         item.hour, item.minute, item.second,
                         item.microsecond),
                    )
        else:
            yield (astyle.style_type_datetime, repr(item))
    elif isinstance(item, datetime.date):
        yield (-1, True)
        if mode == "cell":
            yield (astyle.style_type_datetime,
                   "%04d-%02d-%02d" % (item.year, item.month, item.day))
        else:
            yield (astyle.style_type_datetime, repr(item))
    elif isinstance(item, datetime.time):
        yield (-1, True)
        if mode == "cell":
            yield (astyle.style_type_datetime,
                    "%02d:%02d:%02d.%06d" % \
                        (item.hour, item.minute, item.second, item.microsecond))
        else:
            yield (astyle.style_type_datetime, repr(item))
    elif isinstance(item, datetime.timedelta):
        yield (-1, True)
        yield (astyle.style_type_datetime, repr(item))
    elif isinstance(item, Exception):
        yield (-1, True)
        if item.__class__.__module__ == "exceptions":
            classname = item.__class__.__name__
        else:
            classname = "%s.%s" % \
                (item.__class__.__module__, item.__class__.__name__)
        if mode == "header" or mode == "footer":
            yield (astyle.style_error, "%s: %s" % (classname, item))
        else:
            yield (astyle.style_error, classname)
    elif isinstance(item, (list, tuple)):
        yield (-1, False)
        if mode == "header" or mode == "footer":
            if item.__class__.__module__ == "__builtin__":
                classname = item.__class__.__name__
            else:
                classname = "%s.%s" % \
                    (item.__class__.__module__,item.__class__.__name__)
            yield (astyle.style_default,
                   "<%s object with %d items at 0x%x>" % \
                       (classname, len(item), id(item)))
        else:
            if isinstance(item, list):
                yield (astyle.style_default, "[")
                end = "]"
            else:
                yield (astyle.style_default, "(")
                end = ")"
            for (i, subitem) in enumerate(item):
                if i:
                    yield (astyle.style_default, ", ")
                for part in xrepr(subitem, "default"):
                    yield part
            yield (astyle.style_default, end)
    elif isinstance(item, (dict, types.DictProxyType)):
        yield (-1, False)
        if mode == "header" or mode == "footer":
            if item.__class__.__module__ == "__builtin__":
                classname = item.__class__.__name__
            else:
                classname = "%s.%s" % \
                    (item.__class__.__module__,item.__class__.__name__)
            yield (astyle.style_default,
                   "<%s object with %d items at 0x%x>" % \
                    (classname, len(item), id(item)))
        else:
            if isinstance(item, dict):
                yield (astyle.style_default, "{")
                end = "}"
            else:
                yield (astyle.style_default, "dictproxy((")
                end = "})"
            for (i, (key, value)) in enumerate(item.iteritems()):
                if i:
                    yield (astyle.style_default, ", ")
                for part in xrepr(key, "default"):
                    yield part
                yield (astyle.style_default, ": ")
                for part in xrepr(value, "default"):
                    yield part
            yield (astyle.style_default, end)
    else:
        yield (-1, True)
        yield (astyle.style_default, repr(item))


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
                    yield (astyle.style_default, "+")
                if isinstance(item, Pipe):
                    yield (astyle.style_default, "(")
                for part in xrepr(item, mode):
                    yield part
                if isinstance(item, Pipe):
                    yield (astyle.style_default, ")")
        else:
            yield (astyle.style_default, repr(self))

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
        return ifile(path.path.getcwd())
    getcwd.__doc__ = path.path.getcwd.__doc__
    getcwd = staticmethod(getcwd)

    def abspath(self):
        return ifile(path.path.abspath(self))
    abspath.__doc__ = path.path.abspath.__doc__

    def normcase(self):
        return ifile(path.path.normcase(self))
    normcase.__doc__ = path.path.normcase.__doc__

    def normpath(self):
        return ifile(path.path.normpath(self))
    normpath.__doc__ = path.path.normpath.__doc__

    def realpath(self):
        return ifile(path.path.realpath(self))
    realpath.__doc__ = path.path.realpath.__doc__

    def expanduser(self):
        return ifile(path.path.expanduser(self))
    expanduser.__doc__ = path.path.expanduser.__doc__

    def expandvars(self):
        return ifile(path.path.expandvars(self))
    expandvars.__doc__ = path.path.expandvars.__doc__

    def dirname(self):
        return ifile(path.path.dirname(self))
    dirname.__doc__ = path.path.dirname.__doc__

    parent = property(dirname, None, None, path.path.parent.__doc__)

    def splitpath(self):
        (parent, child) = path.path.splitpath(self)
        return (ifile(parent), child)
    splitpath.__doc__ = path.path.splitpath.__doc__

    def splitdrive(self):
        (drive, rel) = path.path.splitdrive(self)
        return (ifile(drive), rel)
    splitdrive.__doc__ = path.path.splitdrive.__doc__

    def splitext(self):
        (filename, ext) = path.path.splitext(self)
        return (ifile(filename), ext)
    splitext.__doc__ = path.path.splitext.__doc__

    if hasattr(path.path, "splitunc"):
        def splitunc(self):
            (unc, rest) = path.path.splitunc(self)
            return (ifile(unc), rest)
        splitunc.__doc__ = path.path.splitunc.__doc__

        def _get_uncshare(self):
            unc, r = os.path.splitunc(self)
            return ifile(unc)

        uncshare = property(
            _get_uncshare, None, None,
            """ The UNC mount point for this path.
            This is empty for paths on local drives. """)

    def joinpath(self, *args):
        return ifile(path.path.joinpath(self, *args))
    joinpath.__doc__ = path.path.joinpath.__doc__

    def splitall(self):
        return map(ifile, path.path.splitall(self))
    splitall.__doc__ = path.path.splitall.__doc__

    def relpath(self):
        return ifile(path.path.relpath(self))
    relpath.__doc__ = path.path.relpath.__doc__

    def relpathto(self, dest):
        return ifile(path.path.relpathto(self, dest))
    relpathto.__doc__ = path.path.relpathto.__doc__

    def listdir(self, pattern=None):
        return [ifile(child) for child in path.path.listdir(self, pattern)]
    listdir.__doc__ = path.path.listdir.__doc__

    def dirs(self, pattern=None):
        return [ifile(child) for child in path.path.dirs(self, pattern)]
    dirs.__doc__ = path.path.dirs.__doc__

    def files(self, pattern=None):
        return [ifile(child) for child in path.path.files(self, pattern)]
    files.__doc__ = path.path.files.__doc__

    def walk(self, pattern=None):
        for child in path.path.walk(self, pattern):
            yield ifile(child)
    walk.__doc__ = path.path.walk.__doc__

    def walkdirs(self, pattern=None):
        for child in path.path.walkdirs(self, pattern):
            yield ifile(child)
    walkdirs.__doc__ = path.path.walkdirs.__doc__

    def walkfiles(self, pattern=None):
        for child in path.path.walkfiles(self, pattern):
            yield ifile(child)
    walkfiles.__doc__ = path.path.walkfiles.__doc__

    def glob(self, pattern):
        return map(ifile, path.path.glob(self, pattern))
    glob.__doc__ = path.path.glob.__doc__

    if hasattr(os, 'readlink'):
        def readlink(self):
            return ifile(path.path.readlink(self))
        readlink.__doc__ = path.path.readlink.__doc__

        def readlinkabs(self):
            return ifile(path.path.readlinkabs(self))
        readlinkabs.__doc__ = path.path.readlinkabs.__doc__

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
                style = astyle.style_dir
            else:
                name = "ifile"
                style = astyle.style_file
        except IOError:
            name = "ifile"
            style = astyle.style_default
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
            yield (astyle.style_dir, os.pardir)
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
            yield (astyle.style_default,
                   "%s(%r)" % (self.__class__.__name__, self.glob))
        else:
            yield (astyle.style_default, repr(self))

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
            yield (astyle.style_default,
                   "%s(%r)" % (self.__class__.__name__, self.base))
        else:
            yield (astyle.style_default, repr(self))

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
            yield (astyle.style_default, "%s()" % self.__class__.__name__)
        else:
            yield (astyle.style_default, repr(self))


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
            yield (astyle.style_default, "group ")
            try:
                yield (astyle.style_default, self.name)
            except KeyError:
                if isinstance(self._id, basestring):
                    yield (astyle.style_default, self.name_id)
                else:
                    yield (astyle.style_type_number, str(self._id))
        else:
            yield (astyle.style_default, repr(self))

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
            yield (astyle.style_default, "%s()" % self.__class__.__name__)
        else:
            yield (astyle.style_default, repr(self))


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
            yield (astyle.style_default, self.__class__.__name__)
            yield (astyle.style_default, "(")
            for (i, f) in enumerate(self.__fieldnames):
                if i:
                    yield (astyle.style_default, ", ")
                yield (astyle.style_default, f)
                yield (astyle.style_default, "=")
                for part in xrepr(getattr(self, f), "default"):
                    yield part
            yield (astyle.style_default, ")")
        elif mode == "footer":
            yield (astyle.style_default, self.__class__.__name__)
            yield (astyle.style_default, "(")
            for (i, f) in enumerate(self.__fieldnames):
                if i:
                    yield (astyle.style_default, ", ")
                yield (astyle.style_default, f)
            yield (astyle.style_default, ")")
        else:
            yield (astyle.style_default, repr(self))


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
            yield (astyle.style_default, self.__class__.__name__)
            yield (astyle.style_default, "(")
            for (i, f) in enumerate(self.__fieldnames):
                if i:
                    yield (astyle.style_default, ", ")
                yield (astyle.style_default, f)
            yield (astyle.style_default, ")")
        else:
            yield (astyle.style_default, repr(self))

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
            yield (astyle.style_default, self.__class__.__name__)
            yield (astyle.style_default, "(")
            for (i, item) in enumerate(self):
                if i:
                    yield (astyle.style_default, ", ")
                for part in xrepr(item, "default"):
                    yield part
            yield (astyle.style_default, ")")
        else:
            yield (astyle.style_default, repr(self))


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
            yield (astyle.style_default, "%s()" % self.__class__.__name__)
        else:
            yield (astyle.style_default, repr(self))


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
                yield (astyle.style_default, " | ")
            yield (astyle.style_default, "%s(" % self.__class__.__name__)
            for (i, (name, value)) in enumerate(self.csvargs.iteritems()):
                if i:
                    yield (astyle.style_default, ", ")
                yield (astyle.style_default, name)
                yield (astyle.style_default, "=")
                for part in xrepr(value, "default"):
                    yield part
            yield (astyle.style_default, ")")
        else:
            yield (astyle.style_default, repr(self))

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
            yield (astyle.style_default,
                   "%s(%r)" % (self.__class__.__name__, self.cmd))
        else:
            yield (astyle.style_default, repr(self))

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

    def __init__(self, expr, globals=None, errors="raiseifallfail"):
        """
        Create an ``ifilter`` object. ``expr`` can be a callable or a string
        containing an expression. ``globals`` will be used as the global
        namespace for calling string expressions (defaulting to IPython's
        user namespace). ``errors`` specifies how exception during evaluation
        of ``expr`` are handled:

        * ``drop``: drop all items that have errors;

        * ``keep``: keep all items that have errors;

        * ``keeperror``: keep the exception of all items that have errors;

        * ``raise``: raise the exception;

        * ``raiseifallfail``: raise the first exception if all items have errors;
          otherwise drop those with errors (this is the default).
        """
        self.expr = expr
        self.globals = globals
        self.errors = errors

    def __xiter__(self, mode):
        if callable(self.expr):
            def test(item):
                return self.expr(item)
        else:
            g = getglobals(self.globals)
            def test(item):
                return eval(self.expr, g, AttrNamespace(item))

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
                yield (astyle.style_default, " | ")
            yield (astyle.style_default, "%s(" % self.__class__.__name__)
            for part in xrepr(self.expr, "default"):
                yield part
            yield (astyle.style_default, ")")
        else:
            yield (astyle.style_default, repr(self))

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

    def __init__(self, expr, globals=None, errors="raiseifallfail"):
        """
        Create an ``ieval`` object. ``expr`` can be a callable or a string
        containing an expression. For the meaning of ``globals`` and
        ``errors`` see ``ifilter``.
        """
        self.expr = expr
        self.globals = globals
        self.errors = errors

    def __xiter__(self, mode):
        if callable(self.expr):
            def do(item):
                return self.expr(item)
        else:
            g = getglobals(self.globals)
            def do(item):
                return eval(self.expr, g, AttrNamespace(item))

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
                yield (astyle.style_default, " | ")
            yield (astyle.style_default, "%s(" % self.__class__.__name__)
            for part in xrepr(self.expr, "default"):
                yield part
            yield (astyle.style_default, ")")
        else:
            yield (astyle.style_default, repr(self))

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

    def __init__(self, key, globals=None, reverse=False):
        """
        Create an ``isort`` object. ``key`` can be a callable or a string
        containing an expression. If ``reverse`` is true the sort order will
        be reversed. For the meaning of ``globals`` see ``ifilter``.
        """
        self.key = key
        self.globals = globals
        self.reverse = reverse

    def __xiter__(self, mode):
        if callable(self.key):
            items = sorted(
                xiter(self.input, mode),
                key=self.key,
                reverse=self.reverse
            )
        else:
            g = getglobals(self.globals)
            def key(item):
                return eval(self.key, g, AttrNamespace(item))
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
                yield (astyle.style_default, " | ")
            yield (astyle.style_default, "%s(" % self.__class__.__name__)
            for part in xrepr(self.key, "default"):
                yield part
            if self.reverse:
                yield (astyle.style_default, ", ")
                for part in xrepr(True, "default"):
                    yield part
            yield (astyle.style_default, ")")
        else:
            yield (astyle.style_default, repr(self))

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
    text = astyle.Text()
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
                text.append((astyle.style_ellisis, "..."))
                width += 3
                break
    if align is None: # default to left alignment
        align = -1
    return (align, width, text)


class idump(Display):
    # The approximate maximum length of a column entry
    maxattrlength = 200

    # Style for column names
    style_header = astyle.Style.fromstr("white:black:bold")

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
            yield (astyle.style_default, self.title)
        else:
            yield (astyle.style_default, repr(self))

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


try:
    from ibrowse import ibrowse
except ImportError:
    # No curses (probably Windows) => use ``idump`` as the default display.
    defaultdisplay = idump
else:
    defaultdisplay = ibrowse
    __all__.append("ibrowse")


# If we're running under IPython, install an IPython displayhook that
# returns the object from Display.display(), else install a displayhook
# directly as sys.displayhook
api = None
if ipapi is not None:
    try:
        api = ipapi.get()
    except AttributeError:
        pass

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
