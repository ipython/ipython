# coding: utf-8
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

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import shutil
import sys
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from tempfile import TemporaryDirectory

from IPython.core.profileapp import list_bundled_profiles, list_profiles_in
from IPython.core.profiledir import ProfileDir
from IPython.testing import decorators as dec
from IPython.testing import tools as tt
from IPython.utils.process import getoutput

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------
TMP_TEST_DIR = Path(tempfile.mkdtemp())
HOME_TEST_DIR = TMP_TEST_DIR / "home_test_dir"
IP_TEST_DIR = HOME_TEST_DIR / ".ipython"

#
# Setup/teardown functions/decorators
#

def setup_module():
    """Setup test environment for the module:

            - Adds dummy home dir tree
    """
    # Do not mask exceptions here.  In particular, catching WindowsError is a
    # problem because that exception is only defined on Windows...
    (Path.cwd() / IP_TEST_DIR).mkdir(parents=True)


def teardown_module():
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
class ProfileStartupTest(TestCase):
    def setUp(self):
        # create profile dir
        self.pd = ProfileDir.create_profile_dir_by_name(IP_TEST_DIR, "test")
        self.options = ["--ipython-dir", IP_TEST_DIR, "--profile", "test"]
        self.fname = TMP_TEST_DIR / "test.py"

    def tearDown(self):
        # We must remove this profile right away so its presence doesn't
        # confuse other tests.
        shutil.rmtree(self.pd.location)

    def init(self, startup_file, startup, test):
        # write startup python file
        with open(Path(self.pd.startup_dir) / startup_file, "w", encoding="utf-8") as f:
            f.write(startup)
        # write simple test file, to check that the startup file was run
        with open(self.fname, "w", encoding="utf-8") as f:
            f.write(test)

    def validate(self, output):
        tt.ipexec_validate(self.fname, output, "", options=self.options)

def test_wierd():
    TMP = Path(tempfile.mkdtemp())
    td = Path(tempfile.mkdtemp(dir=TMP))
    p = Path(td / "profile_ünicode2")
    p.mkdir(parents=True)

    with open(td / "profile_file", "w", encoding="utf-8") as f:
        f.write("I am not a profile directory")

    things = [s.name for s in os.scandir(td)]
    assert set(things) == {"profile_ünicode2", "profile_file"}

    shutil.rmtree(str(p))


def test_list_profiles_in():
    # No need to remove these directories and files, as they will get nuked in
    # the module-level teardown.
    td = Path(tempfile.mkdtemp(dir=TMP_TEST_DIR))
    for name in ("profile_foo", "profile_hello", "not_a_profile"):
        Path(td / name).mkdir(parents=True)
    if dec.unicode_paths:
        Path(td / "profile_ünicode").mkdir(parents=True)

    with open(td / "profile_file", "w", encoding="utf-8") as f:
        f.write("I am not a profile directory")
    profiles = list_profiles_in(td)

    # unicode normalization can turn u'ünicode' into u'u\0308nicode',
    # so only check for *nicode, and that creating a ProfileDir from the
    # name remains valid
    found_unicode = False
    assert set(list(profiles)) == {"foo", "hello", "ünicode"}
    for p in list(profiles):
        if p.endswith('nicode'):
            pd = ProfileDir.find_profile_dir_by_name(td, p)
            profiles.remove(p)
            found_unicode = True
            break
    if dec.unicode_paths:
        assert found_unicode is True
    assert set(profiles) == {"foo", "hello"}
