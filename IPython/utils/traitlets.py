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
* A full set of trait types.  Most importantly, we don't provide container
  traits (list, dict, tuple) that can trigger notifications if their
  contents change.
* API compatibility with enthought.traits

There are also some important difference in our design:

* enthought.traits does not validate default values.  We do.

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
import sys
import types
from types import (
    InstanceType, ClassType, FunctionType,
    ListType, TupleType
)

def import_item(name):
    """Import and return bar given the string foo.bar."""
    package = '.'.join(name.split('.')[0:-1])
    obj = name.split('.')[-1]
    execString = 'from %s import %s' % (package, obj)
    try:
        exec execString
    except SyntaxError:
        raise ImportError("Invalid class specification: %s" % name)
    exec 'temp = %s' % obj
    return temp


ClassTypes = (ClassType, type)

SequenceTypes = (ListType, TupleType)

#-----------------------------------------------------------------------------
# Basic classes
#-----------------------------------------------------------------------------


class NoDefaultSpecified ( object ): pass
NoDefaultSpecified = NoDefaultSpecified()


class Undefined ( object ): pass
Undefined = Undefined()

class TraitError(Exception):
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
    ['anytrait']
    """
    if isinstance(name, str):
        return [name]
    elif name is None:
        return ['anytrait']
    elif isinstance(name, (list, tuple)):
        for n in name:
            assert isinstance(n, str), "names must be strings"
        return name


class _SimpleTest:
    def __init__ ( self, value ): self.value = value
    def __call__ ( self, test  ):
        return test == self.value
    def __repr__(self):
        return "<SimpleTest(%r)" % self.value
    def __str__(self):
        return self.__repr__()


#-----------------------------------------------------------------------------
# Base TraitType for all traits
#-----------------------------------------------------------------------------


class TraitType(object):
    """A base class for all trait descriptors.

    Notes
    -----
    Our implementation of traits is based on Python's descriptor
    prototol.  This class is the base class for all such descriptors.  The
    only magic we use is a custom metaclass for the main :class:`HasTraits`
    class that does the following:

    1. Sets the :attr:`name` attribute of every :class:`TraitType`
       instance in the class dict to the name of the attribute.
    2. Sets the :attr:`this_class` attribute of every :class:`TraitType`
       instance in the class dict to the *class* that declared the trait.
       This is used by the :class:`This` trait to allow subclasses to
       accept superclasses for :class:`This` values.
    """
    

    metadata = {}
    default_value = Undefined
    info_text = 'any value'

    def __init__(self, default_value=NoDefaultSpecified, **metadata):
        """Create a TraitType.
        """
        if default_value is not NoDefaultSpecified:
            self.default_value = default_value

        if len(metadata) > 0:
            if len(self.metadata) > 0:
                self._metadata = self.metadata.copy()
                self._metadata.update(metadata)
            else:
                self._metadata = metadata
        else:
            self._metadata = self.metadata

        self.init()

    def init(self):
        pass

    def get_default_value(self):
        """Create a new instance of the default value."""
        dv = self.default_value
        return dv

    def instance_init(self, obj):
        """This is called by :meth:`HasTraits.__new__` to finish init'ing.

        Some stages of initialization must be delayed until the parent
        :class:`HasTraits` instance has been created.  This method is
        called in :meth:`HasTraits.__new__` after the instance has been
        created.

        This method trigger the creation and validation of default values
        and also things like the resolution of str given class names in 
        :class:`Type` and :class`Instance`.

        Parameters
        ----------
        obj : :class:`HasTraits` instance
            The parent :class:`HasTraits` instance that has just been
            created.
        """
        self.set_default_value(obj)

    def set_default_value(self, obj):
        """Set the default value on a per instance basis.

        This method is called by :meth:`instance_init` to create and
        validate the default value.  The creation and validation of 
        default values must be delayed until the parent :class:`HasTraits`
        class has been instantiated.
        """
        dv = self.get_default_value()
        newdv = self._validate(obj, dv)
        obj._trait_values[self.name] = newdv

    def __get__(self, obj, cls=None):
        """Get the value of the trait by self.name for the instance.

        Default values are instantiated when :meth:`HasTraits.__new__`
        is called.  Thus by the time this method gets called either the 
        default value or a user defined value (they called :meth:`__set__`)
        is in the :class:`HasTraits` instance.
        """
        if obj is None:
            return self
        else:
            try:
                value = obj._trait_values[self.name]
            except:
                # HasTraits should call set_default_value to populate
                # this.  So this should never be reached.
                raise TraitError('Unexpected error in TraitType: '
                                    'default value not set properly')
            else:
                return value

    def __set__(self, obj, value):
        new_value = self._validate(obj, value)
        old_value = self.__get__(obj)
        if old_value != new_value:
            obj._trait_values[self.name] = new_value
            obj._notify_trait(self.name, old_value, new_value)

    def _validate(self, obj, value):
        if hasattr(self, 'validate'):
            return self.validate(obj, value)
        elif hasattr(self, 'is_valid_for'):
            valid = self.is_valid_for(value)
            if valid:
                return value
            else:
                raise TraitError('invalid value for type: %r' % value)
        elif hasattr(self, 'value_for'):
            return self.value_for(value)
        else:
            return value

    def info(self):
        return self.info_text

    def error(self, obj, value):
        if obj is not None:
            e = "The '%s' trait of %s instance must be %s, but a value of %s was specified." \
                % (self.name, class_of(obj),
                   self.info(), repr_type(value))
        else:
            e = "The '%s' trait must be %s, but a value of %r was specified." \
                % (self.name, self.info(), repr_type(value))            
        raise TraitError(e)

    def get_metadata(self, key):
        return getattr(self, '_metadata', {}).get(key, None)

    def set_metadata(self, key, value):
        getattr(self, '_metadata', {})[key] = value


#-----------------------------------------------------------------------------
# The HasTraits implementation
#-----------------------------------------------------------------------------


class MetaHasTraits(type):
    """A metaclass for HasTraits.
    
    This metaclass makes sure that any TraitType class attributes are
    instantiated and sets their name attribute.
    """
    
    def __new__(mcls, name, bases, classdict):
        """Create the HasTraits class.
        
        This instantiates all TraitTypes in the class dict and sets their
        :attr:`name` attribute.
        """
        for k,v in classdict.iteritems():
            if isinstance(v, TraitType):
                v.name = k
            elif inspect.isclass(v):
                if issubclass(v, TraitType):
                    vinst = v()
                    vinst.name = k
                    classdict[k] = vinst
        return super(MetaHasTraits, mcls).__new__(mcls, name, bases, classdict)

    def __init__(cls, name, bases, classdict):
        """Finish initializing the HasTraits class.
        
        This sets the :attr:`this_class` attribute of each TraitType in the
        class dict to the newly created class ``cls``.
        """
        for k, v in classdict.iteritems():
            if isinstance(v, TraitType):
                v.this_class = cls
        super(MetaHasTraits, cls).__init__(name, bases, classdict)

class HasTraits(object):

    __metaclass__ = MetaHasTraits

    def __new__(cls, *args, **kw):
        # This is needed because in Python 2.6 object.__new__ only accepts
        # the cls argument.
        new_meth = super(HasTraits, cls).__new__
        if new_meth is object.__new__:
            inst = new_meth(cls)
        else:
            inst = new_meth(cls, *args, **kw)
        inst._trait_values = {}
        inst._trait_notifiers = {}
        # Here we tell all the TraitType instances to set their default
        # values on the instance. 
        for key in dir(cls):
            value = getattr(cls, key)
            if isinstance(value, TraitType):
                value.instance_init(inst)
        return inst

    # def __init__(self):
    #     self._trait_values = {}
    #     self._trait_notifiers = {}

    def _notify_trait(self, name, old_value, new_value):

        # First dynamic ones
        callables = self._trait_notifiers.get(name,[])
        more_callables = self._trait_notifiers.get('anytrait',[])
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
                    raise TraitError('a trait changed callback '
                                        'must have 0-3 arguments.')
            else:
                raise TraitError('a trait changed callback '
                                    'must be callable.')
                

    def _add_notifiers(self, handler, name):
        if not self._trait_notifiers.has_key(name):
            nlist = []
            self._trait_notifiers[name] = nlist
        else:
            nlist = self._trait_notifiers[name]
        if handler not in nlist:
            nlist.append(handler)

    def _remove_notifiers(self, handler, name):
        if self._trait_notifiers.has_key(name):
            nlist = self._trait_notifiers[name]
            try:
                index = nlist.index(handler)
            except ValueError:
                pass
            else:
                del nlist[index]

    def on_trait_change(self, handler, name=None, remove=False):
        """Setup a handler to be called when a trait changes.

        This is used to setup dynamic notifications of trait changes.
        
        Static handlers can be created by creating methods on a HasTraits
        subclass with the naming convention '_[traitname]_changed'.  Thus,
        to create static handler for the trait 'a', create the method
        _a_changed(self, name, old, new) (fewer arguments can be used, see
        below).
        
        Parameters
        ----------
        handler : callable
            A callable that is called when a trait changes.  Its 
            signature can be handler(), handler(name), handler(name, new)
            or handler(name, old, new).
        name : list, str, None
            If None, the handler will apply to all traits.  If a list
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

    def trait_names(self, **metadata):
        """Get a list of all the names of this classes traits."""
        return self.traits(**metadata).keys()

    def traits(self, **metadata):
        """Get a list of all the traits of this class.

        The TraitTypes returned don't know anything about the values
        that the various HasTrait's instances are holding.

        This follows the same algorithm as traits does and does not allow
        for any simple way of specifying merely that a metadata name
        exists, but has any value.  This is because get_metadata returns
        None if a metadata key doesn't exist.
        """
        traits = dict([memb for memb in inspect.getmembers(self.__class__) if \
                     isinstance(memb[1], TraitType)])

        if len(metadata) == 0:
            return traits

        for meta_name, meta_eval in metadata.items():
            if type(meta_eval) is not FunctionType:
                metadata[meta_name] = _SimpleTest(meta_eval)

        result = {}
        for name, trait in traits.items():
            for meta_name, meta_eval in metadata.items():
                if not meta_eval(trait.get_metadata(meta_name)):
                    break
            else:
                result[name] = trait

        return result

    def trait_metadata(self, traitname, key):
        """Get metadata values for trait by key."""
        try:
            trait = getattr(self.__class__, traitname)
        except AttributeError:
            raise TraitError("Class %s does not have a trait named %s" %
                                (self.__class__.__name__, traitname))
        else:
            return trait.get_metadata(key)

