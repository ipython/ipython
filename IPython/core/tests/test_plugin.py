"""Tests for plugin.py"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from unittest import TestCase

from IPython.core.plugin import Plugin, PluginManager

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class FooPlugin(Plugin):
    pass


class BarPlugin(Plugin):
    pass


class BadPlugin(object):
    pass


class PluginTest(TestCase):

    def setUp(self):
        self.manager = PluginManager()

    def test_register_get(self):
        self.assertEquals(None, self.manager.get_plugin('foo'))
        foo = FooPlugin()
        self.manager.register_plugin('foo', foo)
        self.assertEquals(foo, self.manager.get_plugin('foo'))
        bar = BarPlugin()
        self.assertRaises(KeyError, self.manager.register_plugin, 'foo', bar)
        bad = BadPlugin()
        self.assertRaises(TypeError, self.manager.register_plugin, 'bad')

    def test_unregister(self):
        foo = FooPlugin()
        self.manager.register_plugin('foo', foo)
        self.manager.unregister_plugin('foo')
        self.assertEquals(None, self.manager.get_plugin('foo'))
