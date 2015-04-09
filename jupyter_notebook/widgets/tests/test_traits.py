"""Test trait types of the widget packages."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from unittest import TestCase
from IPython.utils.traitlets import HasTraits
from traitlets.tests.test_traitlets import TraitTestBase
from jupyter_notebook.widgets import Color, EventfulDict, EventfulList


class ColorTrait(HasTraits):
    value = Color("black")


class TestColor(TraitTestBase):
    obj = ColorTrait()

    _good_values = ["blue", "#AA0", "#FFFFFF"]
    _bad_values = ["vanilla", "blues"]


class TestEventful(TestCase):

    def test_list(self):
        """Does the EventfulList work?"""
        event_cache = []

        class A(HasTraits):
            x = EventfulList([c for c in 'abc'])
        a = A()
        a.x.on_events(lambda i, x: event_cache.append('insert'), \
            lambda i, x: event_cache.append('set'), \
            lambda i: event_cache.append('del'), \
            lambda: event_cache.append('reverse'), \
            lambda *p, **k: event_cache.append('sort'))

        a.x.remove('c')
        # ab
        a.x.insert(0, 'z')
        # zab
        del a.x[1]
        # zb
        a.x.reverse()
        # bz 
        a.x[1] = 'o'
        # bo
        a.x.append('a')
        # boa
        a.x.sort()
        # abo

        # Were the correct events captured?
        self.assertEqual(event_cache, ['del', 'insert', 'del', 'reverse', 'set', 'set', 'sort'])

        # Is the output correct?
        self.assertEqual(a.x, [c for c in 'abo'])

    def test_dict(self):
        """Does the EventfulDict work?"""
        event_cache = []

        class A(HasTraits):
            x = EventfulDict({c: c for c in 'abc'})
        a = A()
        a.x.on_events(lambda k, v: event_cache.append('add'), \
            lambda k, v: event_cache.append('set'), \
            lambda k: event_cache.append('del'))

        del a.x['c']
        # ab
        a.x['z'] = 1
        # abz
        a.x['z'] = 'z'
        # abz
        a.x.pop('a')
        # bz 

        # Were the correct events captured?
        self.assertEqual(event_cache, ['del', 'add', 'set', 'del'])

        # Is the output correct?
        self.assertEqual(a.x, {c: c for c in 'bz'})