#-----------------------------------------------------------------------------
# Actual TraitTypes implementations/subclasses
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# TraitTypes subclasses for handling classes and instances of classes
#-----------------------------------------------------------------------------


class ClassBasedTraitType(TraitType):
    """A trait with error reporting for Type, Instance and This."""

    def error(self, obj, value):
        kind = type(value)
        if kind is InstanceType:
            msg = 'class %s' % value.__class__.__name__
        else:
            msg = '%s (i.e. %s)' % ( str( kind )[1:-1], repr( value ) )

        super(ClassBasedTraitType, self).error(obj, msg)


class Type(ClassBasedTraitType):
    """A trait whose value must be a subclass of a specified class."""

    def __init__ (self, default_value=None, klass=None, allow_none=True, **metadata ):
        """Construct a Type trait

        A Type trait specifies that its values must be subclasses of
        a particular class.

        If only ``default_value`` is given, it is used for the ``klass`` as
        well.

        Parameters
        ----------
        default_value : class, str or None
            The default value must be a subclass of klass.  If an str,
            the str must be a fully specified class name, like 'foo.bar.Bah'.
            The string is resolved into real class, when the parent 
            :class:`HasTraits` class is instantiated.
        klass : class, str, None
            Values of this trait must be a subclass of klass.  The klass
            may be specified in a string like: 'foo.bar.MyClass'.
            The string is resolved into real class, when the parent 
            :class:`HasTraits` class is instantiated.
        allow_none : boolean
            Indicates whether None is allowed as an assignable value. Even if
            ``False``, the default value may be ``None``.
        """
        if default_value is None:
            if klass is None:
                klass = object
        elif klass is None:
            klass = default_value

        if not (inspect.isclass(klass) or isinstance(klass, basestring)):
            raise TraitError("A Type trait must specify a class.")

        self.klass       = klass
        self._allow_none = allow_none

        super(Type, self).__init__(default_value, **metadata)

    def validate(self, obj, value):
        """Validates that the value is a valid object instance."""
        try:
            if issubclass(value, self.klass):
                return value
        except:
            if (value is None) and (self._allow_none):
                return value

        self.error(obj, value)

    def info(self):
        """ Returns a description of the trait."""
        if isinstance(self.klass, basestring):
            klass = self.klass
        else:
            klass = self.klass.__name__
        result = 'a subclass of ' + klass
        if self._allow_none:
            return result + ' or None'
        return result

    def instance_init(self, obj):
        self._resolve_classes()
        super(Type, self).instance_init(obj)

    def _resolve_classes(self):
        if isinstance(self.klass, basestring):
            self.klass = import_item(self.klass)
        if isinstance(self.default_value, basestring):
            self.default_value = import_item(self.default_value)

    def get_default_value(self):
        return self.default_value


