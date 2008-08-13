# -*- coding: iso-8859-1 -*-

"""
``ipipe`` provides classes to be used in an interactive Python session. Doing a
``from ipipe import *`` is the preferred way to do this. The name of all
objects imported this way starts with ``i`` to minimize collisions.

``ipipe`` supports "pipeline expressions", which is something resembling Unix
pipes. An example is::

    >>> ienv | isort("key.lower()")

This gives a listing of all environment variables sorted by name.


There are three types of objects in a pipeline expression:

* ``Table``s: These objects produce items. Examples are ``ils`` (listing the
  current directory, ``ienv`` (listing environment variables), ``ipwd`` (listing
  user accounts) and ``igrp`` (listing user groups). A ``Table`` must be the
  first object in a pipe expression.

* ``Pipe``s: These objects sit in the middle of a pipe expression. They
  transform the input in some way (e.g. filtering or sorting it). Examples are:
  ``ifilter`` (which filters the input pipe), ``isort`` (which sorts the input
  pipe) and ``ieval`` (which evaluates a function or expression for each object
  in the input pipe).

* ``Display``s: These objects can be put as the last object in a pipeline
  expression. There are responsible for displaying the result of the pipeline
  expression. If a pipeline expression doesn't end in a display object a default
  display objects will be used. One example is ``ibrowse`` which is a ``curses``
  based browser.


Adding support for pipeline expressions to your own objects can be done through
three extensions points (all of them optional):

* An object that will be displayed as a row by a ``Display`` object should
  implement the method ``__xattrs__(self, mode)`` method or register an
  implementation of the generic function ``xattrs``. For more info see ``xattrs``.

* When an object ``foo`` is displayed by a ``Display`` object, the generic
  function ``xrepr`` is used.

* Objects that can be iterated by ``Pipe``s must iterable. For special cases,
  where iteration for display is different than the normal iteration a special
  implementation can be registered with the generic function ``xiter``. This
  makes it possible to use dictionaries and modules in pipeline expressions,
  for example::

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
  of the attributes of the object, i.e.::

      >>> sys.modules | ifilter("_.value is not None") | isort("_.key.lower()")

  does the same as::

      >>> sys.modules | ifilter("value is not None") | isort("key.lower()")

  In addition to expression strings, it's possible to pass callables (taking
  the object as an argument) to ``ifilter()``, ``isort()`` and ``ieval()``::

      >>> sys | ifilter(lambda _:isinstance(_.value, int)) \
      ...     | ieval(lambda _: (_.key, hex(_.value))) | idump
      0          |1
      api_version|0x3f4
      dllhandle  |0x1e000000
      hexversion |0x20402f0
      maxint     |0x7fffffff
      maxunicode |0xffff
"""

skip_doctest = True  # ignore top-level docstring as a doctest.

import sys, os, os.path, stat, glob, new, csv, datetime, types
import itertools, mimetypes, StringIO

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

from IPython.external import simplegeneric
from IPython.external import path

try:
    from IPython import genutils, generics
except ImportError:
    genutils = None
    generics = None

from IPython import ipapi


__all__ = [
    "ifile", "ils", "iglob", "iwalk", "ipwdentry", "ipwd", "igrpentry", "igrp",
    "icsv", "ix", "ichain", "isort", "ifilter", "ieval", "ienum",
    "ienv", "ihist", "ialias", "icap", "idump", "iless"
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

        if isinstance(codestring, basestring):
            code = compile(codestring, "_eval", "eval")
        else:
            code = codestring
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
    end (i.e. the last items produced by the iterator)).

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
    """
    Return the global namespace that is used for expression strings in
    ``ifilter`` and others. This is ``g`` or (if ``g`` is ``None``) IPython's
    user namespace.
    """
    if g is None:
        if ipapi is not None:
            api = ipapi.get()
            if api is not None:
                return api.user_ns
        return globals()
    return g


class Descriptor(object):
    """
    A ``Descriptor`` object is used for describing the attributes of objects.
    """
    def __hash__(self):
        return hash(self.__class__) ^ hash(self.key())

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.key() == other.key()

    def __ne__(self, other):
        return self.__class__ is not other.__class__ or self.key() != other.key()

    def key(self):
        pass

    def name(self):
        """
        Return the name of this attribute for display by a ``Display`` object
        (e.g. as a column title).
        """
        key = self.key()
        if key is None:
            return "_"
        return str(key)

    def attrtype(self, obj):
        """
        Return the type of this attribute (i.e. something like "attribute" or
        "method").
        """

    def valuetype(self, obj):
        """
        Return the type of this attribute value of the object ``obj``.
        """

    def value(self, obj):
        """
        Return the value of this attribute of the object ``obj``.
        """

    def doc(self, obj):
        """
        Return the documentation for this attribute.
        """

    def shortdoc(self, obj):
        """
        Return a short documentation for this attribute (defaulting to the
        first line).
        """
        doc = self.doc(obj)
        if doc is not None:
            doc = doc.strip().splitlines()[0].strip()
        return doc

    def iter(self, obj):
        """
        Return an iterator for this attribute of the object ``obj``.
        """
        return xiter(self.value(obj))


