"""
Contains tests class for convert.py
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

from ..convert import convert
from ..reader import read, get_version
from ..current import current_nbformat

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class TestConvert(TestsBase):

    def test_downgrade(self):
        """Do notebook downgrades work?"""

        # Open a version 3 notebook and attempt to downgrade it to version 2.
        with self.fopen(u'test3.ipynb', u'r') as f:
            nb = read(f)
        nb = convert(nb, 2)

        # Check if downgrade was successful.
        (major, minor) = get_version(nb)
        self.assertEqual(major, 2)


    def test_upgrade(self):
        """Do notebook upgrades work?"""

        # Open a version 2 notebook and attempt to upgrade it to version 3.
        with self.fopen(u'test2.ipynb', u'r') as f:
            nb = read(f)
        nb = convert(nb, 3)

        # Check if upgrade was successful.
        (major, minor) = get_version(nb)
        self.assertEqual(major, 3)


    def test_open_current(self):
        """Can an old notebook be opened and converted to the current version 
        while remembering the original version of the notebook?"""

        # Open a version 2 notebook and attempt to upgrade it to the current version
        # while remembering it's version information.
        with self.fopen(u'test2.ipynb', u'r') as f:
            nb = read(f)
        (original_major, original_minor) = get_version(nb)
        nb = convert(nb, current_nbformat)

        # Check if upgrade was successful.
        (major, minor) = get_version(nb)
        self.assertEqual(major, current_nbformat)

        # Check if the original major revision was remembered.
        self.assertEqual(original_major, 2)
