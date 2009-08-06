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
  traitlets (list, dict, tuple) that can trigger notifications if their
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
from types import InstanceType, ClassType

ClassTypes = (ClassType, type)

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


def get_module_name ( level = 2 ):
    """ Returns the name of the module that the caller's caller is located in.
    """
    return sys._getframe( level ).f_globals.get( '__name__', '__main__' )


#-----------------------------------------------------------------------------
# Base TraitletType for all traitlets
#-----------------------------------------------------------------------------


class TraitletType(object):

    metadata = {}
    default_value = Undefined
    info_text = 'any value'

    def __init__(self, default_value=NoDefaultSpecified, **metadata):
        """Create a TraitletType.
        """
        if default_value is not NoDefaultSpecified:
            self.default_value = default_value
        self.metadata.update(metadata)
        self.init()

    def init(self):
        pass

    def get_default_value(self):
        """Create a new instance of the default value."""
        dv = self.default_value
        return dv

    def __get__(self, obj, cls=None, skipset=False):
        """Get the value of the traitlet by self.name for the instance.

        The creation of default values is deferred until this is called the
        first time.  This is done so instances of the parent HasTraitlets
        will have their own default value instances.

        A default value is not validated until it is requested.  Thus, if
        you use an invalid default value, but never request it, you are fine.
        """
        if obj is None:
            return self
        else:
            if not obj._traitlet_values.has_key(self.name):
                dv = self.get_default_value()
                # Call __set__ with first=True so we don't get a recursion
                if not skipset:
                    self.__set__(obj, dv, first=True)
                return dv
            else:
                return obj._traitlet_values[self.name]

    def __set__(self, obj, value, first=False):
        new_value = self._validate(obj, value)
        if not first:
            # Call __get__ with skipset=True so we don't get a recursion
            old_value = self.__get__(obj, skipset=True)
            if old_value != new_value:
                obj._traitlet_values[self.name] = new_value
                obj._notify_traitlet(self.name, old_value, new_value)
        else:
            obj._traitlet_values[self.name] = new_value

    def _validate(self, obj, value):
        if hasattr(self, 'validate'):
            return self.validate(obj, value)
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

    def _notify_traitlet(self, name, old_value, new_value):

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

    def traitlet_keys(self):
        """Get a list of all the names of this classes traitlets."""
        return [memb[0] for memb in inspect.getmembers(self.__class__) if isinstance(memb[1], TraitletType)]


#-----------------------------------------------------------------------------
# Actual TraitletTypes implementations/subclasses
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# TraitletTypes subclasses for handling classes and instances of classes
#-----------------------------------------------------------------------------


class BaseClassResolver(TraitletType):
    """Mixin class for traitlets that need to resolve classes by strings.
    
    This class provides is a mixin that provides its subclasses with the 
    ability to resolve classes by specifying a string name (for example,
    'foo.bar.MyClass').  An actual class can also be resolved.

    Any subclass must define instances with 'klass' and 'module' attributes
    that contain the string name of the class (or actual class object) and
    the module name that contained the original trait definition (used for
    resolving local class names (e.g. 'LocalClass')).
    """

    def resolve_class(self, obj, value):
        klass = self.validate_class(self.find_class(self.klass))
        if klass is None:
            self.validate_failed(obj, value)

        self.klass = klass

    def validate_class(self, klass):
        return klass

    def find_class(self, klass):
        module = self.module
        col    = klass.rfind('.')
        if col >= 0:
            module = klass[ : col ]
            klass = klass[ col + 1: ]

        theClass = getattr(sys.modules.get(module), klass, None)
        if (theClass is None) and (col >= 0):
            try:
                mod = __import__(module)
                for component in module.split( '.' )[1:]:
                    mod = getattr(mod, component)

                theClass = getattr(mod, klass, None)
            except:
                pass

        return theClass

    def validate_failed (self, obj, value):
        kind = type(value)
        if kind is InstanceType:
            msg = 'class %s' % value.__class__.__name__
        else:
            msg = '%s (i.e. %s)' % ( str( kind )[1:-1], repr( value ) )

        self.error(obj, msg)


