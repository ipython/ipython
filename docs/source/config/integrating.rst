.. _integrating:

=====================================
Integrating your objects with IPython
=====================================

Tab completion
==============

To change the attributes displayed by tab-completing your object, define a
``__dir__(self)`` method for it. For more details, see the documentation of the
built-in :external+python:py:func:`dir`

You can also customise key completions for your objects, e.g. pressing tab after
``obj["a``. To do so, define a method ``_ipython_key_completions_()``, which
returns a list of objects which are possible keys in a subscript expression
``obj[key]``.

.. versionadded:: 5.0
   Custom key completions

.. _integrating_rich_display:

Rich display
============

Custom methods
--------------

IPython can display richer representations of objects.
To do this, you can define ``_ipython_display_()``, or any of a number of
``_repr_*_()`` methods.
Note that these are surrounded by single, not double underscores.


.. list-table:: Supported ``_repr_*_`` methods
   :widths: 20 15 15 15
   :header-rows: 1

   * - Format
     - REPL
     - Notebook
     - Qt Console
   * - ``_repr_pretty_``
     - yes
     - yes
     - yes
   * - ``_repr_svg_``
     - no
     - yes
     - yes
   * - ``_repr_png_``
     - no
     - yes
     - yes
   * - ``_repr_jpeg_``
     - no
     - yes
     - yes
   * - ``_repr_html_``
     - no
     - yes
     - no
   * - ``_repr_javascript_``
     - no
     - yes
     - no
   * - ``_repr_markdown_``
     - no
     - yes
     - no
   * - ``_repr_latex_``
     - no
     - yes
     - no
   * - ``_repr_mimebundle_``
     - no
     - ?
     - ?

If the methods don't exist, the standard ``repr()`` is used.
If a method exists and returns ``None``, it is treated the same as if it does not exist.
In general, *all* available formatters will be called when an object is displayed,
and it is up to the UI to select which to display.
A given formatter should not generally change its output based on what other formats are available -
that should be handled at a different level, such as the :class:`~.DisplayFormatter`, or configuration.

``_repr_*_`` methods should *return* data of the expected format and have no side effects.
For example, ``_repr_html_`` should return HTML as a `str` and ``_repr_png_`` should return PNG data as `bytes`.

If you wish to take control of display via your own side effects, use ``_ipython_display_()``.

For example::

    class Shout(object):
        def __init__(self, text):
            self.text = text

        def _repr_html_(self):
            return "<h1>" + self.text + "</h1>"


Special methods
^^^^^^^^^^^^^^^

Pretty printing
"""""""""""""""

To customize how your object is pretty-printed, add a ``_repr_pretty_`` method
to the class.
The method should accept a pretty printer, and a boolean that indicates whether
the printer detected a cycle.
The method should act on the printer to produce your customized pretty output.
Here is an example::

    class MyObject(object):

        def _repr_pretty_(self, p, cycle):
            if cycle:
                p.text('MyObject(...)')
            else:
                p.text('MyObject[...]')

For details on how to use the pretty printer, see :py:mod:`IPython.lib.pretty`.

More powerful methods
"""""""""""""""""""""

.. class:: MyObject

   .. method:: _repr_mimebundle_(include=None, exclude=None)

     Should return a dictionary of multiple formats, keyed by mimetype, or a tuple
     of two dictionaries: *data, metadata* (see :ref:`Metadata`).
     If this returns something, other ``_repr_*_`` methods are ignored.
     The method should take keyword arguments ``include`` and ``exclude``, though
     it is not required to respect them.

   .. method:: _ipython_display_()

      Displays the object as a side effect; the return value is ignored. If this
      is defined, all other display methods are ignored.


Metadata
^^^^^^^^

We often want to provide frontends with guidance on how to display the data. To
support this, ``_repr_*_()`` methods (except ``_repr_pretty_``?) can also return a ``(data, metadata)``
tuple where ``metadata`` is a dictionary containing arbitrary key-value pairs for
the frontend to interpret. An example use case is ``_repr_jpeg_()``, which can
be set to return a jpeg image and a ``{'height': 400, 'width': 600}`` dictionary
to inform the frontend how to size the image.



.. _third_party_formatting:

Formatters for third-party types
--------------------------------

The user can also register formatters for types without modifying the class::

    from bar.baz import Foo

    def foo_html(obj):
        return '<marquee>Foo object %s</marquee>' % obj.name

    html_formatter = get_ipython().display_formatter.formatters['text/html']
    html_formatter.for_type(Foo, foo_html)

    # Or register a type without importing it - this does the same as above:
    html_formatter.for_type_by_name('bar.baz', 'Foo', foo_html)

Custom exception tracebacks
===========================

Rarely, you might want to display a custom traceback when reporting an
exception. To do this, define the custom traceback using
`_render_traceback_(self)` method which returns a list of strings, one string
for each line of the traceback. For example, the `ipyparallel
<https://ipyparallel.readthedocs.io/>`__ a parallel computing framework for
IPython, does this to display errors from multiple engines.

Please be conservative in using this feature; by replacing the default traceback
you may hide important information from the user.
