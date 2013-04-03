# -*- coding: utf-8 -*-
"""Display formatters.

Inheritance diagram:

.. inheritance-diagram:: IPython.core.formatters
   :parts: 3

Authors:

* Robert Kern
* Brian Granger
"""
#-----------------------------------------------------------------------------
# Copyright (C) 2010-2011, IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Stdlib imports
import abc
import sys
import warnings
# We must use StringIO, as cStringIO doesn't handle unicode properly.
from StringIO import StringIO

# Our own imports
from IPython.config.configurable import Configurable
from IPython.lib import pretty
from IPython.utils.traitlets import (
    Bool, Dict, Integer, Unicode, CUnicode, ObjectName, List,
)
from IPython.utils.py3compat import unicode_to_str


#-----------------------------------------------------------------------------
# The main DisplayFormatter class
#-----------------------------------------------------------------------------


class DisplayFormatter(Configurable):

    # When set to true only the default plain text formatter will be used.
    plain_text_only = Bool(False, config=True)
    def _plain_text_only_changed(self, name, old, new):
        warnings.warn("""DisplayFormatter.plain_text_only is deprecated.
        
        Use DisplayFormatter.active_types = ['text/plain']
        for the same effect.
        """, DeprecationWarning)
        if new:
            self.active_types = ['text/plain']
        else:
            self.active_types = self.format_types
    
    active_types = List(Unicode, config=True,
        help="""List of currently active mime-types""")
    def _active_types_default(self):
        return self.format_types
    
    def _active_types_changed(self, name, old, new):
        for key, formatter in self.formatters.keys():
            if key in new:
                formatter.enabled = True
            else:
                formatter.enabled = False
    
    # A dict of formatter whose keys are format types (MIME types) and whose
    # values are subclasses of BaseFormatter.
    formatters = Dict()
    def _formatters_default(self):
        """Activate the default formatters."""
        formatter_classes = [
            PlainTextFormatter,
            HTMLFormatter,
            SVGFormatter,
            PNGFormatter,
            JPEGFormatter,
            LatexFormatter,
            JSONFormatter,
            JavascriptFormatter
        ]
        d = {}
        for cls in formatter_classes:
            f = cls(config=self.config)
            d[f.format_type] = f
        return d

    def format(self, obj, include=None, exclude=None):
        """Return a format data dict for an object.

        By default all format types will be computed.

        The following MIME types are currently implemented:

        * text/plain
        * text/html
        * text/latex
        * application/json
        * application/javascript
        * image/png
        * image/jpeg
        * image/svg+xml

        Parameters
        ----------
        obj : object
            The Python object whose format data will be computed.
        include : list or tuple, optional
            A list of format type strings (MIME types) to include in the
            format data dict. If this is set *only* the format types included
            in this list will be computed.
        exclude : list or tuple, optional
            A list of format type string (MIME types) to exclude in the format
            data dict. If this is set all format types will be computed,
            except for those included in this argument.

        Returns
        -------
        format_dict : dict
            A dictionary of key/value pairs, one or each format that was
            generated for the object. The keys are the format types, which
            will usually be MIME type strings and the values and JSON'able
            data structure containing the raw data for the representation in
            that format.
        """
        format_dict = {}

        for format_type, formatter in self.formatters.items():
            if include and format_type not in include:
                continue
            if exclude and format_type in exclude:
                continue
            try:
                data = formatter(obj)
            except:
                # FIXME: log the exception
                raise
            if data is not None:
                format_dict[format_type] = data
        return format_dict

    @property
    def format_types(self):
        """Return the format types (MIME types) of the active formatters."""
        return self.formatters.keys()


#-----------------------------------------------------------------------------
# Formatters for specific format types (text, html, svg, etc.)
#-----------------------------------------------------------------------------


class FormatterABC(object):
    """ Abstract base class for Formatters.

    A formatter is a callable class that is responsible for computing the
    raw format data for a particular format type (MIME type). For example,
    an HTML formatter would have a format type of `text/html` and would return
    the HTML representation of the object when called.
    """
    __metaclass__ = abc.ABCMeta

    # The format type of the data returned, usually a MIME type.
    format_type = 'text/plain'

    # Is the formatter enabled...
    enabled = True

    @abc.abstractmethod
    def __call__(self, obj):
        """Return a JSON'able representation of the object.

        If the object cannot be formatted by this formatter, then return None
        """
        try:
            return repr(obj)
        except TypeError:
            return None


