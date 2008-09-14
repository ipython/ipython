# encoding: utf-8
# -*- test-case-name: IPython.frontend.tests.test_frontendbase -*-
"""
zope.interface mock. If zope is installed, this module provides a zope
interface classes, if not it provides mocks for them.

Classes provided: 
Interface, Attribute, implements, classProvides
"""
__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

try:
    from zope.interface import Interface, Attribute, implements, classProvides
except ImportError:
    #zope.interface is not available
    Interface = object
    def Attribute(name, doc): pass
    def implements(interface): pass
    def classProvides(interface): pass