class SelfDescriptor(Descriptor):
    """
    A ``SelfDescriptor`` describes the object itself.
    """
    def key(self):
        return None

    def attrtype(self, obj):
        return "self"

    def valuetype(self, obj):
        return type(obj)

    def value(self, obj):
        return obj

    def __repr__(self):
        return "Self"

selfdescriptor = SelfDescriptor() # there's no need for more than one


class AttributeDescriptor(Descriptor):
    """
    An ``AttributeDescriptor`` describes a simple attribute of an object.
    """
    __slots__ = ("_name", "_doc")

    def __init__(self, name, doc=None):
        self._name = name
        self._doc = doc

    def key(self):
        return self._name

    def doc(self, obj):
        return self._doc

    def attrtype(self, obj):
        return "attr"

    def valuetype(self, obj):
        return type(getattr(obj, self._name))

    def value(self, obj):
        return getattr(obj, self._name)

    def __repr__(self):
        if self._doc is None:
            return "Attribute(%r)" % self._name
        else:
            return "Attribute(%r, %r)" % (self._name, self._doc)


class IndexDescriptor(Descriptor):
    """
    An ``IndexDescriptor`` describes an "attribute" of an object that is fetched
    via ``__getitem__``.
    """
    __slots__ = ("_index",)

    def __init__(self, index):
        self._index = index

    def key(self):
        return self._index

    def attrtype(self, obj):
        return "item"

    def valuetype(self, obj):
        return type(obj[self._index])

    def value(self, obj):
        return obj[self._index]

    def __repr__(self):
        return "Index(%r)" % self._index


class MethodDescriptor(Descriptor):
    """
    A ``MethodDescriptor`` describes a method of an object that can be called
    without argument. Note that this method shouldn't change the object.
    """
    __slots__ = ("_name", "_doc")

    def __init__(self, name, doc=None):
        self._name = name
        self._doc = doc

    def key(self):
        return self._name

    def doc(self, obj):
        if self._doc is None:
            return getattr(obj, self._name).__doc__
        return self._doc

    def attrtype(self, obj):
        return "method"

    def valuetype(self, obj):
        return type(self.value(obj))

    def value(self, obj):
        return getattr(obj, self._name)()

    def __repr__(self):
        if self._doc is None:
            return "Method(%r)" % self._name
        else:
            return "Method(%r, %r)" % (self._name, self._doc)


class IterAttributeDescriptor(Descriptor):
    """
    An ``IterAttributeDescriptor`` works like an ``AttributeDescriptor`` but
    doesn't return an attribute values (because this value might be e.g. a large
    list).
    """
    __slots__ = ("_name", "_doc")

    def __init__(self, name, doc=None):
        self._name = name
        self._doc = doc

    def key(self):
        return self._name

    def doc(self, obj):
        return self._doc

    def attrtype(self, obj):
        return "iter"

    def valuetype(self, obj):
        return noitem

    def value(self, obj):
        return noitem

    def iter(self, obj):
        return xiter(getattr(obj, self._name))

    def __repr__(self):
        if self._doc is None:
            return "IterAttribute(%r)" % self._name
        else:
            return "IterAttribute(%r, %r)" % (self._name, self._doc)


class IterMethodDescriptor(Descriptor):
    """
    An ``IterMethodDescriptor`` works like an ``MethodDescriptor`` but doesn't
    return an attribute values (because this value might be e.g. a large list).
    """
    __slots__ = ("_name", "_doc")

    def __init__(self, name, doc=None):
        self._name = name
        self._doc = doc

    def key(self):
        return self._name

    def doc(self, obj):
        if self._doc is None:
            return getattr(obj, self._name).__doc__
        return self._doc

    def attrtype(self, obj):
        return "itermethod"

    def valuetype(self, obj):
        return noitem

    def value(self, obj):
        return noitem

    def iter(self, obj):
        return xiter(getattr(obj, self._name)())

    def __repr__(self):
        if self._doc is None:
            return "IterMethod(%r)" % self._name
        else:
            return "IterMethod(%r, %r)" % (self._name, self._doc)


class FunctionDescriptor(Descriptor):
    """
    A ``FunctionDescriptor`` turns a function into a descriptor. The function
    will be called with the object to get the type and value of the attribute.
    """
    __slots__ = ("_function", "_name", "_doc")

    def __init__(self, function, name=None, doc=None):
        self._function = function
        self._name = name
        self._doc = doc

    def key(self):
        return self._function

    def name(self):
        if self._name is not None:
            return self._name
        return getattr(self._function, "__xname__", self._function.__name__)

    def doc(self, obj):
        if self._doc is None:
            return self._function.__doc__
        return self._doc

    def attrtype(self, obj):
        return "function"

    def valuetype(self, obj):
        return type(self._function(obj))

    def value(self, obj):
        return self._function(obj)

    def __repr__(self):
        if self._doc is None:
            return "Function(%r)" % self._name
        else:
            return "Function(%r, %r)" % (self._name, self._doc)


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


