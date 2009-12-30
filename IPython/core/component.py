#!/usr/bin/env python
# encoding: utf-8
"""
A lightweight component system for IPython.

Authors:

* Brian Granger
* Fernando Perez
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

from copy import deepcopy
import datetime
from weakref import WeakValueDictionary

from IPython.utils.importstring import import_item
from IPython.config.loader import Config
from IPython.utils.traitlets import (
    HasTraitlets, TraitletError, MetaHasTraitlets, Instance, This
)


#-----------------------------------------------------------------------------
# Helper classes for Components
#-----------------------------------------------------------------------------


class ComponentError(Exception):
    pass

class MetaComponentTracker(type):
    """A metaclass that tracks instances of Components and its subclasses."""

    def __init__(cls, name, bases, d):
        super(MetaComponentTracker, cls).__init__(name, bases, d)
        cls.__instance_refs = WeakValueDictionary()
        cls.__numcreated = 0

    def __call__(cls, *args, **kw):
        """Called when a class is called (instantiated)!!!
        
        When a Component or subclass is instantiated, this is called and
        the instance is saved in a WeakValueDictionary for tracking.
        """
        instance = cls.__new__(cls, *args, **kw)

        # Register the instance before __init__ is called so get_instances 
        # works inside __init__ methods!
        indices = cls.register_instance(instance)

        # This is in a try/except because of the __init__ method fails, the
        # instance is discarded and shouldn't be tracked.
        try:
            if isinstance(instance, cls):
                cls.__init__(instance, *args, **kw)
        except:
            # Unregister the instance because __init__ failed!
            cls.unregister_instances(indices)
            raise
        else:
            return instance

    def register_instance(cls, instance):
        """Register instance with cls and its subclasses."""
        # indices is a list of the keys used to register the instance
        # with.  This list is needed if the instance needs to be unregistered.
        indices = []
        for c in cls.__mro__:
            if issubclass(cls, c) and issubclass(c, Component):
                c.__numcreated += 1
                indices.append(c.__numcreated)
                c.__instance_refs[c.__numcreated] = instance
            else:
                break
        return indices

    def unregister_instances(cls, indices):
        """Unregister instance with cls and its subclasses."""
        for c, index in zip(cls.__mro__, indices):
            try:
                del c.__instance_refs[index]
            except KeyError:
                pass

    def clear_instances(cls):
        """Clear all instances tracked by cls."""
        cls.__instance_refs.clear()
        cls.__numcreated = 0

    def get_instances(cls, name=None, root=None, klass=None):
        """Get all instances of cls and its subclasses.

        Parameters
        ----------
        name : str
            Limit to components with this name.
        root : Component or subclass
            Limit to components having this root.
        klass : class or str
            Limits to instances of the class or its subclasses.  If a str
            is given ut must be in the form 'foo.bar.MyClass'.  The str
            form of this argument is useful for forward declarations.
        """
        if klass is not None:
            if isinstance(klass, basestring):
                klass = import_item(klass)
            # Limit search to instances of klass for performance
            if issubclass(klass, Component):
                return klass.get_instances(name=name, root=root)
        instances = cls.__instance_refs.values()
        if name is not None:
            instances = [i for i in instances if i.name == name]
        if klass is not None:
            instances = [i for i in instances if isinstance(i, klass)]
        if root is not None:
            instances = [i for i in instances if i.root == root]
        return instances

    def get_instances_by_condition(cls, call, name=None, root=None,
                                   klass=None):
        """Get all instances of cls, i such that call(i)==True.

        This also takes the ``name`` and ``root`` and ``classname`` 
        arguments of :meth:`get_instance`
        """
        return [i for i in cls.get_instances(name, root, klass) if call(i)]


def masquerade_as(instance, cls):
    """Let instance masquerade as an instance of cls.

    Sometimes, such as in testing code, it is useful to let a class
    masquerade as another.  Python, being duck typed, allows this by 
    default.  But, instances of components are tracked by their class type.

    After calling this, ``cls.get_instances()`` will return ``instance``. This
    does not, however, cause ``isinstance(instance, cls)`` to return ``True``.

    Parameters
    ----------
    instance : an instance of a Component or Component subclass
        The instance that will pretend to be a cls.
    cls : subclass of Component
        The Component subclass that instance will pretend to be.
    """
    cls.register_instance(instance)


class ComponentNameGenerator(object):
    """A Singleton to generate unique component names."""

    def __init__(self, prefix):
        self.prefix = prefix
        self.i = 0

    def __call__(self):
        count = self.i
        self.i += 1
        return "%s%s" % (self.prefix, count)


ComponentNameGenerator = ComponentNameGenerator('ipython.component')


class MetaComponent(MetaHasTraitlets, MetaComponentTracker):
    pass


#-----------------------------------------------------------------------------
# Component implementation
#-----------------------------------------------------------------------------


class Component(HasTraitlets):

    __metaclass__ = MetaComponent

    # Traitlets are fun!
    config = Instance(Config,(),{})
    parent = This()
    root = This()
    created = None

    def __init__(self, parent, name=None, config=None):
        """Create a component given a parent and possibly and name and config.

        Parameters
        ----------
        parent : Component subclass
            The parent in the component graph.  The parent is used
            to get the root of the component graph.
        name : str
            The unique name of the component.  If empty, then a unique
            one will be autogenerated.
        config : Config
            If this is empty, self.config = parent.config, otherwise
            self.config = config and root.config is ignored.  This argument
            should only be used to *override* the automatic inheritance of 
            parent.config.  If a caller wants to modify parent.config 
            (not override), the caller should make a copy and change 
            attributes and then pass the copy to this argument.
        
        Notes
        -----
        Subclasses of Component must call the :meth:`__init__` method of
        :class:`Component` *before* doing anything else and using 
        :func:`super`::
        
            class MyComponent(Component):
                def __init__(self, parent, name=None, config=None):
                    super(MyComponent, self).__init__(parent, name, config)
                    # Then any other code you need to finish initialization.

        This ensures that the :attr:`parent`, :attr:`name` and :attr:`config`
        attributes are handled properly.
        """
        super(Component, self).__init__()
        self._children = []
        if name is None:
            self.name = ComponentNameGenerator()
        else:
            self.name = name
        self.root = self # This is the default, it is set when parent is set
        self.parent = parent
        if config is not None:
            self.config = config
            # We used to deepcopy, but for now we are trying to just save
            # by reference.  This *could* have side effects as all components
            # will share config. In fact, I did find such a side effect in
            # _config_changed below. If a config attribute value was a mutable type
            # all instances of a component were getting the same copy, effectively
            # making that a class attribute.
            # self.config = deepcopy(config)
        else:
            if self.parent is not None:
                self.config = self.parent.config
                # We used to deepcopy, but for now we are trying to just save
                # by reference.  This *could* have side effects as all components
                # will share config. In fact, I did find such a side effect in
                # _config_changed below. If a config attribute value was a mutable type
                # all instances of a component were getting the same copy, effectively
                # making that a class attribute.
                # self.config = deepcopy(self.parent.config)

        self.created = datetime.datetime.now()

    #-------------------------------------------------------------------------
    # Static traitlet notifiations
    #-------------------------------------------------------------------------

    def _parent_changed(self, name, old, new):
        if old is not None:
            old._remove_child(self)
        if new is not None:
            new._add_child(self)

        if new is None:
            self.root = self
        else:
            self.root = new.root

    def _root_changed(self, name, old, new):
        if self.parent is None:
            if not (new is self):
                raise ComponentError("Root not self, but parent is None.")
        else:
            if not self.parent.root is new:
                raise ComponentError("Error in setting the root attribute: "
                                     "root != parent.root")

    def _config_changed(self, name, old, new):
        """Update all the class traits having ``config=True`` as metadata.

        For any class traitlet with a ``config`` metadata attribute that is
        ``True``, we update the traitlet with the value of the corresponding
        config entry.
        """
        # Get all traitlets with a config metadata entry that is True
        traitlets = self.traitlets(config=True)

        # We auto-load config section for this class as well as any parent
        # classes that are Component subclasses.  This starts with Component
        # and works down the mro loading the config for each section.
        section_names = [cls.__name__ for cls in \
            reversed(self.__class__.__mro__) if 
            issubclass(cls, Component) and issubclass(self.__class__, cls)]

        for sname in section_names:
            # Don't do a blind getattr as that would cause the config to 
            # dynamically create the section with name self.__class__.__name__.
            if new._has_section(sname):
                my_config = new[sname]
                for k, v in traitlets.items():
                    # Don't allow traitlets with config=True to start with
                    # uppercase.  Otherwise, they are confused with Config
                    # subsections.  But, developers shouldn't have uppercase
                    # attributes anyways! (PEP 6)
                    if k[0].upper()==k[0] and not k.startswith('_'):
                        raise ComponentError('Component traitlets with '
                        'config=True must start with a lowercase so they are '
                        'not confused with Config subsections: %s.%s' % \
                        (self.__class__.__name__, k))
                    try:
                        # Here we grab the value from the config
                        # If k has the naming convention of a config
                        # section, it will be auto created.
                        config_value = my_config[k]
                    except KeyError:
                        pass
                    else:
                        # print "Setting %s.%s from %s.%s=%r" % \
                        #     (self.__class__.__name__,k,sname,k,config_value)
                        # We have to do a deepcopy here if we don't deepcopy the entire
                        # config object. If we don't, a mutable config_value will be
                        # shared by all instances, effectively making it a class attribute.
                        setattr(self, k, deepcopy(config_value))

    @property
    def children(self):
        """A list of all my child components."""
        return self._children

    def _remove_child(self, child):
        """A private method for removing children components."""
        if child in self._children:
            index = self._children.index(child)
            del self._children[index]

    def _add_child(self, child):
        """A private method for adding children components."""
        if child not in self._children:
            self._children.append(child)

    def __repr__(self):
        return "<%s('%s')>" % (self.__class__.__name__, self.name)