class BaseFormatter(Configurable):
    """A base formatter class that is configurable.

    This formatter should usually be used as the base class of all formatters.
    It is a traited :class:`Configurable` class and includes an extensible
    API for users to determine how their objects are formatted. The following
    logic is used to find a function to format an given object.

    1. The object is introspected to see if it has a method with the name
       :attr:`print_method`. If is does, that object is passed to that method
       for formatting.
    2. If no print method is found, three internal dictionaries are consulted
       to find print method: :attr:`singleton_printers`, :attr:`type_printers`
       and :attr:`deferred_printers`.

    Users should use these dictionaries to register functions that will be
    used to compute the format data for their objects (if those objects don't
    have the special print methods). The easiest way of using these
    dictionaries is through the :meth:`for_type` and :meth:`for_type_by_name`
    methods.

    If no function/callable is found to compute the format data, ``None`` is
    returned and this format type is not used.
    """

    format_type = Unicode('text/plain')

    enabled = Bool(True, config=True)

    print_method = ObjectName('__repr__')

    # The singleton printers.
    # Maps the IDs of the builtin singleton objects to the format functions.
    singleton_printers = Dict(config=True)
    def _singleton_printers_default(self):
        return {}

    # The type-specific printers.
    # Map type objects to the format functions.
    type_printers = Dict(config=True)
    def _type_printers_default(self):
        return {}

    # The deferred-import type-specific printers.
    # Map (modulename, classname) pairs to the format functions.
    deferred_printers = Dict(config=True)
    def _deferred_printers_default(self):
        return {}

    def __call__(self, obj):
        """Compute the format for an object."""
        if self.enabled:
            obj_id = id(obj)
            try:
                obj_class = getattr(obj, '__class__', None) or type(obj)
                # First try to find registered singleton printers for the type.
                try:
                    printer = self.singleton_printers[obj_id]
                except (TypeError, KeyError):
                    pass
                else:
                    return printer(obj)
                # Next look for type_printers.
                for cls in pretty._get_mro(obj_class):
                    if cls in self.type_printers:
                        return self.type_printers[cls](obj)
                    else:
                        printer = self._in_deferred_types(cls)
                        if printer is not None:
                            return printer(obj)
                # Finally look for special method names.
                if hasattr(obj_class, self.print_method):
                    printer = getattr(obj_class, self.print_method)
                    return printer(obj)
                return None
            except Exception:
                pass
        else:
            return None

    def for_type(self, typ, func):
        """Add a format function for a given type.

        Parameters
        -----------
        typ : class
            The class of the object that will be formatted using `func`.
        func : callable
            The callable that will be called to compute the format data. The
            call signature of this function is simple, it must take the
            object to be formatted and return the raw data for the given
            format. Subclasses may use a different call signature for the
            `func` argument.
        """
        oldfunc = self.type_printers.get(typ, None)
        if func is not None:
            # To support easy restoration of old printers, we need to ignore
            # Nones.
            self.type_printers[typ] = func
        return oldfunc

    def for_type_by_name(self, type_module, type_name, func):
        """Add a format function for a type specified by the full dotted
        module and name of the type, rather than the type of the object.

        Parameters
        ----------
        type_module : str
            The full dotted name of the module the type is defined in, like
            ``numpy``.
        type_name : str
            The name of the type (the class name), like ``dtype``
        func : callable
            The callable that will be called to compute the format data. The
            call signature of this function is simple, it must take the
            object to be formatted and return the raw data for the given
            format. Subclasses may use a different call signature for the
            `func` argument.
        """
        key = (type_module, type_name)
        oldfunc = self.deferred_printers.get(key, None)
        if func is not None:
            # To support easy restoration of old printers, we need to ignore
            # Nones.
            self.deferred_printers[key] = func
        return oldfunc

    def _in_deferred_types(self, cls):
        """
        Check if the given class is specified in the deferred type registry.

        Returns the printer from the registry if it exists, and None if the
        class is not in the registry. Successful matches will be moved to the
        regular type registry for future use.
        """
        mod = getattr(cls, '__module__', None)
        name = getattr(cls, '__name__', None)
        key = (mod, name)
        printer = None
        if key in self.deferred_printers:
            # Move the printer over to the regular registry.
            printer = self.deferred_printers.pop(key)
            self.type_printers[cls] = printer
        return printer


