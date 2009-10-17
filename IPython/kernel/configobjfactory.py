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

from IPython.core.component import Component

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class IConfiguredObjectFactory(zi.Interface):
    """I am a component that creates a configured object.

    This class is useful if you want to configure a class that is not a 
    subclass of :class:`IPython.core.component.Component`.
    """

    def __init__(config):
        """Get ready to configure the object using config."""

    def create():
        """Return an instance of the configured object."""


class ConfiguredObjectFactory(Component):

    zi.implements(IConfiguredObjectFactory)

    def __init__(self, config):
        super(ConfiguredObjectFactory, self).__init__(None, config=config)

    def create(self):
        raise NotImplementedError('create must be implemented in a subclass')


class IAdaptedConfiguredObjectFactory(zi.Interface):
    """I am a component that adapts and configures an object.

    This class is useful if you have the adapt a instance and configure it.
    """

    def __init__(config, adaptee=None):
        """Get ready to adapt adaptee and then configure it using config."""

    def create():
        """Return an instance of the adapted and configured object."""


class AdaptedConfiguredObjectFactory(Component):

    # zi.implements(IAdaptedConfiguredObjectFactory)

    def __init__(self, config, adaptee):
        super(AdaptedConfiguredObjectFactory, self).__init__(None, config=config)
        self.adaptee = adaptee

    def create(self):
        raise NotImplementedError('create must be implemented in a subclass')