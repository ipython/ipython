#!/usr/bin/env python
# encoding: utf-8
"""
Tests for IPython.core.component

Authors:

* Brian Granger
* Fernando Perez (design help)
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

from unittest import TestCase

from IPython.core.component import Component


#-----------------------------------------------------------------------------
# Test cases
#-----------------------------------------------------------------------------


class TestComponentMeta(TestCase):

    def test_get_instances(self):
        class BaseComponent(Component):
            pass
        c1 = BaseComponent(None)
        c2 = BaseComponent(c1)
        self.assertEquals(BaseComponent.get_instances(),[c1,c2])


class TestComponent(TestCase):

    def test_parent_child(self):
        c1 = Component(None)
        c2 = Component(c1)
        c3 = Component(c1)
        c4 = Component(c3)
        self.assertEquals(c1.parent, None)
        self.assertEquals(c2.parent, c1)
        self.assertEquals(c3.parent, c1)
        self.assertEquals(c4.parent, c3)
        self.assertEquals(c1.children, [c2, c3])
        self.assertEquals(c2.children, [])
        self.assertEquals(c3.children, [c4])
        self.assertEquals(c4.children, [])

    def test_root(self):
        c1 = Component(None)
        c2 = Component(c1)
        c3 = Component(c1)
        c4 = Component(c3)
        self.assertEquals(c1.root, c1.root)
        self.assertEquals(c2.root, c1)
        self.assertEquals(c3.root, c1)
        self.assertEquals(c4.root, c1)
