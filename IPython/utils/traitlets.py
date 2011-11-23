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
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------


import inspect
import re
import sys
import types
from types import FunctionType
try:
    from types import ClassType, InstanceType
    ClassTypes = (ClassType, type)
except:
    ClassTypes = (type,)

from .importstring import import_item
from IPython.utils import py3compat

SequenceTypes = (list, tuple, set, frozenset)

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
    if (not py3compat.PY3) and the_type is InstanceType:
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


def getmembers(object, predicate=None):
    """A safe version of inspect.getmembers that handles missing attributes.

    This is useful when there are descriptor based attributes that for
    some reason raise AttributeError even though they exist.  This happens
    in zope.inteface with the __provides__ attribute.
    """
    results = []
    for key in dir(object):
        try:
            value = getattr(object, key)
        except AttributeError:
            pass
        else:
            if not predicate or predicate(value):
                results.append((key, value))
    results.sort()
    return results


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
        return self.default_value

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
        # Check for a deferred initializer defined in the same class as the
        # trait declaration or above.
        mro = type(obj).mro()
        meth_name = '_%s_default' % self.name
        for cls in mro[:mro.index(self.this_class)+1]:
            if meth_name in cls.__dict__:
                break
        else:
            # We didn't find one. Do static initialization.
            dv = self.get_default_value()
            newdv = self._validate(obj, dv)
            obj._trait_values[self.name] = newdv
            return
        # Complete the dynamic initialization.
        obj._trait_dyn_inits[self.name] = cls.__dict__[meth_name]

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
            except KeyError:
                # Check for a dynamic initializer.
                if self.name in obj._trait_dyn_inits:
                    value = obj._trait_dyn_inits[self.name](obj)
                    # FIXME: Do we really validate here?
                    value = self._validate(obj, value)
                    obj._trait_values[self.name] = value
                    return value
                else:
                    raise TraitError('Unexpected error in TraitType: '
                        'both default value and dynamic initializer are '
                        'absent.')
            except Exception:
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
        # print "MetaHasTraitlets (mcls, name): ", mcls, name
        # print "MetaHasTraitlets (bases): ", bases
        # print "MetaHasTraitlets (classdict): ", classdict
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

    def __new__(cls, **kw):
        # This is needed because in Python 2.6 object.__new__ only accepts
        # the cls argument.
        new_meth = super(HasTraits, cls).__new__
        if new_meth is object.__new__:
            inst = new_meth(cls)
        else:
            inst = new_meth(cls, **kw)
        inst._trait_values = {}
        inst._trait_notifiers = {}
        inst._trait_dyn_inits = {}
        # Here we tell all the TraitType instances to set their default
        # values on the instance.
        for key in dir(cls):
            # Some descriptors raise AttributeError like zope.interface's
            # __provides__ attributes even though they exist.  This causes
            # AttributeErrors even though they are listed in dir(cls).
            try:
                value = getattr(cls, key)
            except AttributeError:
                pass
            else:
                if isinstance(value, TraitType):
                    value.instance_init(inst)

        return inst

    def __init__(self, **kw):
        # Allow trait values to be set using keyword arguments.
        # We need to use setattr for this to trigger validation and
        # notifications.
        for key, value in kw.iteritems():
            setattr(self, key, value)

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

    @classmethod
    def class_trait_names(cls, **metadata):
        """Get a list of all the names of this classes traits.

        This method is just like the :meth:`trait_names` method, but is unbound.
        """
        return cls.class_traits(**metadata).keys()

    @classmethod
    def class_traits(cls, **metadata):
        """Get a list of all the traits of this class.

        This method is just like the :meth:`traits` method, but is unbound.

        The TraitTypes returned don't know anything about the values
        that the various HasTrait's instances are holding.

        This follows the same algorithm as traits does and does not allow
        for any simple way of specifying merely that a metadata name
        exists, but has any value.  This is because get_metadata returns
        None if a metadata key doesn't exist.
        """
        traits = dict([memb for memb in getmembers(cls) if \
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
        traits = dict([memb for memb in getmembers(self.__class__) if \
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
        if (not py3compat.PY3) and kind is InstanceType:
            msg = 'class %s' % value.__class__.__name__
        else:
            msg = '%s (i.e. %s)' % ( str( kind )[1:-1], repr( value ) )

        if obj is not None:
            e = "The '%s' trait of %s instance must be %s, but a value of %s was specified." \
                % (self.name, class_of(obj),
                   self.info(), msg)
        else:
            e = "The '%s' trait must be %s, but a value of %r was specified." \
                % (self.name, self.info(), msg)

        raise TraitError(e)


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
    """An int trait."""

    default_value = 0
    info_text = 'an int'

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

if py3compat.PY3:
    Long, CLong = Int, CInt
    Integer = Int
else:
    class Long(TraitType):
        """A long integer trait."""

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

    class Integer(TraitType):
        """An integer trait.

        Longs that are unnecessary (<= sys.maxint) are cast to ints."""

        default_value = 0
        info_text = 'an integer'

        def validate(self, obj, value):
            if isinstance(value, int):
                return value
            elif isinstance(value, long):
                # downcast longs that fit in int:
                # note that int(n > sys.maxint) returns a long, so
                # we don't need a condition on this cast
                return int(value)
            self.error(obj, value)


class Float(TraitType):
    """A float trait."""

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

# We should always be explicit about whether we're using bytes or unicode, both
# for Python 3 conversion and for reliable unicode behaviour on Python 2. So
# we don't have a Str type.
class Bytes(TraitType):
    """A trait for byte strings."""

    default_value = b''
    info_text = 'a string'

    def validate(self, obj, value):
        if isinstance(value, bytes):
            return value
        self.error(obj, value)


class CBytes(Bytes):
    """A casting version of the byte string trait."""

    def validate(self, obj, value):
        try:
            return bytes(value)
        except:
            self.error(obj, value)


class Unicode(TraitType):
    """A trait for unicode strings."""

    default_value = u''
    info_text = 'a unicode string'

    def validate(self, obj, value):
        if isinstance(value, unicode):
            return value
        if isinstance(value, bytes):
            return unicode(value)
        self.error(obj, value)


class CUnicode(Unicode):
    """A casting version of the unicode trait."""

    def validate(self, obj, value):
        try:
            return unicode(value)
        except:
            self.error(obj, value)


class ObjectName(TraitType):
    """A string holding a valid object name in this version of Python.

    This does not check that the name exists in any scope."""
    info_text = "a valid object identifier in Python"

    if py3compat.PY3:
        # Python 3:
        coerce_str = staticmethod(lambda _,s: s)

    else:
        # Python 2:
        def coerce_str(self, obj, value):
            "In Python 2, coerce ascii-only unicode to str"
            if isinstance(value, unicode):
                try:
                    return str(value)
                except UnicodeEncodeError:
                    self.error(obj, value)
            return value

    def validate(self, obj, value):
        value = self.coerce_str(obj, value)

        if isinstance(value, str) and py3compat.isidentifier(value):
            return value
        self.error(obj, value)

class DottedObjectName(ObjectName):
    """A string holding a valid dotted object name in Python, such as A.b3._c"""
    def validate(self, obj, value):
        value = self.coerce_str(obj, value)

        if isinstance(value, str) and py3compat.isidentifier(value, dotted=True):
            return value
        self.error(obj, value)


class Bool(TraitType):
    """A boolean (True, False) trait."""

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

        if not isinstance(value, basestring):
            self.error(obj, value)

        for v in self.values:
            if v.lower() == value.lower():
                return v
        self.error(obj, value)

class Container(Instance):
    """An instance of a container (list, set, etc.)

    To be subclassed by overriding klass.
    """
    klass = None
    _valid_defaults = SequenceTypes
    _trait = None

    def __init__(self, trait=None, default_value=None, allow_none=True,
                **metadata):
        """Create a container trait type from a list, set, or tuple.

        The default value is created by doing ``List(default_value)``,
        which creates a copy of the ``default_value``.

        ``trait`` can be specified, which restricts the type of elements
        in the container to that TraitType.

        If only one arg is given and it is not a Trait, it is taken as
        ``default_value``:

        ``c = List([1,2,3])``

        Parameters
        ----------

        trait : TraitType [ optional ]
            the type for restricting the contents of the Container.  If unspecified,
            types are not checked.

        default_value : SequenceType [ optional ]
            The default value for the Trait.  Must be list/tuple/set, and
            will be cast to the container type.

        allow_none : Bool [ default True ]
            Whether to allow the value to be None

        **metadata : any
            further keys for extensions to the Trait (e.g. config)

        """
        istrait = lambda t: isinstance(t, type) and issubclass(t, TraitType)

        # allow List([values]):
        if default_value is None and not istrait(trait):
            default_value = trait
            trait = None

        if default_value is None:
            args = ()
        elif isinstance(default_value, self._valid_defaults):
            args = (default_value,)
        else:
            raise TypeError('default value of %s was %s' %(self.__class__.__name__, default_value))

        if istrait(trait):
            self._trait = trait()
            self._trait.name = 'element'
        elif trait is not None:
            raise TypeError("`trait` must be a Trait or None, got %s"%repr_type(trait))

        super(Container,self).__init__(klass=self.klass, args=args,
                                  allow_none=allow_none, **metadata)

    def element_error(self, obj, element, validator):
        e = "Element of the '%s' trait of %s instance must be %s, but a value of %s was specified." \
            % (self.name, class_of(obj), validator.info(), repr_type(element))
        raise TraitError(e)

    def validate(self, obj, value):
        value = super(Container, self).validate(obj, value)
        if value is None:
            return value

        value = self.validate_elements(obj, value)

        return value

    def validate_elements(self, obj, value):
        validated = []
        if self._trait is None or isinstance(self._trait, Any):
            return value
        for v in value:
            try:
                v = self._trait.validate(obj, v)
            except TraitError:
                self.element_error(obj, v, self._trait)
            else:
                validated.append(v)
        return self.klass(validated)


class List(Container):
    """An instance of a Python list."""
    klass = list

    def __init__(self, trait=None, default_value=None, minlen=0, maxlen=sys.maxint,
                allow_none=True, **metadata):
        """Create a List trait type from a list, set, or tuple.

        The default value is created by doing ``List(default_value)``,
        which creates a copy of the ``default_value``.

        ``trait`` can be specified, which restricts the type of elements
        in the container to that TraitType.

        If only one arg is given and it is not a Trait, it is taken as
        ``default_value``:

        ``c = List([1,2,3])``

        Parameters
        ----------

        trait : TraitType [ optional ]
            the type for restricting the contents of the Container.  If unspecified,
            types are not checked.

        default_value : SequenceType [ optional ]
            The default value for the Trait.  Must be list/tuple/set, and
            will be cast to the container type.

        minlen : Int [ default 0 ]
            The minimum length of the input list

        maxlen : Int [ default sys.maxint ]
            The maximum length of the input list

        allow_none : Bool [ default True ]
            Whether to allow the value to be None

        **metadata : any
            further keys for extensions to the Trait (e.g. config)

        """
        self._minlen = minlen
        self._maxlen = maxlen
        super(List, self).__init__(trait=trait, default_value=default_value,
                                allow_none=allow_none, **metadata)

    def length_error(self, obj, value):
        e = "The '%s' trait of %s instance must be of length %i <= L <= %i, but a value of %s was specified." \
            % (self.name, class_of(obj), self._minlen, self._maxlen, value)
        raise TraitError(e)

    def validate_elements(self, obj, value):
        length = len(value)
        if length < self._minlen or length > self._maxlen:
            self.length_error(obj, value)

        return super(List, self).validate_elements(obj, value)


class Set(Container):
    """An instance of a Python set."""
    klass = set

class Tuple(Container):
    """An instance of a Python tuple."""
    klass = tuple

    def __init__(self, *traits, **metadata):
        """Tuple(*traits, default_value=None, allow_none=True, **medatata)

        Create a tuple from a list, set, or tuple.

        Create a fixed-type tuple with Traits:

        ``t = Tuple(Int, Str, CStr)``

        would be length 3, with Int,Str,CStr for each element.

        If only one arg is given and it is not a Trait, it is taken as
        default_value:

        ``t = Tuple((1,2,3))``

        Otherwise, ``default_value`` *must* be specified by keyword.

        Parameters
        ----------

        *traits : TraitTypes [ optional ]
            the tsype for restricting the contents of the Tuple.  If unspecified,
            types are not checked. If specified, then each positional argument
            corresponds to an element of the tuple.  Tuples defined with traits
            are of fixed length.

        default_value : SequenceType [ optional ]
            The default value for the Tuple.  Must be list/tuple/set, and
            will be cast to a tuple. If `traits` are specified, the
            `default_value` must conform to the shape and type they specify.

        allow_none : Bool [ default True ]
            Whether to allow the value to be None

        **metadata : any
            further keys for extensions to the Trait (e.g. config)

        """
        default_value = metadata.pop('default_value', None)
        allow_none = metadata.pop('allow_none', True)

        istrait = lambda t: isinstance(t, type) and issubclass(t, TraitType)

        # allow Tuple((values,)):
        if len(traits) == 1 and default_value is None and not istrait(traits[0]):
            default_value = traits[0]
            traits = ()

        if default_value is None:
            args = ()
        elif isinstance(default_value, self._valid_defaults):
            args = (default_value,)
        else:
            raise TypeError('default value of %s was %s' %(self.__class__.__name__, default_value))

        self._traits = []
        for trait in traits:
            t = trait()
            t.name = 'element'
            self._traits.append(t)

        if self._traits and default_value is None:
            # don't allow default to be an empty container if length is specified
            args = None
        super(Container,self).__init__(klass=self.klass, args=args,
                                  allow_none=allow_none, **metadata)

    def validate_elements(self, obj, value):
        if not self._traits:
            # nothing to validate
            return value
        if len(value) != len(self._traits):
            e = "The '%s' trait of %s instance requires %i elements, but a value of %s was specified." \
                % (self.name, class_of(obj), len(self._traits), repr_type(value))
            raise TraitError(e)

        validated = []
        for t,v in zip(self._traits, value):
            try:
                v = t.validate(obj, v)
            except TraitError:
                self.element_error(obj, v, t)
            else:
                validated.append(v)
        return tuple(validated)


class Dict(Instance):
    """An instance of a Python dict."""

    def __init__(self, default_value=None, allow_none=True, **metadata):
        """Create a dict trait type from a dict.

        The default value is created by doing ``dict(default_value)``,
        which creates a copy of the ``default_value``.
        """
        if default_value is None:
            args = ((),)
        elif isinstance(default_value, dict):
            args = (default_value,)
        elif isinstance(default_value, SequenceTypes):
            args = (default_value,)
        else:
            raise TypeError('default value of Dict was %s' % default_value)

        super(Dict,self).__init__(klass=dict, args=args,
                                  allow_none=allow_none, **metadata)

class TCPAddress(TraitType):
    """A trait for an (ip, port) tuple.

    This allows for both IPv4 IP addresses as well as hostnames.
    """

    default_value = ('127.0.0.1', 0)
    info_text = 'an (ip, port) tuple'

    def validate(self, obj, value):
        if isinstance(value, tuple):
            if len(value) == 2:
                if isinstance(value[0], basestring) and isinstance(value[1], int):
                    port = value[1]
                    if port >= 0 and port <= 65535:
                        return value
        self.error(obj, value)
