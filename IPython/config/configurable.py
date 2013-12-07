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
from __future__ import print_function

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.external.traitlets import (Config, LazyConfigValue,
        HasTraits, Instance, ConfigurableError, MultipleInstanceError,
        Configurable, SingletonConfigurable
        )


#-----------------------------------------------------------------------------
# Configurable implementation
#-----------------------------------------------------------------------------

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


