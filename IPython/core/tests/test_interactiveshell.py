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
from IPython.testing import decorators as dec

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

    def test_run_empty_cell(self):
        """Just make sure we don't get a horrible error with a blank
        cell of input. Yes, I did overlook that."""
        ip = get_ipython()
        old_xc = ip.execution_count
        ip.run_cell('')
        self.assertEquals(ip.execution_count, old_xc)

    def test_run_cell_multiline(self):
        """Multi-block, multi-line cells must execute correctly.
        """
        ip = get_ipython()
        src = '\n'.join(["x=1",
                         "y=2",
                         "if 1:",
                         "    x += 1",
                         "    y += 1",])
        ip.run_cell(src)
        self.assertEquals(ip.user_ns['x'], 2)
        self.assertEquals(ip.user_ns['y'], 3)

    def test_multiline_string_cells(self):
        "Code sprinkled with multiline strings should execute (GH-306)"
        ip = get_ipython()
        ip.run_cell('tmp=0')
        self.assertEquals(ip.user_ns['tmp'], 0)
        ip.run_cell('tmp=1;"""a\nb"""\n')
        self.assertEquals(ip.user_ns['tmp'], 1)

    def test_dont_cache_with_semicolon(self):
        "Ending a line with semicolon should not cache the returned object (GH-307)"
        ip = get_ipython()
        oldlen = len(ip.user_ns['Out'])
        a = ip.run_cell('1;')
        newlen = len(ip.user_ns['Out'])
        self.assertEquals(oldlen, newlen)
        #also test the default caching behavior
        ip.run_cell('1')
        newlen = len(ip.user_ns['Out'])
        self.assertEquals(oldlen+1, newlen)

    def test_In_variable(self):
        "Verify that In variable grows with user input (GH-284)"
        ip = get_ipython()
        oldlen = len(ip.user_ns['In'])
        ip.run_cell('1;')
        newlen = len(ip.user_ns['In'])
        self.assertEquals(oldlen+1, newlen)
        self.assertEquals(ip.user_ns['In'][-1],'1;')
