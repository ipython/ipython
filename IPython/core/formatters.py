# -*- coding: utf-8 -*-
"""Displayhook formatters.

Authors:

* Robert Kern
"""

import abc
from cStringIO import StringIO

from IPython.config.configurable import Configurable
from IPython.external import pretty
from IPython.utils.traitlets import Bool, Dict, Int, Str


class DefaultFormatter(Configurable):
    """ The default pretty-printer.
    """

    # The ID of the formatter.
    id = Str('default')

    # The kind of data returned.
    format = Str('text')

    # Whether to pretty-print or not.
    pprint = Bool(True)

    # Whether to be verbose or not.
    verbose = Bool(False)

    # The maximum width.
    max_width = Int(79)

    # The newline character.
    newline = Str('\n')

    # The singleton prettyprinters.
    # Maps the IDs of the builtin singleton objects to the format functions.
    singleton_pprinters = Dict()
    def _singleton_pprinters_default(self):
        return pretty._singleton_pprinters.copy()

    # The type-specific prettyprinters.
    # Map type objects to the format functions.
    type_pprinters = Dict()
    def _type_pprinters_default(self):
        return pretty._type_pprinters.copy()

    # The deferred-import type-specific prettyprinters.
    # Map (modulename, classname) pairs to the format functions.
    deferred_pprinters = Dict()
    def _deferred_pprinters_default(self):
        return pretty._deferred_type_pprinters.copy()

    #### FormatterABC interface ####

    def __call__(self, obj):
        """ Format the object.
        """
        if not self.pprint:
            r = repr(obj)
            if r is None:
                # It can happen.
                r = ''
            return r
        else:
            stream = StringIO()
            printer = pretty.RepresentationPrinter(stream, self.verbose,
                self.max_width, self.newline,
                singleton_pprinters=self.singleton_pprinters,
                type_pprinters=self.type_pprinters,
                deferred_pprinters=self.deferred_pprinters)
            printer.pretty(obj)
            printer.flush()
            return stream.getvalue()


    #### DefaultFormatter interface ####

    def for_type(self, typ, func):
        """
        Add a pretty printer for a given type.
        """
        oldfunc = self.type_pprinters.get(typ, None)
        if func is not None:
            # To support easy restoration of old pprinters, we need to ignore
            # Nones.
            self.type_pprinters[typ] = func
        return oldfunc

    def for_type_by_name(self, type_module, type_name, func):
        """
        Add a pretty printer for a type specified by the module and name of
        a type rather than the type object itself.
        """
        key = (type_module, type_name)
        oldfunc = self.deferred_pprinters.get(key, None)
        if func is not None:
            # To support easy restoration of old pprinters, we need to ignore
            # Nones.
            self.deferred_pprinters[key] = func
        return oldfunc


class FormatterABC(object):
    """ Abstract base class for Formatters.
    """
    __metaclass__ = abc.ABCMeta

    # The ID of the formatter.
    id = 'abstract'

    # The kind of data returned.
    format = 'text'

    @abc.abstractmethod
    def __call__(self, obj):
        """ Return a JSONable representation of the object.
        """
        return repr(obj)

FormatterABC.register(DefaultFormatter)
