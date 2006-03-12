# -*- coding: iso-8859-1 -*-

"""
``ipipe`` provides classes to be used in an interactive Python session. Doing a
``from ipipe import *`` is the preferred way to do this. The name of all
objects imported this way starts with ``i`` to minimize collisions.

``ipipe`` supports "pipeline expressions", which is something resembling Unix
pipes. An example is:

    >>> ienv | isort("_.key.lower()")

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

* When an object ``foo`` is displayed in the header (or footer) of the browser
  ``foo.__xrepr__("header")`` (or ``foo.__xrepr__("footer")``) is called.
  Currently only ``"header"`` and ``"footer"`` are used as the mode argument.
  When the method doesn't recognize the mode argument, it should fall back to
  the ``repr()`` output. If the method ``__xrepr__()`` isn't defined the browser
  falls back to ``repr()``. The global function ``xrepr()`` implements this
  functionality.

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
      >>> sys | ifilter("isinstance(_.value, int)") | idump
      key        |value
      api_version|      1012
      dllhandle  | 503316480
      hexversion |  33817328
      maxint     |2147483647
      maxunicode |     65535
      >>> sys.modules | ifilter("_.value is not None") | isort("_.key.lower()")
      ...

  Note: The expression strings passed to ``ifilter()`` and ``isort()`` can
  refer to the object to be filtered or sorted via the variable ``_``. When
  running under Python 2.4 it's also possible to refer to the attributes of
  the object directy, i.e.:

      >>> sys.modules | ifilter("_.value is not None") | isort("_.key.lower()")

  can be replaced with

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

import sys, os, os.path, stat, glob, new, csv, datetime
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

    This class can only be used with Python 2.4.
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
# fall back to a real dictionary (containing just the object itself) if we can't
# use the _AttrNamespace class in eval()
try:
    eval("_", None, _AttrNamespace(None))
except TypeError:
    def _AttrNamespace(wrapped):
        return {"_": wrapped}


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
        return getattr(obj, name, default)
    elif callable(name):
        return name(obj)
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
        return name.__name__
    else:
        return str(name)


def xrepr(item, mode):
    try:
        func = item.__xrepr__
    except AttributeError:
        return repr(item)
    else:
        return func(mode)


def xattrs(item, mode):
    try:
        func = item.__xattrs__
    except AttributeError:
        if isinstance(item, (list, tuple)):
            return xrange(len(item))
        return (None,)
    else:
        return func(mode)


def xiter(item, mode):
    if mode == "detail":
        def items():
            for name in xattrs(item, mode):
                yield XAttr(item, name)
        return items()
    try:
        func = item.__xiter__
    except AttributeError:
        if isinstance(item, dict):
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
        if mode == "header" or mode == "footer":
            parts = []
            for item in self.iters:
                part = xrepr(item, mode)
                if isinstance(item, Pipe):
                    part = "(%s)" % part
                parts.append(part)
            return "+".join(parts)
        return repr(self)

    def __repr__(self):
        args = ", ".join([repr(it) for it in self.iters])
        return "%s.%s(%s)" % \
            (self.__class__.__module__, self.__class__.__name__, args)


class ifile(object):
    """
    file (or directory) object.
    """
    __slots__ = ("name", "_abspath", "_realpath", "_stat", "_lstat")

    def __init__(self, name):
        if isinstance(name, ifile): # copying files
            self.name = name.name
            self._abspath = name._abspath
            self._realpath = name._realpath
            self._stat = name._stat
            self._lstat = name._lstat
        else:
            self.name = os.path.normpath(name)
            self._abspath = None
            self._realpath = None
            self._stat = None
            self._lstat = None

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self.name)

    def open(self, mode="rb", buffer=None):
        if buffer is None:
            return open(self.abspath, mode)
        else:
            return open(self.abspath, mode, buffer)

    def remove(self):
        os.remove(self.abspath)

    def getabspath(self):
        if self._abspath is None:
            self._abspath = os.path.abspath(self.name)
        return self._abspath
    abspath = property(getabspath, None, None, "Path to file")

    def getrealpath(self):
        if self._realpath is None:
            self._realpath = os.path.realpath(self.name)
        return self._realpath
    realpath = property(getrealpath, None, None, "Path with links resolved")

    def getbasename(self):
        return os.path.basename(self.abspath)
    basename = property(getbasename, None, None, "File name without directory")

    def getstat(self):
        if self._stat is None:
            self._stat = os.stat(self.abspath)
        return self._stat
    stat = property(getstat, None, None, "os.stat() result")

    def getlstat(self):
        if self._lstat is None:
            self._lstat = os.lstat(self.abspath)
        return self._lstat
    lstat = property(getlstat, None, None, "os.lstat() result")

    def getmode(self):
        return self.stat.st_mode
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
        lstat = self.lstat
        if lstat is not None:
            types = set([text for (func, text) in data if func(lstat.st_mode)])
        else:
            types = set()
        m = self.mode
        types.update([text for (func, text) in data if func(m)])
        return ", ".join(types)
    type = property(gettype, None, None, "file type")

    def getaccess(self):
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

    access = property(getaccess, None, None, "Access mode as string")

    def getsize(self):
        return int(self.stat.st_size)
    size = property(getsize, None, None, "File size in bytes")

    def getblocks(self):
        return self.stat.st_blocks
    blocks = property(getblocks, None, None, "File size in blocks")

    def getblksize(self):
        return self.stat.st_blksize
    blksize = property(getblksize, None, None, "Filesystem block size")

    def getdev(self):
        return self.stat.st_dev
    dev = property(getdev)

    def getnlink(self):
        return self.stat.st_nlink
    nlink = property(getnlink, None, None, "Number of links")

    def getuid(self):
        return self.stat.st_uid
    uid = property(getuid, None, None, "User id of file owner")

    def getgid(self):
        return self.stat.st_gid
    gid = property(getgid, None, None, "Group id of file owner")

    def getowner(self):
        try:
            return pwd.getpwuid(self.stat.st_uid).pw_name
        except KeyError:
            return self.stat.st_uid
    owner = property(getowner, None, None, "Owner name (or id)")

    def getgroup(self):
        try:
            return grp.getgrgid(self.stat.st_gid).gr_name
        except KeyError:
            return self.stat.st_gid
    group = property(getgroup, None, None, "Group name (or id)")

    def getatime(self):
        return self.stat.st_atime
    atime = property(getatime, None, None, "Access date")

    def getadate(self):
        return datetime.datetime.utcfromtimestamp(self.atime)
    adate = property(getadate, None, None, "Access date")

    def getctime(self):
        return self.stat.st_ctime
    ctime = property(getctime, None, None, "Creation date")

    def getcdate(self):
        return datetime.datetime.utcfromtimestamp(self.ctime)
    cdate = property(getcdate, None, None, "Creation date")

    def getmtime(self):
        return self.stat.st_mtime
    mtime = property(getmtime, None, None, "Modification date")

    def getmdate(self):
        return datetime.datetime.utcfromtimestamp(self.mtime)
    mdate = property(getmdate, None, None, "Modification date")

    def getmimetype(self):
        return mimetypes.guess_type(self.basename)[0]
    mimetype = property(getmimetype, None, None, "MIME type")

    def getencoding(self):
        return mimetypes.guess_type(self.basename)[1]
    encoding = property(getencoding, None, None, "Compression")

    def getisdir(self):
        return os.path.isdir(self.abspath)
    isdir = property(getisdir, None, None, "Is this a directory?")

    def getislink(self):
        return os.path.islink(self.abspath)
    islink = property(getislink, None, None, "Is this a link?")

    def __eq__(self, other):
        return self.abspath == other.abspath

    def __neq__(self, other):
        return self.abspath != other.abspath

    def __xattrs__(self, mode):
        if mode == "detail":
            return (
                "name", "basename", "abspath", "realpath",
                "mode", "type", "access", "stat", "lstat",
                "uid", "gid", "owner", "group", "dev", "nlink",
                "ctime", "mtime", "atime", "cdate", "mdate", "adate",
                "size", "blocks", "blksize", "isdir", "islink",
                "mimetype", "encoding"
            )
        return ("name", "type", "size", "access", "owner", "group", "mdate")

    def __xrepr__(self, mode):
        if mode == "header" or mode == "footer":
            name = "ifile"
            try:
                if self.isdir:
                    name = "idir"
            except IOError:
                pass
            return "%s(%r)" % (name, self.abspath)
        return repr(self)

    def __xiter__(self, mode):
        if self.isdir:
            abspath = self.abspath
            if abspath != os.path.abspath(os.path.join(abspath, os.pardir)):
                yield iparentdir(abspath)
            for name in sorted(os.listdir(abspath), key=lambda n: n.lower()):
                if self.name != os.curdir:
                    name = os.path.join(abspath, name)
                yield ifile(name)
        else:
            f = self.open("rb")
            for line in f:
                yield line
            f.close()

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self.abspath)


class iparentdir(ifile):
    def __init__(self, base):
        self._base = base
        self.name = os.pardir
        self._abspath = None
        self._realpath = None
        self._stat = None
        self._lstat = None

    def getabspath(self):
        if self._abspath is None:
            self._abspath = os.path.abspath(os.path.join(self._base, self.name))
        return self._abspath
    abspath = property(getabspath, None, None, "Path to file")

    def getrealpath(self):
        if self._realpath is None:
            self._realpath = os.path.realpath(
                os.path.join(self._base, self.name))
        return self._realpath
    realpath = property(getrealpath, None, None, "Path with links resolved")


class ils(Table):
    """
    This ``Table`` lists a directory.
    """
    def __init__(self, base=os.curdir):
        self.base = os.path.expanduser(base)

    def __xiter__(self, mode):
        return xiter(ifile(self.base), mode)

    def __xrepr__(self, mode):
        if mode == "header" or mode == "footer":
            return "idir(%r)" % (os.path.abspath(self.base))
        return repr(self)

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self.base)


class iglob(Table):
    """
    This `Table`` lists all files and directories matching a specified pattern.
    (See ``glob.glob()`` for more info.)
    """
    def __init__(self, glob):
        self.glob = glob

    def __xiter__(self, mode):
        for name in glob.glob(self.glob):
            yield ifile(name)

    def __xrepr__(self, mode):
        if mode == "header" or mode == "footer":
            return "%s(%r)" % (self.__class__.__name__, self.glob)
        return repr(self)

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self.glob)


class iwalk(Table):
    """
    This `Table`` lists all files and directories in a directory and it's
    subdirectory.
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
        if mode == "header" or mode == "footer":
            return "%s(%r)" % (self.__class__.__name__, self.base)
        return repr(self)

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
    This ``Table`` lists all entries in the Unix user account and password
    database.
    """
    def __iter__(self):
        for entry in pwd.getpwall():
            yield ipwdentry(entry.pw_name)

    def __xrepr__(self, mode):
        if mode == "header" or mode == "footer":
            return "%s()" % self.__class__.__name__
        return repr(self)


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
        if mode == "header" or mode == "footer":
            return "group %s" % self.name
        return repr(self)

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
        if mode == "header" or mode == "footer":
            return "%s()" % self.__class__.__name__
        return repr(self)


class Fields(object):
    def __init__(self, fieldnames, **fields):
        self.__fieldnames = fieldnames
        for (key, value) in fields.iteritems():
            setattr(self, key, value)

    def __xattrs__(self, mode):
        return self.__fieldnames

    def __xrepr__(self, mode):
        if mode == "header" or mode == "footer":
            args = ["%s=%r" % (f, getattr(self, f)) for f in self.__fieldnames]
            return "%s(%r)" % (self.__class__.__name__, ", ".join(args))
        return repr(self)


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
        if mode == "header" or mode == "footer":
            return "FieldTable(%r)" % ", ".join(map(repr, self.fields))
        return repr(self)

    def __repr__(self):
        return "<%s.%s object with fields=%r at 0x%x>" % \
            (self.__class__.__module__, self.__class__.__name__,
             ", ".join(map(repr, self.fields)), id(self))


class ienv(Table):
    """
    This ``Table`` lists environment variables.
    """

    def __xiter__(self, mode):
        fields = ("key", "value")
        for (key, value) in os.environ.iteritems():
            yield Fields(fields, key=key, value=value)

    def __xrepr__(self, mode):
        if mode == "header" or mode == "footer":
            return "%s()" % self.__class__.__name__
        return repr(self)


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
            yield line

    def __xrepr__(self, mode):
        if mode == "header" or mode == "footer":
            input = getattr(self, "input", None)
            if input is not None:
                prefix = "%s | " % xrepr(input, mode)
            else:
                prefix = ""
            args = ", ".join(["%s=%r" % item for item in self.csvargs.iteritems()])
            return "%s%s(%s)" % (prefix, self.__class__.__name__, args)
        return repr(self)

    def __repr__(self):
        args = ", ".join(["%s=%r" % item for item in self.csvargs.iteritems()])
        return "<%s.%s %s at 0x%x>" % \
        (self.__class__.__module__, self.__class__.__name__, args, id(self))


class ix(Table):
    """
    This ``Table`` executes a system command and lists its output as lines
    (similar to ``os.popen()``).
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
        if mode == "header" or mode == "footer":
            return "%s(%r)" % (self.__class__.__name__, self.cmd)
        return repr(self)

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self.cmd)


