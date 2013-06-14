# encoding: utf-8
"""
A base class for objects that are configurable.

Inheritance diagram:

.. inheritance-diagram:: IPython.config.configurable
   :parts: 3

Authors:

* Brian Granger
* Fernando Perez
* Min RK
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

import datetime
from copy import deepcopy

from loader import Config
from IPython.utils.traitlets import HasTraits, Instance
from IPython.utils.text import indent, wrap_paragraphs


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

    config = Instance(Config, (), {})
    parent = Instance('IPython.config.configurable.Configurable')
    created = None

    def __init__(self, **kwargs):
        """Create a configurable given a config config.

        Parameters
        ----------
        config : Config
            If this is empty, default values are used. If config is a
            :class:`Config` instance, it will be used to configure the
            instance.
        parent : Configurable instance
            The parent

        Notes
        -----
        Subclasses of Configurable must call the :meth:`__init__` method of
        :class:`Configurable` *before* doing anything else and using
        :func:`super`::

            class MyConfigurable(Configurable):
                def __init__(self, config=None):
                    super(MyConfigurable, self).__init__(config=config)
                    # Then any other code you need to finish initialization.

        This ensures that instances will be configured properly.
        """
        parent = kwargs.pop('parent', None)
        if parent:
            # config is implied from parent
            if kwargs.get('config', None) is None:
                kwargs['config'] = parent.config
            self.parent = parent
        
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
    
    @classmethod
    def section_names(cls):
        """return section names as a list"""
        return  [c.__name__ for c in reversed(cls.__mro__) if
            issubclass(c, Configurable) and issubclass(cls, c)
        ]

    def _load_config(self, cfg, section_names=None, traits=None):
        """load traits from a Config object"""
        
        if traits is None:
            traits = self.traits(config=True)
        if section_names is None:
            section_names = self.section_names()
        
        for sname in section_names:
            # Don't do a blind getattr as that would cause the config to
            # dynamically create the section with name self.__class__.__name__.
            if cfg._has_section(sname):
                my_config = cfg[sname]
                for k, v in traits.iteritems():
                    try:
                        # Here we grab the value from the config
                        # If k has the naming convention of a config
                        # section, it will be auto created.
                        config_value = my_config[k]
                    except KeyError:
                        pass
                    else:
                        # We have to do a deepcopy here if we don't deepcopy the entire
                        # config object. If we don't, a mutable config_value will be
                        # shared by all instances, effectively making it a class attribute.
                        setattr(self, k, deepcopy(config_value))

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
        section_names = self.section_names()
        self._load_config(new, traits=traits, section_names=section_names)
        
        # load parent config as well, if we have one
        parent_section_names = [] if self.parent is None else self.parent.section_names()
        for parent in parent_section_names:
            if not new._has_section(parent):
                continue
            self._load_config(new[parent], traits=traits, section_names=section_names)

    def update_config(self, config):
        """Fire the traits events when the config is updated."""
        # Save a copy of the current config.
        newconfig = deepcopy(self.config)
        # Merge the new config into the current one.
        newconfig.merge(config)
        # Save the combined config as self.config, which triggers the traits
        # events.
        self.config = newconfig

    @classmethod
    def class_get_help(cls, inst=None):
        """Get the help string for this class in ReST format.
        
        If `inst` is given, it's current trait values will be used in place of
        class defaults.
        """
        assert inst is None or isinstance(inst, cls)
        final_help = []
        final_help.append(u'%s options' % cls.__name__)
        final_help.append(len(final_help[0])*u'-')
        for k, v in sorted(cls.class_traits(config=True).iteritems()):
            help = cls.class_get_trait_help(v, inst)
            final_help.append(help)
        return '\n'.join(final_help)

    @classmethod
    def class_get_trait_help(cls, trait, inst=None):
        """Get the help string for a single trait.
        
        If `inst` is given, it's current trait values will be used in place of
        the class default.
        """
        assert inst is None or isinstance(inst, cls)
        lines = []
        header = "--%s.%s=<%s>" % (cls.__name__, trait.name, trait.__class__.__name__)
        lines.append(header)
        if inst is not None:
            lines.append(indent('Current: %r' % getattr(inst, trait.name), 4))
        else:
            try:
                dvr = repr(trait.get_default_value())
            except Exception:
                dvr = None # ignore defaults we can't construct
            if dvr is not None:
                if len(dvr) > 64:
                    dvr = dvr[:61]+'...'
                lines.append(indent('Default: %s' % dvr, 4))
        if 'Enum' in trait.__class__.__name__:
            # include Enum choices
            lines.append(indent('Choices: %r' % (trait.values,)))

        help = trait.get_metadata('help')
        if help is not None:
            help = '\n'.join(wrap_paragraphs(help, 76))
            lines.append(indent(help, 4))
        return '\n'.join(lines)

    @classmethod
    def class_print_help(cls, inst=None):
        """Get the help string for a single trait and print it."""
        print cls.class_get_help(inst)

    @classmethod
    def class_config_section(cls):
        """Get the config class config section"""
        def c(s):
            """return a commented, wrapped block."""
            s = '\n\n'.join(wrap_paragraphs(s, 78))

            return '# ' + s.replace('\n', '\n# ')

        # section header
        breaker = '#' + '-'*78
        s = "# %s configuration" % cls.__name__
        lines = [breaker, s, breaker, '']
        # get the description trait
        desc = cls.class_traits().get('description')
        if desc:
            desc = desc.default_value
        else:
            # no description trait, use __doc__
            desc = getattr(cls, '__doc__', '')
        if desc:
            lines.append(c(desc))
            lines.append('')

        parents = []
        for parent in cls.mro():
            # only include parents that are not base classes
            # and are not the class itself
            # and have some configurable traits to inherit
            if parent is not cls and issubclass(parent, Configurable) and \
                    parent.class_traits(config=True):
                parents.append(parent)

        if parents:
            pstr = ', '.join([ p.__name__ for p in parents ])
            lines.append(c('%s will inherit config from: %s'%(cls.__name__, pstr)))
            lines.append('')

        for name, trait in cls.class_traits(config=True).iteritems():
            help = trait.get_metadata('help') or ''
            lines.append(c(help))
            lines.append('# c.%s.%s = %r'%(cls.__name__, name, trait.get_default_value()))
            lines.append('')
        return '\n'.join(lines)



class SingletonConfigurable(Configurable):
    """A configurable that only allows one instance.

    This class is for classes that should only have one instance of itself
    or *any* subclass. To create and retrieve such a class use the
    :meth:`SingletonConfigurable.instance` method.
    """

    _instance = None

    @classmethod
    def _walk_mro(cls):
        """Walk the cls.mro() for parent classes that are also singletons

        For use in instance()
        """

        for subclass in cls.mro():
            if issubclass(cls, subclass) and \
                    issubclass(subclass, SingletonConfigurable) and \
                    subclass != SingletonConfigurable:
                yield subclass

    @classmethod
    def clear_instance(cls):
        """unset _instance for this class and singleton parents.
        """
        if not cls.initialized():
            return
        for subclass in cls._walk_mro():
            if isinstance(subclass._instance, cls):
                # only clear instances that are instances
                # of the calling class
                subclass._instance = None

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
            # parent classes' _instance attribute.
            for subclass in cls._walk_mro():
                subclass._instance = inst

        if isinstance(cls._instance, cls):
            return cls._instance
        else:
            raise MultipleInstanceError(
                'Multiple incompatible subclass instances of '
                '%s are being created.' % cls.__name__
            )

    @classmethod
    def initialized(cls):
        """Has an instance been created?"""
        return hasattr(cls, "_instance") and cls._instance is not None


class LoggingConfigurable(Configurable):
    """A parent class for Configurables that log.

    Subclasses have a log trait, and the default behavior
    is to get the logger from the currently running Application
    via Application.instance().log.
    """

    log = Instance('logging.Logger')
    def _log_default(self):
        from IPython.config.application import Application
        return Application.instance().log