def xrepr(item, mode="default"):
    """
    Generic function that adds color output and different display modes to ``repr``.

    The result of an ``xrepr`` call is iterable and consists of ``(style, string)``
    tuples. The ``style`` in this tuple must be a ``Style`` object from the
    ``astring`` module. To reconfigure the output the first yielded tuple can be
    a ``(aligment, full)`` tuple instead of a ``(style, string)`` tuple.
    ``alignment``  can be -1 for left aligned, 0 for centered and 1 for right
    aligned (the default is left alignment). ``full`` is a boolean that specifies
    whether the complete output must be displayed or the ``Display`` object is
    allowed to stop output after enough text has been produced (e.g. a syntax
    highlighted text line would use ``True``, but for a large data structure
    (i.e. a nested list, tuple or dictionary) ``False`` would be used).
    The default is full output.

    There are four different possible values for ``mode`` depending on where
    the ``Display`` object will display ``item``:

    ``"header"``
        ``item`` will be displayed in a header line (this is used by ``ibrowse``).

    ``"footer"``
        ``item`` will be displayed in a footer line (this is used by ``ibrowse``).

    ``"cell"``
        ``item`` will be displayed in a table cell/list.

    ``"default"``
        default mode. If an ``xrepr`` implementation recursively outputs objects,
        ``"default"`` must be passed in the recursive calls to ``xrepr``.

    If no implementation is registered for ``item``, ``xrepr`` will try the
    ``__xrepr__`` method on ``item``. If ``item`` doesn't have an ``__xrepr__``
    method it falls back to ``repr``/``__repr__`` for all modes.
    """
    try:
        func = item.__xrepr__
    except AttributeError:
        yield (astyle.style_default, repr(item))
    else:
        try:
            for x in func(mode):
                yield x
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            yield (astyle.style_default, repr(item))
xrepr = simplegeneric.generic(xrepr)


def xrepr_none(self, mode="default"):
    yield (astyle.style_type_none, repr(self))
xrepr.when_object(None)(xrepr_none)


def xrepr_noitem(self, mode="default"):
    yield (2, True)
    yield (astyle.style_nodata, "<?>")
xrepr.when_object(noitem)(xrepr_noitem)


def xrepr_bool(self, mode="default"):
    yield (astyle.style_type_bool, repr(self))
xrepr.when_type(bool)(xrepr_bool)


def xrepr_str(self, mode="default"):
    if mode == "cell":
        yield (astyle.style_default, repr(self.expandtabs(tab))[1:-1])
    else:
        yield (astyle.style_default, repr(self))
xrepr.when_type(str)(xrepr_str)


def xrepr_unicode(self, mode="default"):
    if mode == "cell":
        yield (astyle.style_default, repr(self.expandtabs(tab))[2:-1])
    else:
        yield (astyle.style_default, repr(self))
xrepr.when_type(unicode)(xrepr_unicode)


def xrepr_number(self, mode="default"):
    yield (1, True)
    yield (astyle.style_type_number, repr(self))
xrepr.when_type(int)(xrepr_number)
xrepr.when_type(long)(xrepr_number)
xrepr.when_type(float)(xrepr_number)


def xrepr_complex(self, mode="default"):
    yield (astyle.style_type_number, repr(self))
xrepr.when_type(complex)(xrepr_number)


def xrepr_datetime(self, mode="default"):
    if mode == "cell":
        # Don't use strftime() here, as this requires year >= 1900
        yield (astyle.style_type_datetime,
               "%04d-%02d-%02d %02d:%02d:%02d.%06d" % \
                    (self.year, self.month, self.day,
                     self.hour, self.minute, self.second,
                     self.microsecond),
                )
    else:
        yield (astyle.style_type_datetime, repr(self))
xrepr.when_type(datetime.datetime)(xrepr_datetime)


def xrepr_date(self, mode="default"):
    if mode == "cell":
        yield (astyle.style_type_datetime,
               "%04d-%02d-%02d" % (self.year, self.month, self.day))
    else:
        yield (astyle.style_type_datetime, repr(self))
xrepr.when_type(datetime.date)(xrepr_date)


def xrepr_time(self, mode="default"):
    if mode == "cell":
        yield (astyle.style_type_datetime,
                "%02d:%02d:%02d.%06d" % \
                    (self.hour, self.minute, self.second, self.microsecond))
    else:
        yield (astyle.style_type_datetime, repr(self))
xrepr.when_type(datetime.time)(xrepr_time)


def xrepr_timedelta(self, mode="default"):
    yield (astyle.style_type_datetime, repr(self))
xrepr.when_type(datetime.timedelta)(xrepr_timedelta)


def xrepr_type(self, mode="default"):
    if self.__module__ == "__builtin__":
        yield (astyle.style_type_type, self.__name__)
    else:
        yield (astyle.style_type_type, "%s.%s" % (self.__module__, self.__name__))
xrepr.when_type(type)(xrepr_type)


def xrepr_exception(self, mode="default"):
    if self.__class__.__module__ == "exceptions":
        classname = self.__class__.__name__
    else:
        classname = "%s.%s" % \
            (self.__class__.__module__, self.__class__.__name__)
    if mode == "header" or mode == "footer":
        yield (astyle.style_error, "%s: %s" % (classname, self))
    else:
        yield (astyle.style_error, classname)
xrepr.when_type(Exception)(xrepr_exception)