class ifilter(Pipe):
    """
    This ``Pipe`` filters an input pipe. Only objects where an expression
    evaluates to true (and doesn't raise an exception) are listed.
    """

    def __init__(self, expr):
        """
        Create an ``ifilter`` object. ``expr`` can be a callable or a string
        containing an expression.
        """
        self.expr = expr

    def __xiter__(self, mode):
        if callable(self.expr):
            for item in xiter(self.input, mode):
                try:
                    if self.expr(item):
                        yield item
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception:
                    pass # Ignore errors
        else:
            for item in xiter(self.input, mode):
                try:
                    if eval(self.expr, globals(), _AttrNamespace(item)):
                        yield item
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception:
                    pass # Ignore errors

    def __xrepr__(self, mode):
        if mode == "header" or mode == "footer":
            input = getattr(self, "input", None)
            if input is not None:
                prefix = "%s | " % xrepr(input, mode)
            else:
                prefix = ""
            return "%s%s(%s)"% \
                (prefix, self.__class__.__name__, xrepr(self.expr, mode))
        return repr(self)

    def __repr__(self):
        return "<%s.%s expr=%r at 0x%x>" % \
            (self.__class__.__module__, self.__class__.__name__,
             self.expr, id(self))


class ieval(Pipe):
    """
    This ``Pipe`` evaluates an expression for each object in the input pipe.
    """

    def __init__(self, expr):
        """
        Create an ``ieval`` object. ``expr`` can be a callable or a string
        containing an expression.
        """
        self.expr = expr

    def __xiter__(self, mode):
        if callable(self.expr):
            for item in xiter(self.input, mode):
                try:
                    yield self.expr(item)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception:
                    pass # Ignore errors
        else:
            for item in xiter(self.input, mode):
                try:
                    yield eval(self.expr, globals(), _AttrNamespace(item))
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception:
                    pass # Ignore errors

    def __xrepr__(self, mode):
        if mode == "header" or mode == "footer":
            input = getattr(self, "input", None)
            if input is not None:
                prefix = "%s | " % xrepr(input, mode)
            else:
                prefix = ""
            return "%s%s(%s)" % \
                (prefix, self.__class__.__name__, xrepr(self.expr, mode))
        return repr(self)

    def __repr__(self):
        return "<%s.%s expr=%r at 0x%x>" % \
            (self.__class__.__module__, self.__class__.__name__,
             self.expr, id(self))