class DefaultValueGenerator(object):
    """A class for generating new default value instances."""

    def __init__(self, *args, **kw):
        self.args = args
        self.kw = kw

    def generate(self, klass):
        return klass(*self.args, **self.kw)


class Instance(ClassBasedTraitType):
    """A trait whose value must be an instance of a specified class.
    
    The value can also be an instance of a subclass of the specified class.
    """

    def __init__(self, klass=None, args=None, kw=None, 
                 allow_none=True, **metadata ):
        """Construct an Instance trait.

        This trait allows values that are instances of a particular
        class or its sublclasses.  Our implementation is quite different
        from that of enthough.traits as we don't allow instances to be used
        for klass and we handle the ``args`` and ``kw`` arguments differently.

        Parameters
        ----------
        klass : class, str
            The class that forms the basis for the trait.  Class names
            can also be specified as strings, like 'foo.bar.Bar'.
        args : tuple
            Positional arguments for generating the default value.
        kw : dict
            Keyword arguments for generating the default value.
        allow_none : bool
            Indicates whether None is allowed as a value.

        Default Value
        -------------
        If both ``args`` and ``kw`` are None, then the default value is None.
        If ``args`` is a tuple and ``kw`` is a dict, then the default is
        created as ``klass(*args, **kw)``.  If either ``args`` or ``kw`` is 
        not (but not both), None is replace by ``()`` or ``{}``.
        """

        self._allow_none = allow_none

        if (klass is None) or (not (inspect.isclass(klass) or isinstance(klass, basestring))):
            raise TraitError('The klass argument must be a class'
                                ' you gave: %r' % klass)
        self.klass = klass
        
        # self.klass is a class, so handle default_value
        if args is None and kw is None:
            default_value = None
        else:
            if args is None:
                # kw is not None
                args = ()
            elif kw is None:
                # args is not None
                kw = {}
        
            if not isinstance(kw, dict):
                raise TraitError("The 'kw' argument must be a dict or None.")
            if not isinstance(args, tuple):
                raise TraitError("The 'args' argument must be a tuple or None.")
            
            default_value = DefaultValueGenerator(*args, **kw)

        super(Instance, self).__init__(default_value, **metadata)

    def validate(self, obj, value):
        if value is None:
            if self._allow_none:
                return value
            self.error(obj, value)

        if isinstance(value, self.klass):
            return value
        else:
            self.error(obj, value)

    def info(self):
        if isinstance(self.klass, basestring):
            klass = self.klass
        else:
            klass = self.klass.__name__
        result = class_of(klass)
        if self._allow_none:
            return result + ' or None'

        return result

    def instance_init(self, obj):
        self._resolve_classes()
        super(Instance, self).instance_init(obj)

    def _resolve_classes(self):
        if isinstance(self.klass, basestring):
            self.klass = import_item(self.klass)

    def get_default_value(self):
        """Instantiate a default value instance.
        
        This is called when the containing HasTraits classes'
        :meth:`__new__` method is called to ensure that a unique instance
        is created for each HasTraits instance.
        """
        dv  = self.default_value
        if isinstance(dv, DefaultValueGenerator):
            return dv.generate(self.klass)
        else:
            return dv


