"""
Contains tests class for current.py
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .base import TestsBase

from ..reader import get_version
from ..current import read, current_nbformat

class TestCurrent(TestsBase):

    def test_read_v2(self):
        """Can v2 notebooks be opened into the current nbformat?"""

        # Open a version 2 notebook.
        with self.fopen(u'test2.ipynb', u'r') as f:
            nb = read(f, u'json')

        # Check that the notebook was upgraded to the latest version automatically.
        (major, minor) = get_version(nb)
        self.assertEqual(major, current_nbformat)

    def test_read_v4(self):
        """Can v4 notebooks be opened into the current nbformat?"""
        
        # open a v4 notebook
        with self.fopen(u'test4.ipynb', u'r') as f:
            nb = read(f, u'json')

        # Check that the notebook was converted to current automatically.
        (major, minor) = get_version(nb)
        self.assertEqual(major, current_nbformat)