class Type(BaseClassResolver):
    """A traitlet whose value must be a subclass of a specified class."""

    def __init__ (self, default_value=None, klass=None, allow_none=True, **metadata ):
        """Construct a Type traitlet

        A Type traitlet specifies that its values must be subclasses of
        a particular class.

        Parameters
        ----------
        default_value : class or None
            The default value must be a subclass of klass.
        klass : class, str, None
            Values of this traitlet must be a subclass of klass.  The klass
            may be specified in a string like: 'foo.bar.MyClass'.
        allow_none : boolean
            Indicates whether None is allowed as an assignable value. Even if
            ``False``, the default value may be ``None``.
        """
        if default_value is None:
            if klass is None:
                klass = object
        elif klass is None:
            klass = default_value

        if isinstance(klass, basestring):
            self.validate = self.resolve
        elif not isinstance(klass, ClassTypes):
            raise TraitletError("A Type traitlet must specify a class.")

        self.klass       = klass
        self._allow_none = allow_none
        self.module      = get_module_name()

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

    def resolve(self, obj, name, value):
        """ Resolves a class originally specified as a string into an actual
            class, then resets the trait so that future calls will be handled by
            the normal validate method.
        """
        if isinstance(self.klass, basestring):
            self.resolve_class(obj, value)
            del self.validate

        return self.validate(obj, value)

    def info(self):
        """ Returns a description of the trait."""
        klass = self.klass
        if not isinstance(klass, basestring):
            klass = klass.__name__

        result = 'a subclass of ' + klass

        if self._allow_none:
            return result + ' or None'

        return result

    def get_default_value(self):
        """ Returns a tuple of the form: ( default_value_type, default_value )
            which describes the default value for this trait.
        """
        if not isinstance(self.default_value, basestring):
            return super(Type, self).get_default_value()

        dv = self.resolve_default_value()
        dvt = type(dv)
        return (dvt, dv)

    def resolve_default_value(self):
        """ Resolves a class name into a class so that it can be used to
            return the class as the default value of the trait.
        """
        if isinstance(self.klass, basestring):
            try:
                self.resolve_class(None, None)
                del self.validate
            except:
                raise TraitletError('Could not resolve %s into a valid class' %
                                    self.klass )

        return self.klass


class DefaultValueGenerator(object):
    """A class for generating new default value instances."""

    def __init__(self, klass, *args, **kw):
        self.klass = klass
        self.args = args
        self.kw = kw


class Instance(BaseClassResolver):
    """A trait whose value must be an instance of a specified class.
    
    The value can also be an instance of a subclass of the specified class.
    """

    def __init__(self, klass=None, args=None, kw=None, allow_none=True, 
                 module = None, **metadata ):
        """Construct an Instance traitlet.

        Parameters
        ----------
        klass : class or instance
            The object that forms the basis for the traitlet.  If an instance
            values must have isinstance(value, type(instance)).
        args : tuple
            Positional arguments for generating the default value.
        kw : dict
            Keyword arguments for generating the default value.
        allow_none : bool
            Indicates whether None is allowed as a value.

        Default Value
        -------------
        If klass is an instance, default value is None.  If klass is a class
        then the default value is obtained by calling ``klass(*args, **kw)``.
        If klass is a str, it is first resolved to an actual class and then
        instantiated with ``klass(*args, **kw)``.
        """

        self._allow_none = allow_none
        self.module      = module or get_module_name()

        if klass is None:
            raise TraitletError('A %s traitlet must have a class specified.' %
                                self.__class__.__name__ )
        elif not isinstance(klass, (basestring,) + ClassTypes ):
            # klass is an instance so default value will be None
            self.klass = klass.__class__
            default_value = None
        else:
            # klass is a str or class so we handle args, kw
            if args is None:
                args = ()
            if kw is None:
                if isinstance(args, dict):
                    kw = args
                    args = ()
                else:
                    kw = {}
            if not isinstance(kw, dict):
                raise TraitletError("The 'kw' argument must be a dict.")
            if not isinstance(args, tuple):
                raise TraitletError("The 'args' argument must be a tuple.")
            self.klass = klass
            # This tells my get_default_value that the default value
            # instance needs to be generated when it is called.  This 
            # is usually when TraitletType.__get__ is called for the 1st time.
            
            default_value = DefaultValueGenerator(klass, *args, **kw)

        super(Instance, self).__init__(default_value, **metadata)

    def validate(self, obj, value):
        if value is None:
            if self._allow_none:
                return value
            self.validate_failed(obj, value)

        # This is where self.klass is turned into a real class if it was
        # a str initially.  This happens the first time TraitletType.__set__
        # is called.  This does happen if a default value is generated by
        # TraitletType.__get__.
        if isinstance(self.klass, basestring):
            self.resolve_class(obj, value)

        if isinstance(value, self.klass):
            return value
        else:
            self.validate_failed(obj, value)

    def info ( self ):
        klass = self.klass
        if not isinstance( klass, basestring ):
            klass = klass.__name__
        result = class_of(klass)
        if self._allow_none:
            return result + ' or None'

        return result

    def get_default_value ( self ):
        """Instantiate a default value instance.
        
        When TraitletType.__get__ is called the first time, this is called
        (if no value has been assigned) to get a default value instance.
        """
        dv  = self.default_value
        if isinstance(dv, DefaultValueGenerator):
            klass = dv.klass
            args = dv.args
            kw = dv.kw
            if isinstance(klass, basestring):
                klass = self.validate_class(self.find_class(klass))
                if klass is None:
                    raise TraitletError('Unable to locate class: ' + dv.klass)
            return klass(*args, **kw)
        else:
            return dv