def xrepr_listtuple(self, mode="default"):
    if mode == "header" or mode == "footer":
        if self.__class__.__module__ == "__builtin__":
            classname = self.__class__.__name__
        else:
            classname = "%s.%s" % \
                (self.__class__.__module__,self.__class__.__name__)
        yield (astyle.style_default,
               "<%s object with %d items at 0x%x>" % \
                   (classname, len(self), id(self)))
    else:
        yield (-1, False)
        if isinstance(self, list):
            yield (astyle.style_default, "[")
            end = "]"
        else:
            yield (astyle.style_default, "(")
            end = ")"
        for (i, subself) in enumerate(self):
            if i:
                yield (astyle.style_default, ", ")
            for part in xrepr(subself, "default"):
                yield part
        yield (astyle.style_default, end)
xrepr.when_type(list)(xrepr_listtuple)
xrepr.when_type(tuple)(xrepr_listtuple)


def xrepr_dict(self, mode="default"):
    if mode == "header" or mode == "footer":
        if self.__class__.__module__ == "__builtin__":
            classname = self.__class__.__name__
        else:
            classname = "%s.%s" % \
                (self.__class__.__module__,self.__class__.__name__)
        yield (astyle.style_default,
               "<%s object with %d items at 0x%x>" % \
                (classname, len(self), id(self)))
    else:
        yield (-1, False)
        if isinstance(self, dict):
            yield (astyle.style_default, "{")
            end = "}"
        else:
            yield (astyle.style_default, "dictproxy((")
            end = "})"
        for (i, (key, value)) in enumerate(self.iteritems()):
            if i:
                yield (astyle.style_default, ", ")
            for part in xrepr(key, "default"):
                yield part
            yield (astyle.style_default, ": ")
            for part in xrepr(value, "default"):
                yield part
        yield (astyle.style_default, end)
xrepr.when_type(dict)(xrepr_dict)
xrepr.when_type(types.DictProxyType)(xrepr_dict)


def upgradexattr(attr):
    """
    Convert an attribute descriptor string to a real descriptor object.

    If attr already is a descriptor object return if unmodified. A
    ``SelfDescriptor`` will be returned if ``attr`` is ``None``. ``"foo"``
    returns an ``AttributeDescriptor`` for the attribute named ``"foo"``.
    ``"foo()"`` returns a ``MethodDescriptor`` for the method named ``"foo"``.
    ``"-foo"`` will return an ``IterAttributeDescriptor`` for the attribute
    named ``"foo"`` and ``"-foo()"`` will return an ``IterMethodDescriptor``
    for the method named ``"foo"``. Furthermore integer will return the appropriate
    ``IndexDescriptor`` and callables will return a ``FunctionDescriptor``.
    """
    if attr is None:
        return selfdescriptor
    elif isinstance(attr, Descriptor):
        return attr
    elif isinstance(attr, str):
        if attr.endswith("()"):
            if attr.startswith("-"):
                return IterMethodDescriptor(attr[1:-2])
            else:
                return MethodDescriptor(attr[:-2])
        else:
            if attr.startswith("-"):
                return IterAttributeDescriptor(attr[1:])
            else:
                return AttributeDescriptor(attr)
    elif isinstance(attr, (int, long)):
        return IndexDescriptor(attr)
    elif callable(attr):
        return FunctionDescriptor(attr)
    else:
        raise TypeError("can't handle descriptor %r" % attr)


def xattrs(item, mode="default"):
    """
    Generic function that returns an iterable of attribute descriptors
    to be used for displaying the attributes ob the object ``item`` in display
    mode ``mode``.

    There are two possible modes:

    ``"detail"``
        The ``Display`` object wants to display a detailed list of the object
        attributes.

    ``"default"``
        The ``Display`` object wants to display the object in a list view.

    If no implementation is registered for the object ``item`` ``xattrs`` falls
    back to trying the ``__xattrs__`` method of the object. If this doesn't
    exist either, ``dir(item)`` is used for ``"detail"`` mode and ``(None,)``
    for ``"default"`` mode.

    The implementation must yield attribute descriptors (see the class
    ``Descriptor`` for more info). The ``__xattrs__`` method may also return
    attribute descriptor strings (and ``None``) which will be converted to real
    descriptors by ``upgradexattr()``.
    """
    try:
        func = item.__xattrs__
    except AttributeError:
        if mode == "detail":
            for attrname in dir(item):
                yield AttributeDescriptor(attrname)
        else:
            yield selfdescriptor
    else:
        for attr in func(mode):
            yield upgradexattr(attr)
xattrs = simplegeneric.generic(xattrs)


def xattrs_complex(self, mode="default"):
    if mode == "detail":
        return (AttributeDescriptor("real"), AttributeDescriptor("imag"))
    return (selfdescriptor,)
xattrs.when_type(complex)(xattrs_complex)


def _isdict(item):
    try:
        itermeth = item.__class__.__iter__
    except (AttributeError, TypeError):
        return False
    return itermeth is dict.__iter__ or itermeth is types.DictProxyType.__iter__


def _isstr(item):
    if not isinstance(item, basestring):
        return False
    try:
        itermeth = item.__class__.__iter__
    except AttributeError:
        return True
    return False # ``__iter__`` has been redefined


def xiter(item):
    """
    Generic function that implements iteration for pipeline expression. If no
    implementation is registered for ``item`` ``xiter`` falls back to ``iter``.
    """
    try:
        func = item.__xiter__
    except AttributeError:
        if _isdict(item):
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
        elif _isstr(item):
            if not item:
                raise ValueError("can't enter empty string")
            lines = item.splitlines()
            if len(lines) == 1:
               def iterone(item):
                   yield item
               return iterone(item)
            else:
                return iter(lines)
        return iter(item)
    else:
        return iter(func()) # iter() just to be safe
