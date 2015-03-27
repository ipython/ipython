"""
Contains base test class for nbformat
"""
#-----------------------------------------------------------------------------
#Copyright (c) 2013, the IPython Development Team.
#
#Distributed under the terms of the Modified BSD License.
#
#The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import unittest

import IPython

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class TestsBase(unittest.TestCase):
    """Base tests class."""

    def fopen(self, f, mode=u'r'):
        return open(os.path.join(self._get_files_path(), f), mode)


    def _get_files_path(self):
        return os.path.dirname(__file__)