class This(TraitletType):
    """A traitlet for instances of the class containing this trait."""

    info_text = 'an instance of the same type as the receiver'

    def __init__(self, default_value=None, allow_none=True, **metadata):
        if default_value is not None:
            raise TraitletError("The default value of 'This' can only be None.")
        super(This, self).__init__(default_value, **metadata)
        self._allow_none = allow_none
        if allow_none:
            self.info_text = self.info_text + ' or None'

    def validate(self, obj, value):
        if value is None:
            if self._allow_none:
                return value
            self.validate_failed(obj, value)

        if isinstance(value, obj.__class__):
            return value
        else:
            self.validate_failed(obj, value)

    def validate_failed (self, obj, value):
        kind = type(value)
        if kind is InstanceType:
            msg = 'class %s' % value.__class__.__name__
        else:
            msg = '%s (i.e. %s)' % ( str( kind )[1:-1], repr( value ) )

        self.error(obj, msg)


#-----------------------------------------------------------------------------
# Basic TraitletTypes implementations/subclasses
#-----------------------------------------------------------------------------


class Any(TraitletType):
    default_value = None
    info_text = 'any value'


class Int(TraitletType):
    """A integer traitlet."""

    evaluate = int
    default_value = 0
    info_text = 'an integer'

    def validate(self, obj, value):
        if isinstance(value, int):
            return value
        self.error(obj, value)

class CInt(Int):
    """A casting version of the int traitlet."""

    def validate(self, obj, value):
        try:
            return int(value)
        except:
            self.error(obj, value)


class Long(TraitletType):
    """A long integer traitlet."""

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
    """A casting version of the long integer traitlet."""

    def validate(self, obj, value):
        try:
            return long(value)
        except:
            self.error(obj, value)


class Float(TraitletType):
    """A float traitlet."""

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
    """A casting version of the float traitlet."""

    def validate(self, obj, value):
        try:
            return float(value)
        except:
            self.error(obj, value)

class Complex(TraitletType):
    """A traitlet for complex numbers."""

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
    """A casting version of the complex number traitlet."""

    def validate (self, obj, value):
        try:
            return complex(value)
        except:
            self.error(obj, value)


class Str(TraitletType):
    """A traitlet for strings."""

    evaluate = lambda x: x
    default_value = ''
    info_text = 'a string'

    def validate(self, obj, value):
        if isinstance(value, str):
            return value
        self.error(obj, value)


class CStr(Str):
    """A casting version of the string traitlet."""

    def validate(self, obj, value):
        try:
            return str(value)
        except:
            try:
                return unicode(value)
            except:
                self.error(obj, value)


class Unicode(TraitletType):
    """A traitlet for unicode strings."""

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
    """A casting version of the unicode traitlet."""

    def validate(self, obj, value):
        try:
            return unicode(value)
        except:
            self.error(obj, value)


class Bool(TraitletType):
    """A boolean (True, False) traitlet."""
    evaluate = bool
    default_value = False
    info_text = 'a boolean'

    def validate(self, obj, value):
        if isinstance(value, bool):
            return value
        self.error(obj, value)


class CBool(Bool):
    """A casting version of the boolean traitlet."""

    def validate(self, obj, value):
        try:
            return bool(value)
        except:
            self.error(obj, value)