xiter = simplegeneric.generic(xiter)


class ichain(Pipe):
    """
    Chains multiple ``Table``s into one.
    """

    def __init__(self, *iters):
        self.iters = iters

    def __iter__(self):
        return itertools.chain(*self.iters)

    def __xrepr__(self, mode="default"):
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

    def mimetype(self):
        """
        Return MIME type guessed from the extension.
        """
        return mimetypes.guess_type(self.basename())[0]

    def encoding(self):
        """
        Return guessed compression (like "compress" or "gzip").
        """
        return mimetypes.guess_type(self.basename())[1]

    def __repr__(self):
        return "ifile(%s)" % path._base.__repr__(self)

    if sys.platform == "win32":
        defaultattrs = (None, "type", "size", "modestr", "mdate")
    else:
        defaultattrs = (None, "type", "size", "modestr", "owner", "group", "mdate")

    def __xattrs__(self, mode="default"):
        if mode == "detail":
            return (
                "name",
                "basename()",
                "abspath()",
                "realpath()",
                "type",
                "mode",
                "modestr",
                "stat()",
                "lstat()",
                "uid",
                "gid",
                "owner",
                "group",
                "dev",
                "nlink",
                "ctime",
                "mtime",
                "atime",
                "cdate",
                "mdate",
                "adate",
                "size",
                "blocks",
                "blksize",
                "isdir()",
                "islink()",
                "mimetype()",
                "encoding()",
                "-listdir()",
                "-dirs()",
                "-files()",
                "-walk()",
                "-walkdirs()",
                "-walkfiles()",
            )
        else:
            return self.defaultattrs


def xiter_ifile(self):
    if self.isdir():
        yield (self / os.pardir).abspath()
        for child in sorted(self.listdir()):
            yield child
    else:
        f = self.open("rb")
        for line in f:
            yield line
        f.close()
xiter.when_type(ifile)(xiter_ifile)


# We need to implement ``xrepr`` for ``ifile`` as a generic function, because
# otherwise ``xrepr_str`` would kick in.
def xrepr_ifile(self, mode="default"):
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
    if mode in ("cell", "header", "footer"):
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
xrepr.when_type(ifile)(xrepr_ifile)


class ils(Table):
    """
    List the current (or a specified) directory.

    Examples::

        >>> ils
        <class 'IPython.Extensions.ipipe.ils'>
        >>> ils("/usr/local/lib/python2.4")
        IPython.Extensions.ipipe.ils('/usr/local/lib/python2.4')
        >>> ils("~")
        IPython.Extensions.ipipe.ils('/home/fperez')
        # all-random
    """
    def __init__(self, base=os.curdir, dirs=True, files=True):
        self.base = os.path.expanduser(base)
        self.dirs = dirs
        self.files = files

    def __iter__(self):
        base = ifile(self.base)
        yield (base / os.pardir).abspath()
        for child in sorted(base.listdir()):
            if self.dirs:
                if self.files:
                    yield child
                else:
                    if child.isdir():
                        yield child
            elif self.files:
                if not child.isdir():
                    yield child

    def __xrepr__(self, mode="default"):
       return xrepr(ifile(self.base), mode)

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self.base)


