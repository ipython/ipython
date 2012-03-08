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

from unittest import TestCase

import nose.tools as nt
from nose import SkipTest

from IPython.core.profileapp import list_profiles_in, list_bundled_profiles
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
    

class ProfileStartupTest(TestCase):
    def setUp(self):
        # create profile dir
        self.pd = ProfileDir.create_profile_dir_by_name(IP_TEST_DIR, 'test')
        self.options = ['--ipython-dir', IP_TEST_DIR, '--profile', 'test']
        self.fname = os.path.join(TMP_TEST_DIR, 'test.py')
        
    def tearDown(self):
        # We must remove this profile right away so its presence doesn't
        # confuse other tests.
        shutil.rmtree(self.pd.location)

    def init(self, startup_file, startup, test):
        # write startup python file
        with open(os.path.join(self.pd.startup_dir, startup_file), 'w') as f:
            f.write(startup)
        # write simple test file, to check that the startup file was run
        with open(self.fname, 'w') as f:
            f.write(py3compat.doctest_refactor_print(test))

    def validate(self, output):
        tt.ipexec_validate(self.fname, output, '', options=self.options)

    @dec.skipif(win32_without_pywin32(), "Test requires pywin32 on Windows")
    def test_startup_py(self):
        self.init('00-start.py', 'zzz=123\n', 
                  py3compat.doctest_refactor_print('print zzz\n'))
        self.validate('123')

    @dec.skipif(win32_without_pywin32(), "Test requires pywin32 on Windows")
    def test_startup_ipy(self):
        self.init('00-start.ipy', '%profile\n', '')
        self.validate('test')

    
def test_list_profiles_in():
    # No need to remove these directories and files, as they will get nuked in
    # the module-level teardown.
    prof_file = tempfile.NamedTemporaryFile(prefix='profile_', dir=IP_TEST_DIR)
    prof_dir = tempfile.mkdtemp(prefix='profile_', dir=IP_TEST_DIR)
    # Now, check that the profile listing doesn't get confused by files named
    # profile_X
    prof_name = os.path.split(prof_dir)[1].split('profile_')[1]
    profiles = list_profiles_in(IP_TEST_DIR)
    nt.assert_equals(profiles, [prof_name])
    

#def test_list_bundled_profiles():

