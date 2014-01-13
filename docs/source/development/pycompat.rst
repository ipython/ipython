Writing code for Python 2 and 3
===============================

.. module:: IPython.utils.py3compat
   :synopsis: Python 2 & 3 compatibility helpers

.. data:: PY3

   Boolean indicating whether we're currently in Python 3.

Iterators
---------

Many built in functions and methods in Python 2 come in pairs, one
returning a list, and one returning an iterator (e.g. :func:`range` and
:func:`python:xrange`). In Python 3, there is usually only the iterator form,
but it has the name which gives a list in Python 2 (e.g. :func:`range`).

The way to write compatible code depends on what you need:

* A list, e.g. for serialisation, or to test if something is in it.
* Iteration, but it will never be used for very many items, so efficiency
  isn't especially important.
* Iteration over many items, where efficiency is important.

================  =================  =======================
list              iteration (small)  iteration(large)
================  =================  =======================
list(range(n))    range(n)           py3compat.xrange(n)
list(map(f, it))  map(f, it)         --
list(zip(a, b))   zip(a, b)          --
list(d.items())   d.items()          py3compat.iteritems(d)
list(d.values())  d.values()         py3compat.itervalues(d)
================  =================  =======================

Iterating over a dictionary yields its keys, so there is rarely a need
to use :meth:`dict.keys` or :meth:`dict.iterkeys`.

Avoid using :func:`map` to cause function side effects. This is more
clearly written with a simple for loop.

.. data:: xrange

   A reference to ``range`` on Python 3, and :func:`python:xrange` on Python 2.

.. function:: iteritems(d)
              itervalues(d)

   Iterate over (key, value) pairs of a dictionary, or just over values.
   ``iterkeys`` is not defined: iterating over the dictionary yields its keys.

Changed standard library locations
----------------------------------

Several parts of the standard library have been renamed and moved. This
is a short list of things that we're using. A couple of them have names
in :mod:`IPython.utils.py3compat`, so you don't need both
imports in each module that uses them.

==================  ============  ===========
Python 2            Python 3      py3compat
==================  ============  ===========
:func:`raw_input`   input         input
:mod:`__builtin__`  builtins      builtin_mod
:mod:`StringIO`     io
:mod:`Queue`        queue
:mod:`cPickle`      pickle
:mod:`thread`       _thread
:mod:`copy_reg`     copyreg
:mod:`urlparse`     urllib.parse
:mod:`repr`         reprlib
:mod:`Tkinter`      tkinter
:mod:`Cookie`       http.cookie
:mod:`_winreg`      winreg
==================  ============  ===========

Be careful with StringIO: :class:`io.StringIO` is available in Python 2.7,
but it behaves differently from :class:`StringIO.StringIO`, and much of
our code assumes the use of the latter on Python 2. So a try/except on
the import may cause problems.

.. function:: input

   Behaves like :func:`python:raw_input` on Python 2.

.. data:: builtin_mod
          builtin_mod_name

   A reference to the module containing builtins, and its name as a string.

Unicode
-------

Always be explicit about what is text (unicode) and what is bytes.
*Encoding* goes from unicode to bytes, and *decoding* goes from bytes
to unicode.

To open files for reading or writing text, use :func:`io.open`, which is
the Python 3 builtin ``open`` function, available on Python 2 as well.
We almost always need to specify the encoding parameter, because the
default is platform dependent.

We have several helper functions for converting between string types. They all
use the encoding from :func:`IPython.utils.encoding.getdefaultencoding` by default,
and the ``errors='replace'`` option to do best-effort conversions for the user's
system.

.. function:: unicode_to_str(u, encoding=None)
              str_to_unicode(s, encoding=None)

   Convert between unicode and the native str type. No-ops on Python 3.

.. function:: str_to_bytes(s, encoding=None)
              bytes_to_str(u, encoding=None)

   Convert between bytes and the native str type. No-ops on Python 2.

.. function:: cast_unicode(s, encoding=None)
              cast_bytes(s, encoding=None)

   Convert strings to unicode/bytes when they may be of either type.

.. function:: cast_unicode_py2(s, encoding=None)
              cast_bytes_py2(s, encoding=None)

   Convert strings to unicode/bytes when they may be of either type on Python 2,
   but return them unaltered on Python 3 (where string types are more
   predictable).

.. data:: unicode_type

   A reference to ``str`` on Python 3, and to ``unicode`` on Python 2.

.. data:: string_types

   A tuple for isinstance checks: ``(str,)`` on Python 3, ``(str, unicode)`` on
   Python 2.

Relative imports
----------------

::

    # This makes Python 2 behave like Python 3:
    from __future__ import absolute_import
    
    import io  # Imports the standard library io module
    from . import io  # Import the io module from the package
                      # containing the current module
    from .io import foo  # foo from the io module next to this module
    from IPython.utils import io  # This still works

Print function
--------------

::

    # Support the print function on Python 2:
    from __future__ import print_function
    
    print(a, b)
    print(foo, file=sys.stderr)
    print(bar, baz, sep='\t', end='')

Metaclasses
-----------

The syntax for declaring a class with a metaclass is different in
Python 2 and 3. A helper function works for most cases:

.. function:: with_metaclass

   Create a base class with a metaclass. Copied from the six library.

   Used like this::

       class FormatterABC(with_metaclass(abc.ABCMeta, object)):
           ...

Combining inheritance between Qt and the traitlets system, however, does
not work with this. Instead, we do this::

    class QtKernelClientMixin(MetaQObjectHasTraits('NewBase', (HasTraits, SuperQObject), {})): 
        ...

This gives the new class a metaclass of :class:`~IPython.qt.util.MetaQObjectHasTraits`,
and the parent classes :class:`~IPython.utils.traitlets.HasTraits` and
:class:`~IPython.qt.util.SuperQObject`.


Doctests
--------

.. function:: doctest_refactor_print(func_or_str)

   Refactors print statements in doctests in Python 3 only. Accepts a string
   or a function, so it can be used as a decorator.

.. function:: u_format(func_or_str)

   Handle doctests written with ``{u}'abcþ'``, replacing the ``{u}`` with ``u``
   for Python 2, and removing it for Python 3.

   Accepts a string or a function, so it can be used as a decorator.

Execfile
--------

.. function:: execfile(fname, glob, loc=None)

   Equivalent to the Python 2 :func:`python:execfile` builtin. We redefine it in
   Python 2 to better handle non-ascii filenames.

Miscellaneous
-------------

.. autofunction:: safe_unicode

.. function:: isidentifier(s, dotted=False)

   Checks whether the string s is a valid identifier in this version of Python.
   In Python 3, non-ascii characters are allowed. If ``dotted`` is True, it
   allows dots (i.e. attribute access) in the string.

.. function:: getcwd()

   Return the current working directory as unicode, like :func:`os.getcwdu` on
   Python 2.

.. function:: MethodType

   Constructor for :class:`types.MethodType` that takes two arguments, like
   the real constructor on Python 3.