class ienum(Pipe):
    def __xiter__(self, mode):
        fields = ("index", "object")
        for (index, object) in enumerate(xiter(self.input, mode)):
            yield Fields(fields, index=index, object=object)


class isort(Pipe):
    """
    This ``Pipe`` sorts its input pipe.
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
        if mode == "header" or mode == "footer":
            input = getattr(self, "input", None)
            if input is not None:
                prefix = "%s | " % xrepr(input, mode)
            else:
                prefix = ""
            if self.reverse:
                return "%s%s(%r, %r)" % \
                    (prefix, self.__class__.__name__, self.key, self.reverse)
            else:
                return "%s%s(%r)" % (prefix, self.__class__.__name__, self.key)
        return repr(self)

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


class idump(Display):
    def __init__(self, *attrs):
        self.attrs = attrs
        self.headerpadchar = " "
        self.headersepchar = "|"
        self.datapadchar = " "
        self.datasepchar = "|"

    def display(self):
        stream = sys.stdout
        if self.attrs:
            rows = []
            colwidths = dict([(a, len(_attrname(a))) for a in self.attrs])

            for item in xiter(self.input, "default"):
                row = {}
                for attrname in self.attrs:
                    value = _getattr(item, attrname, None)
                    text = _format(value)
                    colwidths[attrname] = max(colwidths[attrname], width)
                    row[attrname] = (value, text)
                rows.append(row)

            stream.write("\n")
            for (i, attrname) in enumerate(self.attrs):
                stream.write(_attrname(attrname))
                spc = colwidths[attrname] - len(_attrname(attrname))
                if i < len(colwidths)-1:
                    if spc>0:
                        stream.write(self.headerpadchar * spc)
                    stream.write(self.headersepchar)
            stream.write("\n")

            for row in rows:
                for (i, attrname) in enumerate(self.attrs):
                    (value, text) = row[attrname]
                    spc = colwidths[attrname] - len(text)
                    if isinstance(value, (int, long)):
                        if spc>0:
                            stream.write(self.datapadchar*spc)
                        stream.write(text)
                    else:
                        stream.write(text)
                        if i < len(colwidths)-1:
                            if spc>0:
                                stream.write(self.datapadchar*spc)
                    if i < len(colwidths)-1:
                        stream.write(self.datasepchar)
                stream.write("\n")
        else:
            allattrs = []
            allattrset = set()
            colwidths = {}
            rows = []
            for item in xiter(self.input, "default"):
                row = {}
                attrs = xattrs(item, "default")
                for attrname in attrs:
                    if attrname not in allattrset:
                        allattrs.append(attrname)
                        allattrset.add(attrname)
                        colwidths[attrname] = len(_attrname(attrname))
                    value = _getattr(item, attrname, None)
                    text = _format(value)
                    colwidths[attrname] = max(colwidths[attrname], len(text))
                    row[attrname] = (value, text)
                rows.append(row)

            for (i, attrname) in enumerate(allattrs):
                stream.write(_attrname(attrname))
                spc = colwidths[attrname] - len(_attrname(attrname))
                if i < len(colwidths)-1:
                    if spc>0:
                        stream.write(self.headerpadchar*spc)
                    stream.write(self.headersepchar)
            stream.write("\n")

            for row in rows:
                for (i, attrname) in enumerate(attrs):
                    (value, text) = row.get(attrname, ("", ""))
                    spc = colwidths[attrname] - len(text)
                    if isinstance(value, (int, long)):
                        if spc>0:
                            stream.write(self.datapadchar*spc)
                        stream.write(text)
                    else:
                        stream.write(text)
                        if i < len(colwidths)-1:
                            if spc>0:
                                stream.write(self.datapadchar*spc)
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
        if mode == "header" or mode == "footer":
            return self.title
        return repr(self)

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
            try:
                meta = getattr(type(object), name)
            except AttributeError:
                pass
            else:
                if isinstance(meta, property):
                    self.doc = getattr(meta, "__doc__", None)
        elif callable(name):
            try:
                self.doc = name.__doc__
            except AttributeError:
                pass

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
'Pick' the object under the cursor (i.e. the row the cursor is on). This leaves
the browser and returns the picked object to the caller. (In IPython this object
will be available as the '_' variable.)

pickattr
'Pick' the attribute under the cursor (i.e. the row/column the cursor is on).

pickallattrs
Pick' the complete column under the cursor (i.e. the attribute under the cursor)
from all currently fetched objects. These attributes will be returned as a list.

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
itself (i.e. how it implements the '__xiter__' method). This opens a new browser
'level'.

enter
Enter the object under the cursor. If the object provides different enter modes
a menu of all modes will be presented; choice one and enter it (via the 'enter'
or 'enterdefault' command).

enterattr
Enter the attribute under the cursor.

leave
Leave the current browser level and go back to the previous one.

detail
Show a detail view of the object under the cursor. This shows the name, type,
doc string and value of the object attributes (and it might show more attributes
than in the list view, depending on the object).

detailattr
Show a detail view of the attribute under the cursor.

markrange
Mark all objects from the last marked object before the current cursor position
to the cursor position.

sortattrasc
Sort the objects (in ascending order) using the attribute under the cursor as
the sort key.

sortattrdesc
Sort the objects (in descending order) using the attribute under the cursor as
the sort key.

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


    class Style(object):
        """
        Store foreground color, background color and attribute (bold, underlined
        etc.) for ``curses``.
        """
        __slots__ = ("fg", "bg", "attrs")

        def __init__(self, fg, bg, attrs=0):
            self.fg = fg
            self.bg = bg
            self.attrs = attrs


    class _BrowserCachedItem(object):
        # This is used internally by ``ibrowse`` to store a item together with its
        # marked status.
        __slots__ = ("item", "marked")

        def __init__(self, item):
            self.item = item
            self.marked = False


    class _BrowserHelp(object):
        # This is used internally by ``ibrowse`` for displaying the help screen.
        def __init__(self, browser):
            self.browser = browser

        def __xrepr__(self, mode):
            if mode == "header" or mode == "footer":
                return "ibrowse help screen"
            return repr(self)

        def __xiter__(self, mode):
            # Get reverse key mapping
            allkeys = {}
            for (key, cmd) in self.browser.keymap.iteritems():
                allkeys.setdefault(cmd, []).append(key)

            fields = ("key", "command", "description")

            for (i, command) in enumerate(_ibrowse_help.strip().split("\n\n")):
                if i:
                    yield Fields(fields, key="", command="", description="")

                (name, description) = command.split("\n", 1)
                keys = allkeys.get(name, [])
                lines = textwrap.wrap(description, 50)

                for i in xrange(max(len(keys), len(lines))):
                    if i:
                        name = ""
                    try:
                        key = self.browser.keylabel(keys[i])
                    except IndexError:
                        key = ""
                    try:
                        line = lines[i]
                    except IndexError:
                        line = ""
                    yield Fields(fields, key=key, command=name, description=line)


    class _BrowserLevel(object):
        # This is used internally to store the state (iterator, fetch items,
        # position of cursor and screen, etc.) of one browser level
        # An ``ibrowse`` object keeps multiple ``_BrowserLevel`` objects in
        # a stack.
        def __init__(self, browser, input, iterator, mainsizey, *attrs):
            self.browser = browser
            self.input = input
            self.header = xrepr(input, "header")
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
                    row[attrname] = self.browser.format(exc)
                else:
                    # only store attribute if it exists
                    if value is not _default:
                        row[attrname] = self.browser.format(value)
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
                    (align, text, style) = row.get(attrname, (2, "", None))
                    # always add attribute to colwidths, even if it doesn't exist
                    if attrname not in self.colwidths:
                        self.colwidths[attrname] = len(_attrname(attrname))
                    newwidth = max(self.colwidths[attrname], len(text))
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

        # Styles for various parts of the GUI
        style_objheadertext = Style(curses.COLOR_WHITE, curses.COLOR_BLACK, curses.A_BOLD|curses.A_REVERSE)
        style_objheadernumber = Style(curses.COLOR_WHITE, curses.COLOR_BLUE, curses.A_BOLD|curses.A_REVERSE)
        style_objheaderobject = Style(curses.COLOR_WHITE, curses.COLOR_BLACK, curses.A_REVERSE)
        style_colheader = Style(curses.COLOR_BLUE, curses.COLOR_WHITE, curses.A_REVERSE)
        style_colheaderhere = Style(curses.COLOR_GREEN, curses.COLOR_BLACK, curses.A_BOLD|curses.A_REVERSE)
        style_colheadersep = Style(curses.COLOR_BLUE, curses.COLOR_BLACK, curses.A_REVERSE)
        style_number = Style(curses.COLOR_BLUE, curses.COLOR_WHITE, curses.A_REVERSE)
        style_numberhere = Style(curses.COLOR_GREEN, curses.COLOR_BLACK, curses.A_BOLD|curses.A_REVERSE)
        style_sep = Style(curses.COLOR_BLUE, curses.COLOR_BLACK)
        style_data = Style(curses.COLOR_WHITE, curses.COLOR_BLACK)
        style_datapad = Style(curses.COLOR_BLUE, curses.COLOR_BLACK, curses.A_BOLD)
        style_footer = Style(curses.COLOR_BLACK, curses.COLOR_WHITE)
        style_noattr = Style(curses.COLOR_RED, curses.COLOR_BLACK)
        style_error = Style(curses.COLOR_RED, curses.COLOR_BLACK)
        style_default = Style(curses.COLOR_WHITE, curses.COLOR_BLACK)
        style_report = Style(curses.COLOR_WHITE, curses.COLOR_BLACK)

        # Styles for datatypes
        style_type_none = Style(curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        style_type_bool = Style(curses.COLOR_GREEN, curses.COLOR_BLACK)
        style_type_number = Style(curses.COLOR_YELLOW, curses.COLOR_BLACK)
        style_type_datetime = Style(curses.COLOR_CYAN, curses.COLOR_BLACK)

        # Column separator in header
        headersepchar = "|"

        # Character for padding data cell entries
        datapadchar = "."

        # Column separator in data area
        datasepchar = "|"

        # Character to use for "empty" cell (i.e. for non-existing attributes)
        nodatachar = "-"

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
            ord(">"): "nextattr",
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

            # Cache for registered ``curses`` colors.
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
                return self._colors[style.fg, style.bg] | style.attrs
            except KeyError:
                curses.init_pair(self._maxcolor, style.fg, style.bg)
                pair = curses.color_pair(self._maxcolor)
                self._colors[style.fg, style.bg] = pair
                c = pair | style.attrs
                self._maxcolor += 1
                return c

        def addstr(self, y, x, begx, endx, s, style):
            """
            A version of ``curses.addstr()`` that can handle ``x`` coordinates
            that are outside the screen.
            """
            s2 = s[max(0, begx-x):max(0, endx-x)]
            if s2:
                self.scr.addstr(y, max(x, begx), s2, self.getstyle(style))
            return len(s)

        def format(self, value):
            """
            Formats one attribute and returns an ``(alignment, string, style)``
            tuple.
            """
            if value is None:
                return (-1, repr(value), self.style_type_none)
            elif isinstance(value, str):
                return (-1, repr(value.expandtabs(tab))[1:-1], self.style_default)
            elif isinstance(value, unicode):
                return (-1, repr(value.expandtabs(tab))[2:-1], self.style_default)
            elif isinstance(value, datetime.datetime):
                # Don't use strftime() here, as this requires year >= 1900
                return (-1, "%04d-%02d-%02d %02d:%02d:%02d.%06d" % \
                            (value.year, value.month, value.day,
                             value.hour, value.minute, value.second,
                             value.microsecond),
                        self.style_type_datetime)
            elif isinstance(value, datetime.date):
                return (-1, "%04d-%02d-%02d" % \
                            (value.year, value.month, value.day),
                        self.style_type_datetime)
            elif isinstance(value, datetime.time):
                return (-1, "%02d:%02d:%02d.%06d" % \
                            (value.hour, value.minute, value.second,
                             value.microsecond),
                        self.style_type_datetime)
            elif isinstance(value, datetime.timedelta):
                return (-1, repr(value), self.style_type_datetime)
            elif isinstance(value, bool):
                return (-1, repr(value), self.style_type_bool)
            elif isinstance(value, (int, long, float)):
                return (1, repr(value), self.style_type_number)
            elif isinstance(value, complex):
                return (-1, repr(value), self.style_type_number)
            elif isinstance(value, Exception):
                if value.__class__.__module__ == "exceptions":
                    value = "%s: %s" % (value.__class__.__name__, value)
                else:
                    value = "%s.%s: %s" % \
                        (value.__class__.__module__, value.__class__.__name__,
                         value)
                return (-1, value, self.style_error)
            return (-1, repr(value), self.style_default)

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
            return Style(style.fg, style.bg, style.attrs | curses.A_BOLD)

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
            self.report("entering object (default mode)...")
            self.enter(level.items[level.cury].item, "default")

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
            self.report("entering object...")
            self.enter(level.items[level.cury].item, None)

        def cmd_enterattr(self):
            level = self.levels[-1]
            attrname = level.displayattr[1]
            if attrname is _default:
                curses.beep()
                self.report(AttributeError(_attrname(attrname)))
                return
            attr = _getattr(level.items[level.cury].item, attrname)
            if attr is _default:
                self.report(AttributeError(_attrname(attrname)))
            else:
                self.report("entering object attribute %s..." % _attrname(attrname))
                self.enter(attr, None)

        def cmd_detail(self):
            level = self.levels[-1]
            self.report("entering detail view for object...")
            self.enter(level.items[level.cury].item, "detail")

        def cmd_detailattr(self):
            level = self.levels[-1]
            attrname = level.displayattr[1]
            if attrname is _default:
                curses.beep()
                self.report(AttributeError(_attrname(attrname)))
                return
            attr = _getattr(level.items[level.cury].item, attrname)
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
            helpmsg = " %s" % " ".join(keys)

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
                    posx += self.addstr(i-self._firstheaderline, posx, 0, self.scrsizex, " ibrowse #%d: " % i, self.style_objheadertext)
                    posx += self.addstr(i-self._firstheaderline, posx, 0, self.scrsizex, lv.header, self.style_objheaderobject)
                    if i: # not the first level
                        posx += self.addstr(i-self._firstheaderline, posx, 0, self.scrsizex, " == ", self.style_objheadertext)
                        msg = "%d/%d" % (self.levels[i-1].cury, len(self.levels[i-1].items))
                        if not self.levels[i-1].exhausted:
                            msg += "+"
                        posx += self.addstr(i-self._firstheaderline, posx, 0, self.scrsizex, msg, self.style_objheadernumber)
                    if posx < self.scrsizex:
                        scr.addstr(" "*(self.scrsizex-posx), self.getstyle(self.style_objheadertext))

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
                        (align, text, style) = level.displayrows[i-level.datastarty].get(attrname, (2, None, self.style_noattr))
                        padstyle = self.style_datapad
                        sepstyle = self.style_sep
                        if i == level.cury:
                            style = self.getstylehere(style)
                            padstyle = self.getstylehere(padstyle)
                            sepstyle = self.getstylehere(sepstyle)
                        if align == 2:
                            text = self.nodatachar*cwidth
                            posx += self.addstr(posy, posx, begx, self.scrsizex, text, style)
                        elif align == -1:
                            pad = self.datapadchar*(cwidth-len(text))
                            posx += self.addstr(posy, posx, begx, self.scrsizex, text, style)
                            posx += self.addstr(posy, posx, begx, self.scrsizex, pad, padstyle)
                        elif align == 0:
                            pad1 = self.datapadchar*((cwidth-len(text))//2)
                            pad2 = self.datapadchar*(cwidth-len(text)-len(pad1))
                            posx += self.addstr(posy, posx, begx, self.scrsizex, pad1, padstyle)
                            posx += self.addstr(posy, posx, begx, self.scrsizex, text, style)
                            posx += self.addstr(posy, posx, begx, self.scrsizex, pad2, padstyle)
                        elif align == 1:
                            pad = self.datapadchar*(cwidth-len(text))
                            posx += self.addstr(posy, posx, begx, self.scrsizex, pad, padstyle)
                            posx += self.addstr(posy, posx, begx, self.scrsizex, text, style)
                        posx += self.addstr(posy, posx, begx, self.scrsizex, self.datasepchar, sepstyle)
                        if posx >= self.scrsizex:
                            break
                    else:
                        scr.clrtoeol()

                # Add blank row headers for the rest of the screen
                for posy in xrange(posy+1, self.scrsizey-2):
                    scr.addstr(posy, 0, " " * (level.numbersizex+2), self.getstyle(self.style_colheader))
                    scr.clrtoeol()

                # Display footer
                scr.addstr(self.scrsizey-footery, 0, " "*self.scrsizex, self.getstyle(self.style_footer))

                if level.exhausted:
                    flag = ""
                else:
                    flag = "+"

                scr.addstr(self.scrsizey-footery, self.scrsizex-len(helpmsg)-1, helpmsg, self.getstyle(self.style_footer))

                msg = "%d%s objects (%d marked)" % (len(level.items), flag, level.marked)
                attrname = level.displayattr[1]
                try:
                    if attrname is not _default:
                        msg += ": %s > %s" % (xrepr(level.items[level.cury].item, "footer"), _attrname(attrname))
                    else:
                        msg += ": %s > no attribute" % xrepr(level.items[level.cury].item, "footer")
                except IndexError: # empty
                    pass
                self.addstr(self.scrsizey-footery, 1, 1, self.scrsizex-len(helpmsg)-1, msg, self.style_footer)

                # Display report
                if self._report is not None:
                    if isinstance(self._report, Exception):
                        style = self.getstyle(self.style_error)
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
                    try:
                        scr.addstr(self.scrsizey-1, 0, msg[:self.scrsizex], style)
                    except curses.err:
                        # Protect against error from writing to the last line
                        pass
                    self._report = None
                else:
                    scr.move(self.scrsizey-1, 0)
                scr.clrtoeol()

                # Position cursor
                scr.move(
                    1+self._headerlines+level.cury-level.datastarty,
                    level.numbersizex+3+level.curx-level.datastartx
                )
                scr.refresh()

                # Check keyboard
                while True:
                    c = scr.getch()
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
