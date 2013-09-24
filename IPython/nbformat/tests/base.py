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

        #Get the relative path to this module in the IPython directory.
        names = self.__module__.split(u'.')[1:-1]
        
        #Build a path using the IPython directory and the relative path we just
        #found.
        path = IPython.__path__[0]
        for name in names:
            path = os.path.join(path, name)
        return path