class PlainTextFormatter(BaseFormatter):
    """The default pretty-printer.

    This uses :mod:`IPython.lib.pretty` to compute the format data of
    the object. If the object cannot be pretty printed, :func:`repr` is used.
    See the documentation of :mod:`IPython.lib.pretty` for details on
    how to write pretty printers.  Here is a simple example::

        def dtype_pprinter(obj, p, cycle):
            if cycle:
                return p.text('dtype(...)')
            if hasattr(obj, 'fields'):
                if obj.fields is None:
                    p.text(repr(obj))
                else:
                    p.begin_group(7, 'dtype([')
                    for i, field in enumerate(obj.descr):
                        if i > 0:
                            p.text(',')
                            p.breakable()
                        p.pretty(field)
                    p.end_group(7, '])')
    """

    # The format type of data returned.
    format_type = Unicode('text/plain')

    # This subclass ignores this attribute as it always need to return
    # something.
    enabled = Bool(True, config=False)

    # Look for a _repr_pretty_ methods to use for pretty printing.
    print_method = ObjectName('_repr_pretty_')

    # Whether to pretty-print or not.
    pprint = Bool(True, config=True)

    # Whether to be verbose or not.
    verbose = Bool(False, config=True)

    # The maximum width.
    max_width = Integer(79, config=True)

    # The newline character.
    newline = Unicode('\n', config=True)

    # format-string for pprinting floats
    float_format = Unicode('%r')
    # setter for float precision, either int or direct format-string
    float_precision = CUnicode('', config=True)

    def _float_precision_changed(self, name, old, new):
        """float_precision changed, set float_format accordingly.

        float_precision can be set by int or str.
        This will set float_format, after interpreting input.
        If numpy has been imported, numpy print precision will also be set.

        integer `n` sets format to '%.nf', otherwise, format set directly.

        An empty string returns to defaults (repr for float, 8 for numpy).

        This parameter can be set via the '%precision' magic.
        """

        if '%' in new:
            # got explicit format string
            fmt = new
            try:
                fmt%3.14159
            except Exception:
                raise ValueError("Precision must be int or format string, not %r"%new)
        elif new:
            # otherwise, should be an int
            try:
                i = int(new)
                assert i >= 0
            except ValueError:
                raise ValueError("Precision must be int or format string, not %r"%new)
            except AssertionError:
                raise ValueError("int precision must be non-negative, not %r"%i)

            fmt = '%%.%if'%i
            if 'numpy' in sys.modules:
                # set numpy precision if it has been imported
                import numpy
                numpy.set_printoptions(precision=i)
        else:
            # default back to repr
            fmt = '%r'
            if 'numpy' in sys.modules:
                import numpy
                # numpy default is 8
                numpy.set_printoptions(precision=8)
        self.float_format = fmt

    # Use the default pretty printers from IPython.lib.pretty.
    def _singleton_printers_default(self):
        return pretty._singleton_pprinters.copy()

    def _type_printers_default(self):
        d = pretty._type_pprinters.copy()
        d[float] = lambda obj,p,cycle: p.text(self.float_format%obj)
        return d

    def _deferred_printers_default(self):
        return pretty._deferred_type_pprinters.copy()

    #### FormatterABC interface ####

    def __call__(self, obj):
        """Compute the pretty representation of the object."""
        if not self.pprint:
            try:
                return repr(obj)
            except TypeError:
                return ''
        else:
            # This uses use StringIO, as cStringIO doesn't handle unicode.
            stream = StringIO()
            # self.newline.encode() is a quick fix for issue gh-597. We need to
            # ensure that stream does not get a mix of unicode and bytestrings,
            # or it will cause trouble.
            printer = pretty.RepresentationPrinter(stream, self.verbose,
                self.max_width, unicode_to_str(self.newline),
                singleton_pprinters=self.singleton_printers,
                type_pprinters=self.type_printers,
                deferred_pprinters=self.deferred_printers)
            printer.pretty(obj)
            printer.flush()
            return stream.getvalue()


class HTMLFormatter(BaseFormatter):
    """An HTML formatter.

    To define the callables that compute the HTML representation of your
    objects, define a :meth:`_repr_html_` method or use the :meth:`for_type`
    or :meth:`for_type_by_name` methods to register functions that handle
    this.

    The return value of this formatter should be a valid HTML snippet that
    could be injected into an existing DOM. It should *not* include the
    ```<html>`` or ```<body>`` tags.
    """
    format_type = Unicode('text/html')

    print_method = ObjectName('_repr_html_')