class This(ClassBasedTraitType):
    """A trait for instances of the class containing this trait.

    Because how how and when class bodies are executed, the ``This``
    trait can only have a default value of None.  This, and because we 
    always validate default values, ``allow_none`` is *always* true.
    """

    info_text = 'an instance of the same type as the receiver or None'

    def __init__(self, **metadata):
        super(This, self).__init__(None, **metadata)

    def validate(self, obj, value):
        # What if value is a superclass of obj.__class__?  This is
        # complicated if it was the superclass that defined the This
        # trait.
        if isinstance(value, self.this_class) or (value is None):
            return value
        else:
            self.error(obj, value)


#-----------------------------------------------------------------------------
# Basic TraitTypes implementations/subclasses
#-----------------------------------------------------------------------------


class Any(TraitType):
    default_value = None
    info_text = 'any value'


class Int(TraitType):
    """A integer trait."""

    evaluate = int
    default_value = 0
    info_text = 'an integer'

    def validate(self, obj, value):
        if isinstance(value, int):
            return value
        self.error(obj, value)

class CInt(Int):
    """A casting version of the int trait."""

    def validate(self, obj, value):
        try:
            return int(value)
        except:
            self.error(obj, value)


class Long(TraitType):
    """A long integer trait."""

    evaluate = long
    default_value = 0L
    info_text = 'a long'

    def validate(self, obj, value):
        if isinstance(value, long):
            return value
        if isinstance(value, int):
            return long(value)
        self.error(obj, value)


