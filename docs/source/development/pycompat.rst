Writing code for Python 2 and 3
===============================

Iterators
---------

Many built in functions and methods in Python 2 come in pairs, one
returning a list, and one returning an iterator (e.g. :func:`range` and
:func:`xrange`). In Python 3, there is usually only the iterator form,
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

Unicode
-------

Always be explicit about what is text (unicode) and what is bytes.
*Encoding* goes from unicode to bytes, and *decoding* goes from bytes
to unicode.

To open files for reading or writing text, use :func:`io.open`, which is
the Python 3 builtin ``open`` function, available on Python 2 as well.
We almost always need to specify the encoding parameter, because the
default is platform dependent.

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
Python 2 and 3. In most cases, the helper function
:func:`~IPython.utils.py3compat.with_metaclass` (copied from the six
library) can be used like this::

    class FormatterABC(with_metaclass(abc.ABCMeta, object)):
        ...

Combining inheritance between Qt and the traitlets system, however, does
not work with this. Instead, we do this::

    class QtKernelClientMixin(MetaQObjectHasTraits('NewBase', (HasTraits, SuperQObject), {})): 
        ...

This gives the new class a metaclass of :class:`~IPython.qt.util.MetaQObjectHasTraits`,
and the parent classes :class:`~IPython.utils.traitlets.HasTraits` and
:class:`~IPython.qt.util.SuperQObject`.
