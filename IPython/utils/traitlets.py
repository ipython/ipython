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
from types import InstanceType, ClassType, FunctionType

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


class _SimpleTest:
    def __init__ ( self, value ): self.value = value
    def __call__ ( self, test  ):
        print test, self.value 
        return test == self.value
    def __repr__(self):
        return "<SimpleTest(%r)" % self.value
    def __str__(self):
        return self.__repr__()


#-----------------------------------------------------------------------------
# Base TraitletType for all traitlets
#-----------------------------------------------------------------------------


class TraitletType(object):
    """A base class for all traitlet descriptors.

    Notes
    -----
    Our implementation of traitlets is based on Python's descriptor
    prototol.  This class is the base class for all such descriptors.  The
    only magic we use is a custom metaclass for the main :class:`HasTraitlets`
    class that does the following:

    1. Sets the :attr:`name` attribute of every :class:`TraitletType`
       instance in the class dict to the name of the attribute.
    2. Sets the :attr:`this_class` attribute of every :class:`TraitletType`
       instance in the class dict to the *class* that declared the traitlet.
       This is used by the :class:`This` traitlet to allow subclasses to
       accept superclasses for :class:`This` values.
    """
    

    metadata = {}
    default_value = Undefined
    info_text = 'any value'

    def __init__(self, default_value=NoDefaultSpecified, **metadata):
        """Create a TraitletType.
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

    def set_default_value(self, obj):
        dv = self.get_default_value()
        newdv = self._validate(obj, dv)
        obj._traitlet_values[self.name] = newdv
        

    def __get__(self, obj, cls=None):
        """Get the value of the traitlet by self.name for the instance.

        Default values are instantiated when :meth:`HasTraitlets.__new__`
        is called.  Thus by the time this method gets called either the 
        default value or a user defined value (they called :meth:`__set__`)
        is in the :class:`HasTraitlets` instance.
        """
        if obj is None:
            return self
        else:
            try:
                value = obj._traitlet_values[self.name]
            except:
                # HasTraitlets should call set_default_value to populate
                # this.  So this should never be reached.
                raise TraitletError('Unexpected error in TraitletType: '
                                    'default value not set properly')
            else:
                return value

    def __set__(self, obj, value):
        new_value = self._validate(obj, value)
        old_value = self.__get__(obj)
        if old_value != new_value:
            obj._traitlet_values[self.name] = new_value
            obj._notify_traitlet(self.name, old_value, new_value)

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

    def get_metadata(self, key):
        return getattr(self, '_metadata', {}).get(key, None)

    def set_metadata(self, key, value):
        getattr(self, '_metadata', {})[key] = value


#-----------------------------------------------------------------------------
# The HasTraitlets implementation
#-----------------------------------------------------------------------------


class MetaHasTraitlets(type):
    """A metaclass for HasTraitlets.
    
    This metaclass makes sure that any TraitletType class attributes are
    instantiated and sets their name attribute.
    """
    
    def __new__(mcls, name, bases, classdict):
        """Create the HasTraitlets class.
        
        This instantiates all TraitletTypes in the class dict and sets their
        :attr:`name` attribute.
        """
        # print "========================="
        # print "MetaHasTraitlets.__new__"
        # print "mcls, ", mcls
        # print "name, ", name
        # print "bases, ", bases
        # print "classdict, ", classdict
        for k,v in classdict.iteritems():
            if isinstance(v, TraitletType):
                v.name = k
            elif inspect.isclass(v):
                if issubclass(v, TraitletType):
                    vinst = v()
                    vinst.name = k
                    classdict[k] = vinst
        return super(MetaHasTraitlets, mcls).__new__(mcls, name, bases, classdict)

    def __init__(cls, name, bases, classdict):
        """Finish initializing the HasTraitlets class.
        
        This sets the :attr:`this_class` attribute of each TraitletType in the
        class dict to the newly created class ``cls``.
        """
        # print "========================="
        # print "MetaHasTraitlets.__init__"
        # print "cls, ", cls
        # print "name, ", name
        # print "bases, ", bases
        # print "classdict, ", classdict
        for k, v in classdict.iteritems():
            if isinstance(v, TraitletType):
                v.this_class = cls
        super(MetaHasTraitlets, cls).__init__(name, bases, classdict)

class HasTraitlets(object):

    __metaclass__ = MetaHasTraitlets

    def __new__(cls, *args, **kw):
        inst = super(HasTraitlets, cls).__new__(cls, *args, **kw)
        inst._traitlet_values = {}
        inst._traitlet_notifiers = {}
        # Here we tell all the TraitletType instances to set their default
        # values on the instance. 
        for key in dir(cls):
            value = getattr(cls, key)
            if isinstance(value, TraitletType):
                value.set_default_value(inst)
        return inst

    # def __init__(self):
    #     self._traitlet_values = {}
    #     self._traitlet_notifiers = {}

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

    def traitlet_names(self, **metadata):
        """Get a list of all the names of this classes traitlets."""
        return self.traitlets(**metadata).keys()

    def traitlets(self, **metadata):
        """Get a list of all the traitlets of this class.

        The TraitletTypes returned don't know anything about the values
        that the various HasTraitlet's instances are holding.
        """
        traitlets = dict([memb for memb in inspect.getmembers(self.__class__) if \
                     isinstance(memb[1], TraitletType)])
        if len(metadata) == 0:
            return traitlets

        for meta_name, meta_eval in metadata.items():
            if type(meta_eval) is not FunctionType:
                metadata[meta_name] = _SimpleTest(meta_eval)

        result = {}
        for name, traitlet in traitlets.items():
            for meta_name, meta_eval in metadata.items():
                if not meta_eval(traitlet.get_metadata(meta_name)):
                    break
            else:
                result[name] = traitlet

        return result

    def traitlet_metadata(self, traitletname, key):
        """Get metadata values for traitlet by key."""
        try:
            traitlet = getattr(self.__class__, traitletname)
        except AttributeError:
            raise TraitletError("Class %s does not have a traitlet named %s" %
                                (self.__class__.__name__, traitletname))
        else:
            return traitlet.get_metadata(key)

#-----------------------------------------------------------------------------
# Actual TraitletTypes implementations/subclasses
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# TraitletTypes subclasses for handling classes and instances of classes
#-----------------------------------------------------------------------------


class ClassBasedTraitletType(TraitletType):
    """A traitlet with error reporting for Type, Instance and This."""

    def error(self, obj, value):
        kind = type(value)
        if kind is InstanceType:
            msg = 'class %s' % value.__class__.__name__
        else:
            msg = '%s (i.e. %s)' % ( str( kind )[1:-1], repr( value ) )

        super(ClassBasedTraitletType, self).error(obj, msg)


class Type(ClassBasedTraitletType):
    """A traitlet whose value must be a subclass of a specified class."""

    def __init__ (self, default_value=None, klass=None, allow_none=True, **metadata ):
        """Construct a Type traitlet

        A Type traitlet specifies that its values must be subclasses of
        a particular class.

        Parameters
        ----------
        default_value : class
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

        if not inspect.isclass(klass):
            raise TraitletError("A Type traitlet must specify a class.")

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
        klass = self.klass.__name__
        result = 'a subclass of ' + klass
        if self._allow_none:
            return result + ' or None'
        return result


