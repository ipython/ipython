============
Coding guide
============

General coding conventions
==========================

In general, we'll try to follow the standard Python style conventions as
described in Python's PEP 8 [PEP8]_, the official Python Style Guide.

Other general comments:

* In a large file, top level classes and functions should be separated by 2
  lines to make it easier to separate them visually.

* Use 4 spaces for indentation, **never** use hard tabs.

* Keep the ordering of methods the same in classes that have the same methods.
  This is particularly true for classes that implement similar interfaces and
  for interfaces that are similar.

Naming conventions
==================

In terms of naming conventions, we'll follow the guidelines of PEP 8 [PEP8]_.
Some of the existing code doesn't honor this perfectly, but for all new
IPython code (and much existing code is being refactored), we'll use:

* All ``lowercase`` module names.

* ``CamelCase`` for class names.

* ``lowercase_with_underscores`` for methods, functions, variables and
  attributes.

This may be confusing as some of the existing codebase uses a different
convention (``lowerCamelCase`` for methods and attributes).  Slowly, we will
move IPython over to the new convention, providing shadow names for backward
compatibility in public interfaces.

There are, however, some important exceptions to these rules.  In some cases,
IPython code will interface with packages (Twisted, Wx, Qt) that use other
conventions.  At some level this makes it impossible to adhere to our own
standards at all times.  In particular, when subclassing classes that use other
naming conventions, you must follow their naming conventions.  To deal with
cases like this, we propose the following policy:

* If you are subclassing a class that uses different conventions, use its
  naming conventions throughout your subclass.  Thus, if you are creating a
  Twisted Protocol class, used Twisted's
  ``namingSchemeForMethodsAndAttributes.``

* All IPython's official interfaces should use our conventions.  In some cases
  this will mean that you need to provide shadow names (first implement
  ``fooBar`` and then ``foo_bar = fooBar``).  We want to avoid this at all
  costs, but it will probably be necessary at times.  But, please use this
  sparingly!

Implementation-specific *private* methods will use
``_single_underscore_prefix``.  Names with a leading double underscore will
*only* be used in special cases, as they makes subclassing difficult (such
names are not easily seen by child classes).

Occasionally some run-in lowercase names are used, but mostly for very short
names or where we are implementing methods very similar to existing ones in a
base class (like ``runlines()`` where ``runsource()`` and ``runcode()`` had
established precedent).

The old IPython codebase has a big mix of classes and modules prefixed with an
explicit ``IP``. In Python this is mostly unnecessary, redundant and frowned
upon, as namespaces offer cleaner prefixing. The only case where this approach
is justified is for classes which are expected to be imported into external
namespaces and a very generic name (like Shell) is too likely to clash with
something else.  However, if a prefix seems absolutely necessary the more
specific ``IPY`` or ``ipy`` are preferred.

.. [PEP8] Python Enhancement Proposal 8.  http://www.python.org/peps/pep-0008.html

Attribute declarations for objects
==================================

In general, objects should declare in their *class* all attributes the object
is meant to hold throughout its life.  While Python allows you to add an
attribute to an instance at any point in time, this makes the code harder to
read and requires methods to constantly use checks with hasattr() or try/except
calls.  By declaring all attributes of the object in the class header, there is
a single place one can refer to for understanding the object's data interface,
where comments can explain the role of each variable and when possible,
sensible deafaults can be assigned.

.. Warning::
    
    If an attribute is meant to contain a mutable object, it should be set to
    ``None`` in the class and its mutable value should be set in the object's
    constructor.  Since class attributes are shared by all instances, failure
    to do this can lead to difficult to track bugs.  But you should still set
    it in the class declaration so the interface specification is complete and
    documdented in one place.

A simple example::

    class foo:
        # X does..., sensible default given:
        x = 1
        # y does..., default will be set by constructor
        y = None
        # z starts as an empty list, must be set in constructor
        z = None
        
        def __init__(self, y):
            self.y = y
            self.z = []

	    
New files
=========

When starting a new file for IPython, you can use the following template as a
starting point that has a few common things pre-written for you.  The template
is included in the documentation sources as
:file:`docs/sources/development/template.py`:

.. literalinclude:: template.py
