"""
Contains tests class for current.py
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

from ..reader import get_version
from ..current import read, current_nbformat

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class TestCurrent(TestsBase):

    def test_read(self):
        """Can older notebooks be opened and automatically converted to the current 
        nbformat?"""

        # Open a version 2 notebook.
        with self.fopen(u'test2.ipynb', u'r') as f:
            nb = read(f, u'json')

        # Check that the notebook was upgraded to the latest version automatically.
        (major, minor) = get_version(nb)
        self.assertEqual(major, current_nbformat)
