"""Tests for IPython.lib.display.

"""
#-----------------------------------------------------------------------------
# Copyright (c) 2012, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Third-party imports
import nose.tools as nt

# Our own imports
from IPython.lib import display

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

#--------------------------
# FileLink tests
#--------------------------

def test_instantiation_FileLink():
    """Test classes can be instantiated"""
    fl = display.FileLink('example.txt')

def test_warning_on_non_existant_path_FileLink():
    """Calling _repr_html_ on non-existant files returns a warning"""
    fl = display.FileLink('example.txt')
    nt.assert_true(fl._repr_html_().startswith('Path (<tt>example.txt</tt>)'))

#--------------------------
# FileLinks tests
#--------------------------

def test_instantiation_FileLinks():
    """Test classes can be instantiated"""
    fls = display.FileLinks(['example1.txt','example2.txt'])

def test_warning_on_non_existant_path_FileLinks():
    """Calling _repr_html_ on non-existant files returns a warning"""
    fls = display.FileLinks('example')
    nt.assert_true(fls._repr_html_().startswith('Path (<tt>example</tt>)'))

#--------------------------
# DirectoryLink tests
#--------------------------

def test_instantiation_DirectoryLink():
    """Test classes can be instantiated"""
    dl = display.DirectoryLink('example')

def test_warning_on_non_existant_path_DirectoryLink():
    """Calling _repr_html_ on non-existant files returns a warning"""
    dl = display.DirectoryLink('example')
    nt.assert_true(dl._repr_html_().startswith('Path (<tt>example</tt>)'))