class SVGFormatter(BaseFormatter):
    """An SVG formatter.

    To define the callables that compute the SVG representation of your
    objects, define a :meth:`_repr_svg_` method or use the :meth:`for_type`
    or :meth:`for_type_by_name` methods to register functions that handle
    this.

    The return value of this formatter should be valid SVG enclosed in
    ```<svg>``` tags, that could be injected into an existing DOM. It should
    *not* include the ```<html>`` or ```<body>`` tags.
    """
    format_type = Unicode('image/svg+xml')

    print_method = ObjectName('_repr_svg_')


class PNGFormatter(BaseFormatter):
    """A PNG formatter.

    To define the callables that compute the PNG representation of your
    objects, define a :meth:`_repr_png_` method or use the :meth:`for_type`
    or :meth:`for_type_by_name` methods to register functions that handle
    this.

    The return value of this formatter should be raw PNG data, *not*
    base64 encoded.
    """
    format_type = Unicode('image/png')

    print_method = ObjectName('_repr_png_')


class JPEGFormatter(BaseFormatter):
    """A JPEG formatter.

    To define the callables that compute the JPEG representation of your
    objects, define a :meth:`_repr_jpeg_` method or use the :meth:`for_type`
    or :meth:`for_type_by_name` methods to register functions that handle
    this.

    The return value of this formatter should be raw JPEG data, *not*
    base64 encoded.
    """
    format_type = Unicode('image/jpeg')

    print_method = ObjectName('_repr_jpeg_')


class LatexFormatter(BaseFormatter):
    """A LaTeX formatter.

    To define the callables that compute the LaTeX representation of your
    objects, define a :meth:`_repr_latex_` method or use the :meth:`for_type`
    or :meth:`for_type_by_name` methods to register functions that handle
    this.

    The return value of this formatter should be a valid LaTeX equation,
    enclosed in either ```$```, ```$$``` or another LaTeX equation
    environment.
    """
    format_type = Unicode('text/latex')

    print_method = ObjectName('_repr_latex_')


class JSONFormatter(BaseFormatter):
    """A JSON string formatter.

    To define the callables that compute the JSON string representation of
    your objects, define a :meth:`_repr_json_` method or use the :meth:`for_type`
    or :meth:`for_type_by_name` methods to register functions that handle
    this.

    The return value of this formatter should be a valid JSON string.
    """
    format_type = Unicode('application/json')

    print_method = ObjectName('_repr_json_')


class JavascriptFormatter(BaseFormatter):
    """A Javascript formatter.

    To define the callables that compute the Javascript representation of
    your objects, define a :meth:`_repr_javascript_` method or use the
    :meth:`for_type` or :meth:`for_type_by_name` methods to register functions
    that handle this.

    The return value of this formatter should be valid Javascript code and
    should *not* be enclosed in ```<script>``` tags.
    """
    format_type = Unicode('application/javascript')

    print_method = ObjectName('_repr_javascript_')

FormatterABC.register(BaseFormatter)
FormatterABC.register(PlainTextFormatter)
FormatterABC.register(HTMLFormatter)
FormatterABC.register(SVGFormatter)
FormatterABC.register(PNGFormatter)
FormatterABC.register(JPEGFormatter)
FormatterABC.register(LatexFormatter)
FormatterABC.register(JSONFormatter)
FormatterABC.register(JavascriptFormatter)


def format_display_data(obj, include=None, exclude=None):
    """Return a format data dict for an object.

    By default all format types will be computed.

    The following MIME types are currently implemented:

    * text/plain
    * text/html
    * text/latex
    * application/json
    * application/javascript
    * image/png
    * image/jpeg
    * image/svg+xml

    Parameters
    ----------
    obj : object
        The Python object whose format data will be computed.

    Returns
    -------
    format_dict : dict
        A dictionary of key/value pairs, one or each format that was
        generated for the object. The keys are the format types, which
        will usually be MIME type strings and the values and JSON'able
        data structure containing the raw data for the representation in
        that format.
    include : list or tuple, optional
        A list of format type strings (MIME types) to include in the
        format data dict. If this is set *only* the format types included
        in this list will be computed.
    exclude : list or tuple, optional
        A list of format type string (MIME types) to exclue in the format
        data dict. If this is set all format types will be computed,
        except for those included in this argument.
    """
    from IPython.core.interactiveshell import InteractiveShell

    InteractiveShell.instance().display_formatter.format(
        obj,
        include,
        exclude
    )

