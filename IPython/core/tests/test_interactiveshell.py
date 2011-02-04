"""Tests for the key interactiveshell module.

Historically the main classes in interactiveshell have been under-tested.  This
module should grow as many single-method tests as possible to trap many of the
recurring bugs we seem to encounter with high-level interaction.

Authors
-------
* Fernando Perez
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# stdlib
import unittest

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class InteractiveShellTestCase(unittest.TestCase):
    def test_naked_string_cells(self):
        """Test that cells with only naked strings are fully executed"""
        ip = get_ipython()
        # First, single-line inputs
        ip.run_cell('"a"\n')
        self.assertEquals(ip.user_ns['_'], 'a')
        # And also multi-line cells
        ip.run_cell('"""a\nb"""\n')
        self.assertEquals(ip.user_ns['_'], 'a\nb')