class DefaultValueGenerator(object):
    """A class for generating new default value instances."""

    def __init__(self, klass, *args, **kw):
        self.klass = klass
        self.args = args
        self.kw = kw

    def generate(self):
        return self.klass(*self.args, **self.kw)


class Instance(ClassBasedTraitletType):
    """A trait whose value must be an instance of a specified class.
    
    The value can also be an instance of a subclass of the specified class.
    """

    def __init__(self, klass=None, args=None, kw=None, 
                 allow_none=True, **metadata ):
        """Construct an Instance traitlet.

        This traitlet allows values that are instances of a particular
        class or its sublclasses.  Our implementation is quite different
        from that of enthough.traits as we don't allow instances to be used
        for klass and we handle the ``args`` and ``kw`` arguments differently.

        Parameters
        ----------
        klass : class
            The class that forms the basis for the traitlet.  Instances
            and strings are not allowed.
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

        if (klass is None) or (not inspect.isclass(klass)):
            raise TraitletError('The klass argument must be a class'
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
                raise TraitletError("The 'kw' argument must be a dict or None.")
            if not isinstance(args, tuple):
                raise TraitletError("The 'args' argument must be a tuple or None.")
            
            default_value = DefaultValueGenerator(self.klass, *args, **kw)

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
        klass = self.klass.__name__
        result = class_of(klass)
        if self._allow_none:
            return result + ' or None'

        return result

    def get_default_value(self):
        """Instantiate a default value instance.
        
        This is called when the containing HasTraitlets classes'
        :meth:`__new__` method is called to ensure that a unique instance
        is created for each HasTraitlets instance.
        """
        dv  = self.default_value
        if isinstance(dv, DefaultValueGenerator):
            return dv.generate()
        else:
            return dv


class This(ClassBasedTraitletType):
    """A traitlet for instances of the class containing this trait.

    Because how how and when class bodies are executed, the ``This``
    traitlet can only have a default value of None.  This, and because we 
    always validate default values, ``allow_none`` is *always* true.
    """

    info_text = 'an instance of the same type as the receiver or None'

    def __init__(self, **metadata):
        super(This, self).__init__(None, **metadata)

    def validate(self, obj, value):
        # What if value is a superclass of obj.__class__?  This is
        # complicated if it was the superclass that defined the This
        # traitlet.
        if isinstance(value, self.this_class) or (value is None):
            return value
        else:
            self.error(obj, value)


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