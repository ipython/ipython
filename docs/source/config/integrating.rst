.. _integrating:

=====================================
Integrating your objects with IPython
=====================================

Tab completion
==============

To change the attributes displayed by tab-completing your object, define a
``__dir__(self)`` method for it. For more details, see the documentation of the
built-in `dir() function <http://docs.python.org/library/functions.html#dir>`_.

Rich display
============

The notebook and the Qt console can display richer representations of objects.
To use this, you can define any of a number of ``_repr_*_()`` methods. Note that
these are surrounded by single, not double underscores.

Both the notebook and the Qt console can display ``svg``, ``png`` and ``jpeg``
representations. The notebook can also display ``html``, ``javascript``,
and ``latex``. If the methods don't exist, or return ``None``, it falls
back to a standard ``repr()``.

For example::

    class Shout(object):
        def __init__(self, text):
            self.text = text
        
        def _repr_html_(self):
            return "<h1>" + self.text + "</h1>"

Custom exception tracebacks
===========================

Rarely, you might want to display a different traceback with an exception -
IPython's own parallel computing framework does this to display errors from the
engines. To do this, define a ``_render_traceback_(self)`` method which returns
a list of strings, each containing one line of the traceback.

Please be conservative in using this feature; by replacing the default traceback
you may hide important information from the user.
