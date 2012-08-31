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
from tempfile import NamedTemporaryFile, mkdtemp


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

def test_existing_path_FileLink():
    """ Calling _repr_html_ functions as expected on existing filepath """
    tf = NamedTemporaryFile()
    fl = display.FileLink(tf.name)
    actual = fl._repr_html_()
    # Note: this is a bit awkward since tf.name has to be a full path
    # for it to exist, but that won't happen in our applications. While
    # in practice "files/" would be prepended to the href path, os.join
    # doesn't do that if the second value is an absolute path. So, the
    # expected here is slightly different than what we get in practice.
    expected = "<a href='%s' target='_blank'>%s</a><br>" % (tf.name,tf.name)
    nt.assert_equal(actual,expected)

#--------------------------
# FileLinks tests
#--------------------------

def test_instantiation_FileLinks():
    """Test classes can be instantiated"""
    fls = display.FileLinks('example')

def test_warning_on_non_existant_path_FileLinks():
    """Calling _repr_html_ on non-existant files returns a warning"""
    fls = display.FileLinks('example')
    nt.assert_true(fls._repr_html_().startswith('Path (<tt>example</tt>)'))

def test_existing_path_FileLinks():
    """ Calling _repr_html_ functions as expected on existing directory """
    td = mkdtemp()
    tf1 = NamedTemporaryFile(dir=td)
    tf2 = NamedTemporaryFile(dir=td)
    fl = display.FileLinks(td)
    actual = fl._repr_html_()
    actual = actual.split('\n')
    actual.sort()
    # Note: this is a bit awkward since tf.name has to be a full path
    # for it to exist, but that won't happen in our applications. While
    # in practice "files/" would be prepended to the href path, os.join
    # doesn't do that if the second value is an absolute path. So, the
    # expected here is slightly different than what we get in practice.
    expected = ["<a href='%s' target='_blank'>%s</a><br>" % (tf2.name,tf2.name.split('/')[-1]),
                "<a href='%s' target='_blank'>%s</a><br>" % (tf1.name,tf1.name.split('/')[-1])]
    expected.sort()
    # We compare the sorted list of links here as that's more reliable
    nt.assert_equal(actual,expected)

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

def test_existing_path_FileLinks():
    """ Calling _repr_html_ functions as expected on existing directory """
    td = mkdtemp()
    dl = display.DirectoryLink(td)
    actual = dl._repr_html_()
    # Note: this is a bit awkward since tf.name has to be a full path
    # for it to exist, but that won't happen in our applications. While
    # in practice "files/" would be prepended to the href path, os.join
    # doesn't do that if the second value is an absolute path. So, the
    # expected here is slightly different than what we get in practice.
    expected = "<a href='%s' target='_blank'>%s</a><br>" % (td,td)
    nt.assert_equal(actual,expected)
