#!/usr/bin/env python
# encoding: utf-8
"""
A lightweight Traits like module.

This is designed to provide a lightweight, simple, pure Python version of
many of the capabilities of enthought.traits.  This includes:

* Validation
* Type specification with defaults
* Static and dynamic notification
* Basic predefined types
* An API that is similar to enthought.traits

We don't support:

* Delegation
* Automatic GUI generation
* A full set of trait types
* API compatibility with enthought.traits

We choose to create this module because we need these capabilities, but
we need them to be pure Python so they work in all Python implementations,
including Jython and IronPython.

Authors:

* Brian Granger
* Enthought, Inc.  Some of the code in this file comes from enthought.traits
  and is licensed under the BSD license.  Also, many of the ideas also come
  from enthought.traits even though our implementation is very different.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import inspect
import types
from types import InstanceType

#-----------------------------------------------------------------------------
# Basic classes
#-----------------------------------------------------------------------------


class NoDefaultSpecified ( object ): pass
NoDefaultSpecified = NoDefaultSpecified()


class Undefined ( object ): pass
Undefined = Undefined()


class TraitletError(Exception):
    pass


#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------


def class_of ( object ):
    """ Returns a string containing the class name of an object with the
    correct indefinite article ('a' or 'an') preceding it (e.g., 'an Image',
    'a PlotValue').
    """
    if isinstance( object, basestring ):
        return add_article( object )

    return add_article( object.__class__.__name__ )


def add_article ( name ):
    """ Returns a string containing the correct indefinite article ('a' or 'an')
    prefixed to the specified string.
    """
    if name[:1].lower() in 'aeiou':
       return 'an ' + name

    return 'a ' + name


def repr_type(obj):
    """ Return a string representation of a value and its type for readable
    error messages.
    """
    the_type = type(obj)
    if the_type is InstanceType:
        # Old-style class.
        the_type = obj.__class__
    msg = '%r %r' % (obj, the_type)
    return msg


def parse_notifier_name(name):
    """Convert the name argument to a list of names.
    
    Examples
    --------
    
    >>> parse_notifier_name('a')
    ['a']
    >>> parse_notifier_name(['a','b'])
    ['a', 'b']
    >>> parse_notifier_name(None)
    ['anytraitlet']
    """
    if isinstance(name, str):
        return [name]
    elif name is None:
        return ['anytraitlet']
    elif isinstance(name, (list, tuple)):
        for n in name:
            assert isinstance(n, str), "names must be strings"
        return name


#-----------------------------------------------------------------------------
# Base TraitletType for all traitlets
#-----------------------------------------------------------------------------


class TraitletType(object):

    metadata = {}
    default_value = None
    info_text = 'any value'

    def __init__(self, default_value=NoDefaultSpecified, **metadata):
        if default_value is not NoDefaultSpecified:
            self.default_value = default_value
        self.metadata.update(metadata)

    def __get__(self, inst, cls=None):
        if inst is None:
            return self
        else:
            return inst._traitlet_values.get(self.name, self.default_value)

    def __set__(self, inst, value):
        new_value = self._validate(inst, value)
        old_value = self.__get__(inst)
        if old_value != new_value:
            inst._traitlet_values[self.name] = new_value
            inst._notify(self.name, old_value, new_value)

    def _validate(self, inst, value):
        if hasattr(self, 'validate'):
            return self.validate(inst, value)
        elif hasattr(self, 'is_valid_for'):
            valid = self.is_valid_for(value)
            if valid:
                return value
            else:
                raise TraitletError('invalid value for type: %r' % value)
        elif hasattr(self, 'value_for'):
            return self.value_for(value)
        else:
            return value

    def info(self):
        return self.info_text

    def error(self, obj, value):
        if obj is not None:
            e = "The '%s' traitlet of %s instance must be %s, but a value of %s was specified." \
                % (self.name, class_of(obj),
                   self.info(), repr_type(value))
        else:
            e = "The '%s' traitlet must be %s, but a value of %r was specified." \
                % (self.name, self.info(), repr_type(value))            
        raise TraitletError(e)


#-----------------------------------------------------------------------------
# The HasTraitlets implementation
#-----------------------------------------------------------------------------


class MetaHasTraitlets(type):
    """A metaclass for HasTraitlets.
    
    This metaclass makes sure that any TraitletType class attributes are
    instantiated and sets their name attribute.
    """
    
    def __new__(mcls, name, bases, classdict):
        for k,v in classdict.iteritems():
            if isinstance(v, TraitletType):
                v.name = k
            elif inspect.isclass(v):
                if issubclass(v, TraitletType):
                    vinst = v()
                    vinst.name = k
                    classdict[k] = vinst
        return super(MetaHasTraitlets, mcls).__new__(mcls, name, bases, classdict)


class HasTraitlets(object):

    __metaclass__ = MetaHasTraitlets

    def __init__(self):
        self._traitlet_values = {}
        self._traitlet_notifiers = {}

    def _notify(self, name, old_value, new_value):

        # First dynamic ones
        callables = self._traitlet_notifiers.get(name,[])
        more_callables = self._traitlet_notifiers.get('anytraitlet',[])
        callables.extend(more_callables)

        # Now static ones
        try:
            cb = getattr(self, '_%s_changed' % name)
        except:
            pass
        else:
            callables.append(cb)

        # Call them all now
        for c in callables:
            # Traits catches and logs errors here.  I allow them to raise
            if callable(c):
                argspec = inspect.getargspec(c)
                nargs = len(argspec[0])
                # Bound methods have an additional 'self' argument
                # I don't know how to treat unbound methods, but they
                # can't really be used for callbacks.
                if isinstance(c, types.MethodType):
                    offset = -1
                else:
                    offset = 0
                if nargs + offset == 0:
                    c()
                elif nargs + offset == 1:
                    c(name)
                elif nargs + offset == 2:
                    c(name, new_value)
                elif nargs + offset == 3:
                    c(name, old_value, new_value)
                else:
                    raise TraitletError('a traitlet changed callback '
                                        'must have 0-3 arguments.')
            else:
                raise TraitletError('a traitlet changed callback '
                                    'must be callable.')
                

    def _add_notifiers(self, handler, name):
        if not self._traitlet_notifiers.has_key(name):
            nlist = []
            self._traitlet_notifiers[name] = nlist
        else:
            nlist = self._traitlet_notifiers[name]
        if handler not in nlist:
            nlist.append(handler)

    def _remove_notifiers(self, handler, name):
        if self._traitlet_notifiers.has_key(name):
            nlist = self._traitlet_notifiers[name]
            try:
                index = nlist.index(handler)
            except ValueError:
                pass
            else:
                del nlist[index]

    def on_traitlet_change(self, handler, name=None, remove=False):
        """Setup a handler to be called when a traitlet changes.

        This is used to setup dynamic notifications of traitlet changes.
        
        Static handlers can be created by creating methods on a HasTraitlets
        subclass with the naming convention '_[traitletname]_changed'.  Thus,
        to create static handler for the traitlet 'a', create the method
        _a_changed(self, name, old, new) (fewer arguments can be used, see
        below).
        
        Parameters
        ----------
            handler : callable
                A callable that is called when a traitlet changes.  Its 
                signature can be handler(), handler(name), handler(name, new)
                or handler(name, old, new).
            name : list, str, None
                If None, the handler will apply to all traitlets.  If a list
                of str, handler will apply to all names in the list.  If a
                str, the handler will apply just to that name.
            remove : bool
                If False (the default), then install the handler.  If True
                then unintall it.
        """
        if remove:
            names = parse_notifier_name(name)
            for n in names:
                self._remove_notifiers(handler, n)
        else:
            names = parse_notifier_name(name)
            for n in names:
                self._add_notifiers(handler, n)

    def _add_class_traitlet(self, name, traitlet):
        """Add a class-level traitlet.

        This create a new traitlet attached to all instances of this class.
        But, the value can be different on each instance.  But, this behavior
        is likely to trip up many folks as they would expect the traitlet
        type to be different on each instance.

        Parameters
        ----------
        name : str
            The name of the traitlet.
        traitlet : TraitletType or an instance of one
            The traitlet to assign to the name.
        """
        if inspect.isclass(traitlet):
            inst = traitlet()
        else:
            inst = traitlet
        assert isinstance(inst, TraitletType)
        inst.name = name
        setattr(self.__class__, name, inst)

#-----------------------------------------------------------------------------
# Actual TraitletTypes implementations/subclasses
#-----------------------------------------------------------------------------


class Any(TraitletType):
    default_value = None
    info_text = 'any value'


class Int(TraitletType):

    evaluate = int
    default_value = 0
    info_text = 'an integer'

    def validate(self, obj, value):
        if isinstance(value, int):
            return value
        self.error(obj, value)


class Long(TraitletType):

    evaluate = long
    default_value = 0L
    info_text = 'a long'

    def validate(self, obj, value):
        if isinstance(value, long):
            return value
        if isinstance(value, int):
            return long(value)
        self.error(obj, value)


class Float(TraitletType):

    evaluate = float
    default_value = 0.0
    info_text = 'a float'

    def validate(self, obj, value):
        if isinstance(value, float):
            return value
        if isinstance(value, int):
            return float(value)
        self.error(obj, value)


class Complex(TraitletType):

    evaluate = complex
    default_value = 0.0 + 0.0j
    info_text = 'a complex number'

    def validate(self, obj, value):
        if isinstance(value, complex):
            return value
        if isinstance(value, (float, int)):
            return complex(value)
        self.error(obj, value)


class Str(TraitletType):

    evaluate = lambda x: x
    default_value = ''
    info_text = 'a string'

    def validate(self, obj, value):
        if isinstance(value, str):
            return value
        self.error(obj, value)


class Unicode(TraitletType):

    evaluate = unicode
    default_value = u''
    info_text = 'a unicode string'

    def validate(self, obj, value):
        if isinstance(value, unicode):
            return value
        if isinstance(value, str):
            return unicode(value)
        self.error(obj, value)


class Bool(TraitletType):

    evaluate = bool
    default_value = False
    info_text = 'a boolean'

    def validate(self, obj, value):
        if isinstance(value, bool):
            return value
        self.error(obj, value)

