"""
Contains tests class for reader.py
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from .base import TestsBase

from ..reader import read, get_version

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class TestReader(TestsBase):

    def test_read(self):
        """Can older notebooks be opened without modification?"""

        # Open a version 3 notebook.  Make sure it is still version 3.
        with self.fopen(u'test3.ipynb', u'r') as f:
            nb = read(f)
        (major, minor) = get_version(nb)
        self.assertEqual(major, 3)

        # Open a version 2 notebook.  Make sure it is still version 2.
        with self.fopen(u'test2.ipynb', u'r') as f:
            nb = read(f)
        (major, minor) = get_version(nb)
        self.assertEqual(major, 2)
