#!/usr/bin/env python
# encoding: utf-8
"""
A class for creating a Twisted service that is configured using IPython's
configuration system.
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

import zope.interface as zi

from IPython.config.configurable import Configurable

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class IConfiguredObjectFactory(zi.Interface):
    """I am a component that creates a configured object.

    This class is useful if you want to configure a class that is not a 
    subclass of :class:`IPython.config.configurable.Configurable`.
    """

    def __init__(config=None):
        """Get ready to configure the object using config."""

    def create():
        """Return an instance of the configured object."""


class ConfiguredObjectFactory(Configurable):

    zi.implements(IConfiguredObjectFactory)

    def __init__(self, config=None):
        super(ConfiguredObjectFactory, self).__init__(config=config)

    def create(self):
        raise NotImplementedError('create must be implemented in a subclass')


class IAdaptedConfiguredObjectFactory(zi.Interface):
    """I am a component that adapts and configures an object.

    This class is useful if you have the adapt an instance and configure it.
    """

    def __init__(config=None, adaptee=None):
        """Get ready to adapt adaptee and then configure it using config."""

    def create():
        """Return an instance of the adapted and configured object."""


class AdaptedConfiguredObjectFactory(Configurable):

    # zi.implements(IAdaptedConfiguredObjectFactory)

    def __init__(self, config=None, adaptee=None):
        # print
        # print "config pre:", config
        super(AdaptedConfiguredObjectFactory, self).__init__(config=config)
        # print
        # print "config post:", config
        self.adaptee = adaptee

    def create(self):
        raise NotImplementedError('create must be implemented in a subclass')