class iglob(Table):
    """
    List all files and directories matching a specified pattern.
    (See ``glob.glob()`` for more info.).

    Examples::

        >>> iglob("*.py")
        IPython.Extensions.ipipe.iglob('*.py')
    """
    def __init__(self, glob):
        self.glob = glob

    def __iter__(self):
        for name in glob.glob(self.glob):
            yield ifile(name)

    def __xrepr__(self, mode="default"):
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
    List all files and directories in a directory and it's subdirectory::

        >>> iwalk
        <class 'IPython.Extensions.ipipe.iwalk'>
        >>> iwalk("/usr/lib")
        IPython.Extensions.ipipe.iwalk('/usr/lib')
        >>> iwalk("~")
        IPython.Extensions.ipipe.iwalk('/home/fperez')  # random
        
    """
    def __init__(self, base=os.curdir, dirs=True, files=True):
        self.base = os.path.expanduser(base)
        self.dirs = dirs
        self.files = files

    def __iter__(self):
        for (dirpath, dirnames, filenames) in os.walk(self.base):
            if self.dirs:
                for name in sorted(dirnames):
                    yield ifile(os.path.join(dirpath, name))
            if self.files:
                for name in sorted(filenames):
                    yield ifile(os.path.join(dirpath, name))

    def __xrepr__(self, mode="default"):
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

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self._id == other._id

    def __ne__(self, other):
        return self.__class__ is not other.__class__ or self._id != other._id

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

    def __xattrs__(self, mode="default"):
       return ("name", "passwd", "uid", "gid", "gecos", "dir", "shell")

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self._id)


class ipwd(Table):
    """
    List all entries in the Unix user account and password database.

    Example::

        >>> ipwd | isort("uid")
        <IPython.Extensions.ipipe.isort key='uid' reverse=False at 0x849efec>
        # random
    """
    def __iter__(self):
        for entry in pwd.getpwall():
            yield ipwdentry(entry.pw_name)

    def __xrepr__(self, mode="default"):
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

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self._id == other._id

    def __ne__(self, other):
        return self.__class__ is not other.__class__ or self._id != other._id

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

    def __xattrs__(self, mode="default"):
        return ("name", "passwd", "gid", "mem")

    def __xrepr__(self, mode="default"):
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

    def __iter__(self):
        for member in self.mem:
            yield ipwdentry(member)

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self._id)


class igrp(Table):
    """
    This ``Table`` lists all entries in the Unix group database.
    """
    def __iter__(self):
        for entry in grp.getgrall():
            yield igrpentry(entry.gr_name)

    def __xrepr__(self, mode="default"):
        if mode == "header" or mode == "footer":
            yield (astyle.style_default, "%s()" % self.__class__.__name__)
        else:
            yield (astyle.style_default, repr(self))


class Fields(object):
    def __init__(self, fieldnames, **fields):
        self.__fieldnames = [upgradexattr(fieldname) for fieldname in fieldnames]
        for (key, value) in fields.iteritems():
            setattr(self, key, value)

    def __xattrs__(self, mode="default"):
        return self.__fieldnames

    def __xrepr__(self, mode="default"):
        yield (-1, False)
        if mode == "header" or mode == "cell":
            yield (astyle.style_default, self.__class__.__name__)
            yield (astyle.style_default, "(")
            for (i, f) in enumerate(self.__fieldnames):
                if i:
                    yield (astyle.style_default, ", ")
                yield (astyle.style_default, f.name())
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
                yield (astyle.style_default, f.name())
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

    def __xrepr__(self, mode="default"):
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
    def __xattrs__(self, mode="default"):
        return xrange(len(self))

    def __xrepr__(self, mode="default"):
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

    Example::

        >>> ienv
        <class 'IPython.Extensions.ipipe.ienv'>
    """

    def __iter__(self):
        fields = ("key", "value")
        for (key, value) in os.environ.iteritems():
            yield Fields(fields, key=key, value=value)

    def __xrepr__(self, mode="default"):
        if mode == "header" or mode == "cell":
            yield (astyle.style_default, "%s()" % self.__class__.__name__)
        else:
            yield (astyle.style_default, repr(self))


class ihist(Table):
    """
    IPython input history

    Example::

        >>> ihist
        <class 'IPython.Extensions.ipipe.ihist'>
        >>> ihist(True) # raw mode
        <IPython.Extensions.ipipe.ihist object at 0x849602c>  # random
    """
    def __init__(self, raw=True):
        self.raw = raw

    def __iter__(self):
        api = ipapi.get()
        if self.raw:
            for line in api.IP.input_hist_raw:
                yield line.rstrip("\n")
        else:
            for line in api.IP.input_hist:
                yield line.rstrip("\n")


class Alias(object):
    """
    Entry in the alias table
    """
    def __init__(self, name, args, command):
        self.name = name
        self.args = args
        self.command = command

    def __xattrs__(self, mode="default"):
        return ("name", "args", "command")


class ialias(Table):
    """
    IPython alias list

    Example::

        >>> ialias
        <class 'IPython.Extensions.ipipe.ialias'>
    """
    def __iter__(self):
        api = ipapi.get()

        for (name, (args, command)) in api.IP.alias_table.iteritems():
            yield Alias(name, args, command)


