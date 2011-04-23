#!/usr/bin/env python
# encoding: utf-8
"""
A base class for objects that are configurable.

Authors:

* Brian Granger
* Fernando Perez
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from copy import deepcopy
import datetime

from loader import Config
from IPython.utils.traitlets import HasTraits, Instance
from IPython.utils.text import indent


#-----------------------------------------------------------------------------
# Helper classes for Configurables
#-----------------------------------------------------------------------------


class ConfigurableError(Exception):
    pass


class MultipleInstanceError(ConfigurableError):
    pass

#-----------------------------------------------------------------------------
# Configurable implementation
#-----------------------------------------------------------------------------


class Configurable(HasTraits):

    config = Instance(Config,(),{})
    created = None

    def __init__(self, **kwargs):
        """Create a conigurable given a config config.

        Parameters
        ----------
        config : Config
            If this is empty, default values are used. If config is a 
            :class:`Config` instance, it will be used to configure the
            instance.
        
        Notes
        -----
        Subclasses of Configurable must call the :meth:`__init__` method of
        :class:`Configurable` *before* doing anything else and using 
        :func:`super`::
        
            class MyConfigurable(Configurable):
                def __init__(self, config=None):
                    super(MyConfigurable, self).__init__(config)
                    # Then any other code you need to finish initialization.

        This ensures that instances will be configured properly.
        """
        config = kwargs.pop('config', None)
        if config is not None:
            # We used to deepcopy, but for now we are trying to just save
            # by reference.  This *could* have side effects as all components
            # will share config. In fact, I did find such a side effect in
            # _config_changed below. If a config attribute value was a mutable type
            # all instances of a component were getting the same copy, effectively
            # making that a class attribute.
            # self.config = deepcopy(config)
            self.config = config
        # This should go second so individual keyword arguments override 
        # the values in config.
        super(Configurable, self).__init__(**kwargs)
        self.created = datetime.datetime.now()

    #-------------------------------------------------------------------------
    # Static trait notifiations
    #-------------------------------------------------------------------------

    def _config_changed(self, name, old, new):
        """Update all the class traits having ``config=True`` as metadata.

        For any class trait with a ``config`` metadata attribute that is
        ``True``, we update the trait with the value of the corresponding
        config entry.
        """
        # Get all traits with a config metadata entry that is True
        traits = self.traits(config=True)

        # We auto-load config section for this class as well as any parent
        # classes that are Configurable subclasses.  This starts with Configurable
        # and works down the mro loading the config for each section.
        section_names = [cls.__name__ for cls in \
            reversed(self.__class__.__mro__) if 
            issubclass(cls, Configurable) and issubclass(self.__class__, cls)]

        for sname in section_names:
            # Don't do a blind getattr as that would cause the config to 
            # dynamically create the section with name self.__class__.__name__.
            if new._has_section(sname):
                my_config = new[sname]
                for k, v in traits.iteritems():
                    # Don't allow traitlets with config=True to start with
                    # uppercase.  Otherwise, they are confused with Config
                    # subsections.  But, developers shouldn't have uppercase
                    # attributes anyways! (PEP 6)
                    if k[0].upper()==k[0] and not k.startswith('_'):
                        raise ConfigurableError('Configurable traitlets with '
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

    @classmethod
    def class_get_shortnames(cls):
        """Return the shortname to fullname dict for config=True traits."""
        cls_traits = cls.class_traits(config=True)
        shortnames = {}
        for k, v in cls_traits.items():
            shortname = v.get_metadata('shortname')
            if shortname is not None:
                longname = cls.__name__ + '.' + k
                shortnames[shortname] = longname
        return shortnames

    @classmethod
    def class_get_help(cls):
        """Get the help string for this class in ReST format."""
        cls_traits = cls.class_traits(config=True)
        final_help = []
        final_help.append(u'%s options' % cls.__name__)
        final_help.append(len(final_help[0])*u'-')
        for k, v in cls_traits.items():
            help = v.get_metadata('help')
            shortname = v.get_metadata('shortname')
            header = "%s.%s : %s" % (cls.__name__, k, v.__class__.__name__)
            if shortname is not None:
                header += " (shortname=" + shortname + ")"
            final_help.append(header)
            if help is not None:
                final_help.append(indent(help))
        return '\n'.join(final_help)

    @classmethod
    def class_print_help(cls):
        print cls.class_get_help()


class SingletonConfigurable(Configurable):
    """A configurable that only allows one instance.

    This class is for classes that should only have one instance of itself
    or *any* subclass. To create and retrieve such a class use the
    :meth:`SingletonConfigurable.instance` method.
    """

    _instance = None

    @classmethod
    def instance(cls, *args, **kwargs):
        """Returns a global instance of this class.

        This method create a new instance if none have previously been created
        and returns a previously created instance is one already exists.

        The arguments and keyword arguments passed to this method are passed
        on to the :meth:`__init__` method of the class upon instantiation.

        Examples
        --------

        Create a singleton class using instance, and retrieve it::

            >>> from IPython.config.configurable import SingletonConfigurable
            >>> class Foo(SingletonConfigurable): pass
            >>> foo = Foo.instance()
            >>> foo == Foo.instance()
            True

        Create a subclass that is retrived using the base class instance::

            >>> class Bar(SingletonConfigurable): pass
            >>> class Bam(Bar): pass
            >>> bam = Bam.instance()
            >>> bam == Bar.instance()
            True
        """
        # Create and save the instance
        if cls._instance is None:
            inst = cls(*args, **kwargs)
            # Now make sure that the instance will also be returned by
            # the subclasses instance attribute.
            for subclass in cls.mro():
                if issubclass(cls, subclass) and \
                issubclass(subclass, SingletonConfigurable) and \
                subclass != SingletonConfigurable:
                    subclass._instance = inst
                else:
                    break
        if isinstance(cls._instance, cls):
            return cls._instance
        else:
            raise MultipleInstanceError(
                'Multiple incompatible subclass instances of '
                '%s are being created.' % cls.__name__
            )
