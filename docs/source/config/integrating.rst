.. _integrating:

=====================================
Integrating your objects with IPython
=====================================

Tab completion
==============

To change the attributes displayed by tab-completing your object, define a
``__dir__(self)`` method for it. For more details, see the documentation of the
built-in `dir() function <http://docs.python.org/library/functions.html#dir>`_.

You can also customise key completions for your objects, e.g. pressing tab after
``obj["a``. To do so, define a method ``_ipython_key_completions_()``, which
returns a list of objects which are possible keys in a subscript expression
``obj[key]``.

.. versionadded:: 5.0
   Custom key completions

.. _integrating_rich_display:

Rich display
============

The notebook and the Qt console can display richer representations of objects.
To use this, you can define any of a number of ``_repr_*_()`` methods. Note that
these are surrounded by single, not double underscores.

Both the notebook and the Qt console can display ``svg``, ``png`` and ``jpeg``
representations. The notebook can also display ``html``, ``javascript``,
``markdown`` and ``latex``. If the methods don't exist, or return ``None``, it
falls back to a standard ``repr()``.

For example::

    class Shout(object):
        def __init__(self, text):
            self.text = text
        
        def _repr_html_(self):
            return "<h1>" + self.text + "</h1>"

There are also two more powerful display methods:

.. class:: MyObject

   .. method:: _repr_mimebundle_(include=None, exclude=None)

     Should return a dictionary of multiple formats, keyed by mimetype, or a tuple
     of two dictionaries: *data, metadata*. If this returns something, other
     ``_repr_*_`` methods are ignored. The method should take keyword arguments
     ``include`` and ``exclude``, though it is not required to respect them.

   .. method:: _ipython_display_()

      Displays the object as a side effect; the return value is ignored. If this
      is defined, all other display methods are ignored.

Formatters for third-party types
--------------------------------

The user can also register formatters for types without modifying the class::

    from bar import Foo

    def foo_html(obj):
        return '<marquee>Foo object %s</marquee>' % obj.name

    html_formatter = get_ipython().display_formatter.formatters['text/html']
    html_formatter.for_type(Foo, foo_html)

    # Or register a type without importing it - this does the same as above:
    html_formatter.for_type_by_name('bar.Foo', foo_html)

Custom exception tracebacks
===========================

Rarely, you might want to display a custom traceback when reporting an
exception. To do this, define the custom traceback using
`_render_traceback_(self)` method which returns a list of strings, one string
for each line of the traceback. For example, the `ipyparallel
<http://ipyparallel.readthedocs.io/>`__ a parallel computing framework for
IPython, does this to display errors from multiple engines.

Please be conservative in using this feature; by replacing the default traceback
you may hide important information from the user.
