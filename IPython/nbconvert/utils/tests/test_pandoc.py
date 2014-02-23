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
import warnings

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
        with self.assertRaises(pandoc.PandocMissing):
            pandoc.get_pandoc_version()
        with self.assertRaises(pandoc.PandocMissing):
            pandoc.check_pandoc_version()
        with self.assertRaises(pandoc.PandocMissing):
            pandoc.pandoc("", "markdown", "html")

        # original_env["PATH"] should contain pandoc
        os.environ["PATH"] = self.original_env["PATH"]
        with warnings.catch_warnings(record=True) as w:
            pandoc.get_pandoc_version()
            pandoc.check_pandoc_version()
            pandoc.pandoc("", "markdown", "html")
        self.assertEqual(w, [])
        
    @dec.onlyif_cmds_exist('pandoc')
    def test_minimal_version(self):
        original_minversion = pandoc._minimal_version
        
        pandoc._minimal_version = "120.0"
        with warnings.catch_warnings(record=True) as w:
            assert not pandoc.check_pandoc_version()
        self.assertEqual(len(w), 1)

        pandoc._minimal_version = pandoc.get_pandoc_version()
        assert pandoc.check_pandoc_version()


def pandoc_function_raised_missing(f, *args, **kwargs):
    try:
        f(*args, **kwargs)
    except pandoc.PandocMissing:
        return True
    else:
        return False
