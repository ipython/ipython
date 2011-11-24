# encoding: utf-8
"""IPython plugins.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Dict

#-----------------------------------------------------------------------------
# Main class
#-----------------------------------------------------------------------------

class PluginManager(Configurable):
    """A manager for IPython plugins."""

    plugins = Dict({})

    def __init__(self, config=None):
        super(PluginManager, self).__init__(config=config)

    def register_plugin(self, name, plugin):
        if not isinstance(plugin, Plugin):
            raise TypeError('Expected Plugin, got: %r' % plugin)
        if self.plugins.has_key(name):
            raise KeyError('Plugin with name already exists: %r' % name)
        self.plugins[name] = plugin

    def unregister_plugin(self, name):
        del self.plugins[name]

    def get_plugin(self, name, default=None):
        return self.plugins.get(name, default)


class Plugin(Configurable):
    """Base class for IPython plugins."""
    pass
