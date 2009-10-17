#!/usr/bin/env python
# encoding: utf-8
"""
Simple tests for :mod:`IPython.extensions.pretty`.
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

import sys
from unittest import TestCase

from IPython.core.component import Component, masquerade_as
from IPython.core.iplib import InteractiveShell
from IPython.extensions import pretty as pretty_ext
from IPython.external import pretty

from IPython.utils.traitlets import Bool

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


class InteractiveShellStub(Component):
    pprint = Bool(True)

class A(object):
    pass

def a_pprinter(o, p, c):
    return p.text("<A>")

class TestPrettyResultDisplay(TestCase):

    def setUp(self):
        self.ip = InteractiveShellStub(None)
        # This allows our stub to be retrieved instead of the real InteractiveShell
        masquerade_as(self.ip, InteractiveShell)
        self.prd = pretty_ext.PrettyResultDisplay(self.ip, name='pretty_result_display')    

    def test_for_type(self):
        self.prd.for_type(A, a_pprinter)
        a = A()
        result = pretty.pretty(a)
        self.assertEquals(result, "<A>")


