"""Test Pandoc module"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os

from .base import TestsBase
from ..utils import pandoc

from IPython.testing import decorators as dec

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------


#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class TestPandoc(TestsBase):
    """Collection of Pandoc tests"""

    def __init__(self, *args, **kwargs):
        super(TestPandoc, self).__init__(*args, **kwargs)
        self.original_env = os.environ.copy()

    @dec.onlyif_cmds_exist('pandoc')
    def test_pandoc_available(self):
        """ Test behaviour of pandoc_available() """
        os.environ["PATH"] = ""
        assert not pandoc.pandoc_available()
        try:
            pandoc.pandoc_available(failmode="raise")
        except pandoc.PandocMissing:
            assert True

        os.environ["PATH"] = self.original_env["PATH"]
        assert pandoc.pandoc_available()
        try:
            pandoc.pandoc_available(failmode="raise")
        except pandoc.PandocMissing:
            assert False
        
    @dec.onlyif_cmds_exist('pandoc')        
    def test_minimal_version(self):
        original_minversion = pandoc.minimal_version

        pandoc.minimal_version = "120.0"
        assert not pandoc.check_pandoc_version()

        pandoc.minimal_version = pandoc.get_pandoc_version()
        assert pandoc.check_pandoc_version()
        

        
