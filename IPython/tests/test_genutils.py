# encoding: utf-8

"""Tests for genutils.py"""

__docformat__ = "restructuredtext en"

#-----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython import genutils


def test_get_home_dir():
    """Make sure we can get the home directory."""
    home_dir = genutils.get_home_dir()

def test_get_ipython_dir():
    """Make sure we can get the ipython directory."""
    ipdir = genutils.get_ipython_dir()

def test_get_security_dir():
    """Make sure we can get the ipython/security directory."""
    sdir = genutils.get_security_dir()
    