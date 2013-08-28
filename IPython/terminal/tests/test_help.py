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

from IPython.testing.tools import help, help_all

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


@help()
def test_ipython_help():
    pass

@help_all()
def test_ipython_help_all():
    pass

@help("profile")
def test_profile_help():
    pass

@help_all("profile")
def test_profile_help_all():
    pass

@help("profile list")
def test_profile_list_help():
    pass

@help_all("profile list")
def test_profile_list_help_all():
    pass

@help("profile create")
def test_profile_create_help():
    pass

@help_all("profile create")
def test_profile_create_help_all():
    pass

@help("locate")
def test_locate_help():
    pass

@help_all("locate")
def test_locate_help_all():
    pass

@help("locate profile")
def test_locate_profile_help():
    pass

@help_all("locate profile")
def test_locate_profile_all():
    pass
