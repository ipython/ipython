"""Tests for profile-related functions.

Currently only the startup-dir functionality is tested, but more tests should
be added for:

    * ipython profile create
    * ipython profile list
    * ipython profile create --parallel
    * security dir permissions

Authors
-------

* MinRK

"""
from __future__ import absolute_import

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import shutil
import sys
import tempfile

import nose.tools as nt
from nose import SkipTest

from IPython.core.profiledir import ProfileDir

from IPython.testing import decorators as dec
from IPython.testing import tools as tt
from IPython.utils import py3compat


#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------
TMP_TEST_DIR = tempfile.mkdtemp()
HOME_TEST_DIR = os.path.join(TMP_TEST_DIR, "home_test_dir")
IP_TEST_DIR = os.path.join(HOME_TEST_DIR,'.ipython')

#
# Setup/teardown functions/decorators
#

def setup():
    """Setup test environment for the module:

            - Adds dummy home dir tree
    """
    # Do not mask exceptions here.  In particular, catching WindowsError is a
    # problem because that exception is only defined on Windows...
    os.makedirs(IP_TEST_DIR)


def teardown():
    """Teardown test environment for the module:

            - Remove dummy home dir tree
    """
    # Note: we remove the parent test dir, which is the root of all test
    # subdirs we may have created.  Use shutil instead of os.removedirs, so
    # that non-empty directories are all recursively removed.
    shutil.rmtree(TMP_TEST_DIR)


#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------
def win32_without_pywin32():
    if sys.platform == 'win32':
        try:
            import pywin32
        except ImportError:
            return True
    return False
    

@dec.skipif(win32_without_pywin32(), "Test requires pywin32 on Windows")
def test_startup_py():
    # create profile dir
    pd = ProfileDir.create_profile_dir_by_name(IP_TEST_DIR, 'test')
    # write startup python file
    with open(os.path.join(pd.startup_dir, '00-start.py'), 'w') as f:
        f.write('zzz=123\n')
    # write simple test file, to check that the startup file was run
    fname = os.path.join(TMP_TEST_DIR, 'test.py')
    with open(fname, 'w') as f:
        f.write(py3compat.doctest_refactor_print('print zzz\n'))
    # validate output
    tt.ipexec_validate(fname, '123', '', 
        options=['--ipython-dir', IP_TEST_DIR, '--profile', 'test'])

@dec.skipif(win32_without_pywin32(), "Test requires pywin32 on Windows")
def test_startup_ipy():
    # create profile dir
    pd = ProfileDir.create_profile_dir_by_name(IP_TEST_DIR, 'test')
    # write startup ipython file
    with open(os.path.join(pd.startup_dir, '00-start.ipy'), 'w') as f:
        f.write('%profile\n')
    # write empty script, because we don't need anything to happen
    # after the startup file is run
    fname = os.path.join(TMP_TEST_DIR, 'test.py')
    with open(fname, 'w') as f:
        f.write('')
    # validate output
    tt.ipexec_validate(fname, 'test', '', 
        options=['--ipython-dir', IP_TEST_DIR, '--profile', 'test'])
    
    
