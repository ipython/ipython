"""
Module with tests for stdout
"""

#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys

from ...tests.base import TestsBase
from ..stdout import StdoutWriter
from IPython.utils.py3compat import PY3

if PY3:
    from io import StringIO
else:
    from StringIO import StringIO


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestStdout(TestsBase):
    """Contains test functions for stdout.py"""

    def test_output(self):
        """Test stdout writer output."""
        
        # Capture the stdout.  Remember original.
        stdout = sys.stdout
        stream = StringIO()
        sys.stdout = stream

        # Create stdout writer, test output
        writer = StdoutWriter()
        writer.write('a', {'b': 'c'})
        output = stream.getvalue()
        self.fuzzy_compare(output, 'a')

        # Revert stdout
        sys.stdout = stdout


    def test_utf_output(self):
        """Test stdout writer unicode output."""
        
        # Capture the stdout.  Remember original.
        stdout = sys.stdout
        stream = StringIO()
        sys.stdout = stream

        # Create stdout writer, test output
        writer = StdoutWriter()
        writer.write(u'\xC3\x97', {'b': 'c'})
        output = stream.getvalue()
        self.assertEqual(output, u'\xC3\x97')

        # Revert stdout
        sys.stdout = stdout