class icsv(Pipe):
    """
    This ``Pipe`` turns the input (with must be a pipe outputting lines
    or an ``ifile``) into lines of CVS columns.
    """
    def __init__(self, **csvargs):
        """
        Create an ``icsv`` object. ``cvsargs`` will be passed through as
        keyword arguments to ``cvs.reader()``.
        """
        self.csvargs = csvargs

    def __iter__(self):
        input = self.input
        if isinstance(input, ifile):
            input = input.open("rb")
        reader = csv.reader(input, **self.csvargs)
        for line in reader:
            yield List(line)

    def __xrepr__(self, mode="default"):
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

    Examples::

        >>> ix("ps x")
        IPython.Extensions.ipipe.ix('ps x')

        >>> ix("find .") | ifile
        <IPython.Extensions.ipipe.ieval expr=<class 'IPython.Extensions.ipipe.ifile'> at 0x8509d2c>
        # random
    """
    def __init__(self, cmd):
        self.cmd = cmd
        self._pipeout = None

    def __iter__(self):
        (_pipein, self._pipeout) = os.popen4(self.cmd)
        _pipein.close()
        for l in self._pipeout:
            yield l.rstrip("\r\n")
        self._pipeout.close()
        self._pipeout = None

    def __del__(self):
        if self._pipeout is not None and not self._pipeout.closed:
            self._pipeout.close()
        self._pipeout = None

    def __xrepr__(self, mode="default"):
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

    Examples::

        >>> ils | ifilter("_.isfile() and size>1000")
        >>> igrp | ifilter("len(mem)")
        >>> sys.modules | ifilter(lambda _:_.value is not None)
        # all-random
    """

    def __init__(self, expr, globals=None, errors="raiseifallfail"):
        """
        Create an ``ifilter`` object. ``expr`` can be a callable or a string
        containing an expression. ``globals`` will be used as the global
        namespace for calling string expressions (defaulting to IPython's
        user namespace). ``errors`` specifies how exception during evaluation
        of ``expr`` are handled:

        ``"drop"``
            drop all items that have errors;

        ``"keep"``
            keep all items that have errors;

        ``"keeperror"``
            keep the exception of all items that have errors;

        ``"raise"``
            raise the exception;

        ``"raiseifallfail"``
            raise the first exception if all items have errors; otherwise drop
            those with errors (this is the default).
        """
        self.expr = expr
        self.globals = globals
        self.errors = errors

    def __iter__(self):
        if callable(self.expr):
            test = self.expr
        else:
            g = getglobals(self.globals)
            expr = compile(self.expr, "ipipe-expression", "eval")
            def test(item):
                return eval(expr, g, AttrNamespace(item))

        ok = 0
        exc_info = None
        for item in xiter(self.input):
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

    def __xrepr__(self, mode="default"):
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

    Examples::

        >>> ils | ieval("_.abspath()")
        # random
        >>> sys.path | ieval(ifile)
        # random
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

    def __iter__(self):
        if callable(self.expr):
            do = self.expr
        else:
            g = getglobals(self.globals)
            expr = compile(self.expr, "ipipe-expression", "eval")
            def do(item):
                return eval(expr, g, AttrNamespace(item))

        ok = 0
        exc_info = None
        for item in xiter(self.input):
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

    def __xrepr__(self, mode="default"):
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

    Examples::

        >>> xrange(20) | ieval("_,_*_") | ienum | ifilter("index % 2 == 0") | ieval("object")
    """
    skip_doctest = True
    
    def __iter__(self):
        fields = ("index", "object")
        for (index, object) in enumerate(xiter(self.input)):
            yield Fields(fields, index=index, object=object)


class isort(Pipe):
    """
    Sorts the input pipe.

    Examples::

        >>> ils | isort("size")
        <IPython.Extensions.ipipe.isort key='size' reverse=False at 0x849ec2c>
        >>> ils | isort("_.isdir(), _.lower()", reverse=True)
        <IPython.Extensions.ipipe.isort key='_.isdir(), _.lower()' reverse=True at 0x849eacc>
        # all-random
    """

    def __init__(self, key=None, globals=None, reverse=False):
        """
        Create an ``isort`` object. ``key`` can be a callable or a string
        containing an expression (or ``None`` in which case the items
        themselves will be sorted). If ``reverse`` is true the sort order
        will be reversed. For the meaning of ``globals`` see ``ifilter``.
        """
        self.key = key
        self.globals = globals
        self.reverse = reverse

    def __iter__(self):
        if self.key is None:
            items = sorted(xiter(self.input), reverse=self.reverse)
        elif callable(self.key):
            items = sorted(xiter(self.input), key=self.key, reverse=self.reverse)
        else:
            g = getglobals(self.globals)
            key = compile(self.key, "ipipe-expression", "eval")
            def realkey(item):
                return eval(key, g, AttrNamespace(item))
            items = sorted(xiter(self.input), key=realkey, reverse=self.reverse)
        for item in items:
            yield item

    def __xrepr__(self, mode="default"):
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

    def __init__(self, input=None):
        self.input = input

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
                for item in xiter(self.input):
                    first = False
                    for attr in xattrs(item, "default"):
                        if first:
                            first = False
                        else:
                            pager.write(" ")
                        attr = upgradexattr(attr)
                        if not isinstance(attr, SelfDescriptor):
                            pager.write(attr.name())
                            pager.write("=")
                        pager.write(str(attr.value(item)))
                    pager.write("\n")
            finally:
                pager.close()
        except Exception, exc:
            print "%s: %s" % (exc.__class__.__name__, str(exc))


class _RedirectIO(object):
    def __init__(self,*args,**kwargs):
        """
        Map the system output streams to self.
        """
        self.stream = StringIO.StringIO()
        self.stdout = sys.stdout
        sys.stdout = self
        self.stderr = sys.stderr
        sys.stderr = self

    def write(self, text):
        """
        Write both to screen and to self.
        """
        self.stream.write(text)
        self.stdout.write(text)
        if "\n" in text:
            self.stdout.flush()

    def writelines(self, lines):
        """
        Write lines both to screen and to self.
        """
        self.stream.writelines(lines)
        self.stdout.writelines(lines)
        self.stdout.flush()

    def restore(self):
        """
        Restore the default system streams.
        """
        self.stdout.flush()
        self.stderr.flush()
        sys.stdout = self.stdout
        sys.stderr = self.stderr


class icap(Table):
    """
    Execute a python string and capture any output to stderr/stdout.

    Examples::

        >>> import time
        >>> icap("for i in range(10): print i, time.sleep(0.1)")

    """
    skip_doctest = True
    
    def __init__(self, expr, globals=None):
        self.expr = expr
        self.globals = globals
        log = _RedirectIO()
        try:
            exec(expr, getglobals(globals))
        finally:
            log.restore()
        self.stream = log.stream

    def __iter__(self):
        self.stream.seek(0)
        for line in self.stream:
            yield line.rstrip("\r\n")

    def __xrepr__(self, mode="default"):
        if mode == "header" or mode == "footer":
            yield (astyle.style_default,
                   "%s(%r)" % (self.__class__.__name__, self.expr))
        else:
            yield (astyle.style_default, repr(self))

    def __repr__(self):
        return "%s.%s(%r)" % \
            (self.__class__.__module__, self.__class__.__name__, self.expr)


def xformat(value, mode, maxlength):
    align = None
    full = True
    width = 0
    text = astyle.Text()
    for (style, part) in xrepr(value, mode):
        # only consider the first result
        if align is None:
            if isinstance(style, int):
                # (style, text) really is (alignment, stop)
                align = style
                full = part
                continue
            else:
                align = -1
                full = True
        if not isinstance(style, int):
            text.append((style, part))
            width += len(part)
            if width >= maxlength and not full:
                text.append((astyle.style_ellisis, "..."))
                width += 3
                break
    if align is None: # default to left alignment
        align = -1
    return (align, width, text)



import astyle

class idump(Display):
    # The approximate maximum length of a column entry
    maxattrlength = 200

    # Style for column names
    style_header = astyle.Style.fromstr("white:black:bold")

    def __init__(self, input=None, *attrs):
        Display.__init__(self, input)
        self.attrs = [upgradexattr(attr) for attr in attrs]
        self.headerpadchar = " "
        self.headersepchar = "|"
        self.datapadchar = " "
        self.datasepchar = "|"

    def display(self):
        stream = genutils.Term.cout
        allattrs = []
        attrset = set()
        colwidths = {}
        rows = []
        for item in xiter(self.input):
            row = {}
            attrs = self.attrs
            if not attrs:
                attrs = xattrs(item, "default")
            for attr in attrs:
                if attr not in attrset:
                    allattrs.append(attr)
                    attrset.add(attr)
                    colwidths[attr] = len(attr.name())
                try:
                    value = attr.value(item)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception, exc:
                    value = exc
                (align, width, text) = xformat(value, "cell", self.maxattrlength)
                colwidths[attr] = max(colwidths[attr], width)
                # remember alignment, length and colored parts
                row[attr] = (align, width, text)
            rows.append(row)

        stream.write("\n")
        for (i, attr) in enumerate(allattrs):
            attrname = attr.name()
            self.style_header(attrname).write(stream)
            spc = colwidths[attr] - len(attrname)
            if i < len(colwidths)-1:
                stream.write(self.headerpadchar*spc)
                stream.write(self.headersepchar)
        stream.write("\n")

        for row in rows:
            for (i, attr) in enumerate(allattrs):
                (align, width, text) = row[attr]
                spc = colwidths[attr] - width
                if align == -1:
                    text.write(stream)
                    if i < len(colwidths)-1:
                        stream.write(self.datapadchar*spc)
                elif align == 0:
                    spc = colwidths[attr] - width
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


class AttributeDetail(Table):
    """
    ``AttributeDetail`` objects are use for displaying a detailed list of object
    attributes.
    """
    def __init__(self, object, descriptor):
        self.object = object
        self.descriptor = descriptor

    def __iter__(self):
        return self.descriptor.iter(self.object)

    def name(self):
        return self.descriptor.name()

    def attrtype(self):
        return self.descriptor.attrtype(self.object)

    def valuetype(self):
        return self.descriptor.valuetype(self.object)

    def doc(self):
        return self.descriptor.doc(self.object)

    def shortdoc(self):
        return self.descriptor.shortdoc(self.object)

    def value(self):
        return self.descriptor.value(self.object)

    def __xattrs__(self, mode="default"):
        attrs = ("name()", "attrtype()", "valuetype()", "value()", "shortdoc()")
        if mode == "detail":
            attrs += ("doc()",)
        return attrs

    def __xrepr__(self, mode="default"):
        yield (-1, True)
        valuetype = self.valuetype()
        if valuetype is not noitem:
            for part in xrepr(valuetype):
                yield part
            yield (astyle.style_default, " ")
        yield (astyle.style_default, self.attrtype())
        yield (astyle.style_default, " ")
        yield (astyle.style_default, self.name())
        yield (astyle.style_default, " of ")
        for part in xrepr(self.object):
            yield part


try:
    from ibrowse import ibrowse
except ImportError:
    # No curses (probably Windows) => try igrid
    try:
        from igrid import igrid
    except ImportError:
        # no wx either => use ``idump`` as the default display.
        defaultdisplay = idump
    else:
        defaultdisplay = igrid
        __all__.append("igrid")
else:
    defaultdisplay = ibrowse
    __all__.append("ibrowse")


# If we're running under IPython, register our objects with IPython's
# generic function ``result_display``, else install a displayhook
# directly as sys.displayhook
if generics is not None:
    def display_display(obj):
        return obj.display()
    generics.result_display.when_type(Display)(display_display)

    def display_tableobject(obj):
        return display_display(defaultdisplay(obj))
    generics.result_display.when_type(Table)(display_tableobject)

    def display_tableclass(obj):
        return display_tableobject(obj())
    generics.result_display.when_type(Table.__metaclass__)(display_tableclass)
else:
    def installdisplayhook():
        _originalhook = sys.displayhook
        def displayhook(obj):
            if isinstance(obj, type) and issubclass(obj, Table):
                obj = obj()
            if isinstance(obj, Table):
                obj = defaultdisplay(obj)
            if isinstance(obj, Display):
                return obj.display()
            else:
                _originalhook(obj)
        sys.displayhook = displayhook
    installdisplayhook()
