"""Test Pandoc module"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2014 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import os

from IPython.testing import decorators as dec

from IPython.nbconvert.tests.base import TestsBase
from .. import pandoc

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
        """ Test behaviour that pandoc functions raise PandocMissing as documented """
        pandoc.clean_cache()

        os.environ["PATH"] = ""
        assert pandoc_function_raised_missing(pandoc.get_pandoc_version) == True
        assert pandoc_function_raised_missing(pandoc.check_pandoc_version) == True
        assert pandoc_function_raised_missing(pandoc.pandoc, "", "markdown", "html") == True

        # original_env["PATH"] should contain pandoc
        os.environ["PATH"] = self.original_env["PATH"]
        assert pandoc_function_raised_missing(pandoc.get_pandoc_version) == False
        assert pandoc_function_raised_missing(pandoc.check_pandoc_version) == False
        assert pandoc_function_raised_missing(pandoc.pandoc, "", "markdown", "html") == False
        
    @dec.onlyif_cmds_exist('pandoc')
    def test_minimal_version(self):
        original_minversion = pandoc._minimal_version

        pandoc._minimal_version = "120.0"
        assert not pandoc.check_pandoc_version()

        pandoc._minimal_version = pandoc.get_pandoc_version()
        assert pandoc.check_pandoc_version()


def pandoc_function_raised_missing(f, *args, **kwargs):
    try:
        f(*args, **kwargs)
    except pandoc.PandocMissing:
        return True
    else:
        return False
