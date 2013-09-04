"""Test help output of various IPython entry points"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import IPython.testing.tools as tt

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


def test_ipython_help():
    tt.help_all_output_test()

def test_profile_help():
    tt.help_all_output_test("profile")

def test_profile_list_help():
    tt.help_all_output_test("profile list")

def test_profile_create_help():
    tt.help_all_output_test("profile create")

def test_locate_help():
    tt.help_all_output_test("locate")

def test_locate_profile_help():
    tt.help_all_output_test("locate profile")
