"""Test NotebookApp"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import nose.tools as nt

import IPython.testing.tools as tt

#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------

def test_help_output():
    """ipython notebook --help-all works"""
    tt.help_all_output_test('notebook')

