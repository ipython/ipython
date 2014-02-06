"""Test HTML utils"""

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

import nose.tools as nt

import IPython.testing.tools as tt
from IPython.html.utils import url_escape, url_unescape, is_hidden
from IPython.utils.tempdir import TemporaryDirectory

#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------

def test_help_output():
    """ipython notebook --help-all works"""
    tt.help_all_output_test('notebook')


def test_url_escape():

    # changes path or notebook name with special characters to url encoding
    # these tests specifically encode paths with spaces
    path = url_escape('/this is a test/for spaces/')
    nt.assert_equal(path, '/this%20is%20a%20test/for%20spaces/')

    path = url_escape('notebook with space.ipynb')
    nt.assert_equal(path, 'notebook%20with%20space.ipynb')

    path = url_escape('/path with a/notebook and space.ipynb')
    nt.assert_equal(path, '/path%20with%20a/notebook%20and%20space.ipynb')
    
    path = url_escape('/ !@$#%^&* / test %^ notebook @#$ name.ipynb')
    nt.assert_equal(path,
        '/%20%21%40%24%23%25%5E%26%2A%20/%20test%20%25%5E%20notebook%20%40%23%24%20name.ipynb')

def test_url_unescape():

    # decodes a url string to a plain string
    # these tests decode paths with spaces
    path = url_unescape('/this%20is%20a%20test/for%20spaces/')
    nt.assert_equal(path, '/this is a test/for spaces/')

    path = url_unescape('notebook%20with%20space.ipynb')
    nt.assert_equal(path, 'notebook with space.ipynb')

    path = url_unescape('/path%20with%20a/notebook%20and%20space.ipynb')
    nt.assert_equal(path, '/path with a/notebook and space.ipynb')

    path = url_unescape(
        '/%20%21%40%24%23%25%5E%26%2A%20/%20test%20%25%5E%20notebook%20%40%23%24%20name.ipynb')
    nt.assert_equal(path, '/ !@$#%^&* / test %^ notebook @#$ name.ipynb')

def test_is_hidden():
    with TemporaryDirectory() as root:
        subdir1 = os.path.join(root, 'subdir')
        os.makedirs(subdir1)
        nt.assert_equal(is_hidden(subdir1, root), False)
        subdir2 = os.path.join(root, '.subdir2')
        os.makedirs(subdir2)
        nt.assert_equal(is_hidden(subdir2, root), True)
        subdir34 = os.path.join(root, 'subdir3', '.subdir4')
        os.makedirs(subdir34)
        nt.assert_equal(is_hidden(subdir34, root), True)
        nt.assert_equal(is_hidden(subdir34), True)
