"""
Module with tests base for exporters
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

import os

from ...tests.base import TestsBase

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class ExportersTestsBase(TestsBase):
    """Contains base test functions for exporters"""

    def _get_notebook(self):
        return os.path.join(self._get_files_path(), 'notebook2.ipynb')
                