class CLong(Long):
    """A casting version of the long integer trait."""

    def validate(self, obj, value):
        try:
            return long(value)
        except:
            self.error(obj, value)


class Float(TraitType):
    """A float trait."""

    evaluate = float
    default_value = 0.0
    info_text = 'a float'

    def validate(self, obj, value):
        if isinstance(value, float):
            return value
        if isinstance(value, int):
            return float(value)
        self.error(obj, value)


class CFloat(Float):
    """A casting version of the float trait."""

    def validate(self, obj, value):
        try:
            return float(value)
        except:
            self.error(obj, value)

class Complex(TraitType):
    """A trait for complex numbers."""

    evaluate = complex
    default_value = 0.0 + 0.0j
    info_text = 'a complex number'

    def validate(self, obj, value):
        if isinstance(value, complex):
            return value
        if isinstance(value, (float, int)):
            return complex(value)
        self.error(obj, value)


class CComplex(Complex):
    """A casting version of the complex number trait."""

    def validate (self, obj, value):
        try:
            return complex(value)
        except:
            self.error(obj, value)


class Str(TraitType):
    """A trait for strings."""

    evaluate = lambda x: x
    default_value = ''
    info_text = 'a string'

    def validate(self, obj, value):
        if isinstance(value, str):
            return value
        self.error(obj, value)


class CStr(Str):
    """A casting version of the string trait."""

    def validate(self, obj, value):
        try:
            return str(value)
        except:
            try:
                return unicode(value)
            except:
                self.error(obj, value)


class Unicode(TraitType):
    """A trait for unicode strings."""

    evaluate = unicode
    default_value = u''
    info_text = 'a unicode string'

    def validate(self, obj, value):
        if isinstance(value, unicode):
            return value
        if isinstance(value, str):
            return unicode(value)
        self.error(obj, value)


class CUnicode(Unicode):
    """A casting version of the unicode trait."""

    def validate(self, obj, value):
        try:
            return unicode(value)
        except:
            self.error(obj, value)


class Bool(TraitType):
    """A boolean (True, False) trait."""
    evaluate = bool
    default_value = False
    info_text = 'a boolean'

    def validate(self, obj, value):
        if isinstance(value, bool):
            return value
        self.error(obj, value)


class CBool(Bool):
    """A casting version of the boolean trait."""

    def validate(self, obj, value):
        try:
            return bool(value)
        except:
            self.error(obj, value)


class Enum(TraitType):
    """An enum that whose value must be in a given sequence."""

    def __init__(self, values, default_value=None, allow_none=True, **metadata):
        self.values = values
        self._allow_none = allow_none
        super(Enum, self).__init__(default_value, **metadata)

    def validate(self, obj, value):
        if value is None:
            if self._allow_none:
                return value

        if value in self.values:
                return value
        self.error(obj, value)

    def info(self):
        """ Returns a description of the trait."""
        result = 'any of ' + repr(self.values)
        if self._allow_none:
            return result + ' or None'
        return result

class CaselessStrEnum(Enum):
    """An enum of strings that are caseless in validate."""

    def validate(self, obj, value):
        if value is None:
            if self._allow_none:
                return value

        if not isinstance(value, str):
            self.error(obj, value)

        for v in self.values:
            if v.lower() == value.lower():
                return v
        self.error(obj, value)


class List(Instance):
    """An instance of a Python list."""

    def __init__(self, default_value=None, allow_none=True, **metadata):
        """Create a list trait type from a list or tuple.

        The default value is created by doing ``list(default_value)``, 
        which creates a copy of the ``default_value``.
        """
        if default_value is None:
            args = ((),)
        elif isinstance(default_value, SequenceTypes):
            args = (default_value,)
        else:
            raise TypeError('default value of List was %s' % default_value)

        super(List,self).__init__(klass=list, args=args, 
                                  allow_none=allow_none, **metadata)
