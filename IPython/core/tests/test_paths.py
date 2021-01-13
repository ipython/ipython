import errno
from os import name as os_name
import shutil
import sys
import tempfile
import warnings
from pathlib import Path
from unittest.mock import patch

import nose.tools as nt
from testpath import modified_env, assert_isdir, assert_isfile

from IPython import paths
from IPython.testing.decorators import skip_win32
from IPython.utils.tempdir import TemporaryDirectory

TMP_TEST_DIR = Path(tempfile.mkdtemp()).resolve()
HOME_TEST_DIR = Path(TMP_TEST_DIR, "home_test_dir")
XDG_TEST_DIR = Path(HOME_TEST_DIR, "xdg_test_dir")
XDG_CACHE_DIR = Path(HOME_TEST_DIR, "xdg_cache_dir")
IP_TEST_DIR = Path(HOME_TEST_DIR, ".ipython")


def setup_module():
    """Setup testenvironment for the module:

            - Adds dummy home dir tree
    """
    # Do not mask exceptions here.  In particular, catching WindowsError is a
    # problem because that exception is only defined on Windows...
    IP_TEST_DIR.mkdir(parents=True)
    Path(XDG_TEST_DIR, "ipython").mkdir(parents=True)
    Path(XDG_CACHE_DIR, "ipython").mkdir(parents=True)


def teardown_module():
    """Teardown testenvironment for the module:

            - Remove dummy home dir tree
    """
    # Note: we remove the parent test dir, which is the root of all test
    # subdirs we may have created.  Use shutil instead of os.removedirs, so
    # that non-empty directories are all recursively removed.
    shutil.rmtree(TMP_TEST_DIR)

def patch_get_home_dir(dirpath):
    return patch.object(paths, 'get_home_dir', return_value=dirpath)


def test_get_ipython_dir_1():
    """test_get_ipython_dir_1, Testcase to see if we can call get_ipython_dir without Exceptions."""
    env_ipdir = Path("someplace", ".ipython")
    with patch.object(paths, "_writable_dir", return_value=True):
        with modified_env({"IPYTHONDIR": "%s" % env_ipdir}):
            ipdir = paths.get_ipython_dir()

    nt.assert_equal(ipdir, env_ipdir)

    # TODO Fix this test because `patch('os.name', "posix")` causes trouble
    # def test_get_ipython_dir_2():
    #     """test_get_ipython_dir_2, Testcase to see if we can call get_ipython_dir without Exceptions."""
    #     with patch_get_home_dir('someplace'), \
    #             patch.object(paths, 'get_xdg_dir', return_value=None), \
    #             patch.object(paths, '_writable_dir', return_value=True), \
    #                             patch('os.name', "posix"), \
    #                             modified_env({'IPYTHON_DIR': None,
    #                           'IPYTHONDIR': None,
    #                           'XDG_CONFIG_HOME': None
    #                          }):
    #         ipdir = paths.get_ipython_dir()

    nt.assert_equal(ipdir, Path("someplace", ".ipython"))

# TODO Fix this test because `patch('os.name', "posix")` causes trouble
# def test_get_ipython_dir_3():
#     """test_get_ipython_dir_3, move XDG if defined, and .ipython doesn't exist."""
#     tmphome = TemporaryDirectory()
#     try:
#         with patch_get_home_dir(tmphome.name), \
#                 patch('os.name', 'posix'), \
#                 modified_env({
#                 "IPYTHON_DIR": None,
#                 "IPYTHONDIR": None,
#                 "XDG_CONFIG_HOME": "%s" % XDG_TEST_DIR,
#             }
#         ), warnings.catch_warnings(record=True) as w:
#             ipdir = paths.get_ipython_dir()

#         nt.assert_equal(ipdir, Path(tmphome.name, ".ipython"))
#         if sys.platform != 'darwin':
#             nt.assert_equal(len(w), 1)
#             nt.assert_in('Moving', str(w[0]))
#     finally:
#         tmphome.cleanup()

# TODO Fix this test because `patch('os.name', "posix")` causes trouble
# def test_get_ipython_dir_4():
#     """test_get_ipython_dir_4, warn if XDG and home both exist."""
#     with patch_get_home_dir(HOME_TEST_DIR), \
#             patch('os.name', 'posix'):
#         try:
#             Path(XDG_TEST_DIR, "ipython").mkdir()
#         except OSError as e:
#             if e.errno != errno.EEXIST:
#                 raise

#         with modified_env(
#             {
#                 "IPYTHON_DIR": None,
#                 "IPYTHONDIR": None,
#                 "XDG_CONFIG_HOME": "%s" % XDG_TEST_DIR,
#             }
#         ):
#             with warnings.catch_warnings(record=True) as w:
#                 ipdir = paths.get_ipython_dir()

#         nt.assert_equal(ipdir, Path(HOME_TEST_DIR, ".ipython"))
#         if sys.platform != 'darwin':
#             nt.assert_equal(len(w), 1)
#             nt.assert_in('Ignoring', str(w[0]))


# TODO Fix this test because `patch('os.name', "posix")` causes trouble
# def test_get_ipython_dir_5():
#     """test_get_ipython_dir_5, use .ipython if exists and XDG defined, but doesn't exist."""
#     with patch_get_home_dir(HOME_TEST_DIR), \
#             patch('os.name', 'posix'):
#         try:
#             Path(XDG_TEST_DIR, "ipython").rmdir()
#         except OSError as e:
#             if e.errno != errno.ENOENT:
#                 raise

#         with modified_env(
#             {
#                 "IPYTHON_DIR": None,
#                 "IPYTHONDIR": None,
#                 "XDG_CONFIG_HOME": "%s" % XDG_TEST_DIR,
#             }
#         ):
#             ipdir = paths.get_ipython_dir()

#         nt.assert_equal(ipdir, IP_TEST_DIR)

# TODO Fix this test because `patch('os.name', "posix")` causes trouble
# def test_get_ipython_dir_6():
#     """test_get_ipython_dir_6, use home over XDG if defined and neither exist."""
#     xdg = Path(HOME_TEST_DIR, "somexdg")
#     xdg.mkdir()
#     shutil.rmtree(Path(HOME_TEST_DIR, ".ipython"))
#     print(paths._writable_dir)
#     with patch_get_home_dir(HOME_TEST_DIR), patch.object(
#         paths, "get_xdg_dir", return_value=xdg
#     ), patch('os.name', 'posix'), \
#         modified_env(
#         {"IPYTHON_DIR": None, "IPYTHONDIR": None, "XDG_CONFIG_HOME": None}
#     ), warnings.catch_warnings(
#         record=True
#     ) as w:
#         ipdir = paths.get_ipython_dir()

#     nt.assert_equal(ipdir, Path(HOME_TEST_DIR, ".ipython"))
#     nt.assert_equal(len(w), 0)

def test_get_ipython_dir_7():
    """test_get_ipython_dir_7, test home directory expansion on IPYTHONDIR"""
    home_dir = Path.home()
    with modified_env({"IPYTHONDIR": "%s" % Path(home_dir, "somewhere")}):
        with patch.object(paths, "_writable_dir", return_value=True):
            ipdir = paths.get_ipython_dir()
    nt.assert_equal(ipdir, Path(home_dir, "somewhere"))


@skip_win32
def test_get_ipython_dir_8():
    """test_get_ipython_dir_8, test / home directory"""
    with patch.object(paths, "_writable_dir", lambda path: bool(path)), patch.object(
        paths, "get_xdg_dir", return_value=None
    ), modified_env({"IPYTHON_DIR": None, "IPYTHONDIR": None, "HOME": "/"}):
        nt.assert_equal(paths.get_ipython_dir(), Path("/.ipython"))


def test_get_ipython_cache_dir():
    with modified_env({"HOME": "%s" % HOME_TEST_DIR}):
        if os_name == "posix" and sys.platform != "darwin":
            # test default
            Path(HOME_TEST_DIR, ".cache").mkdir(parents=True)
            with modified_env({'XDG_CACHE_HOME': None}):
                ipdir = paths.get_ipython_cache_dir()
            nt.assert_equal(Path(HOME_TEST_DIR, ".cache", "ipython"), ipdir)
            assert_isdir(ipdir)

            # test env override
            with modified_env({"XDG_CACHE_HOME": "%s" % XDG_CACHE_DIR}):
                ipdir = paths.get_ipython_cache_dir()
            assert_isdir(ipdir)
            nt.assert_equal(ipdir, Path(XDG_CACHE_DIR, "ipython"))
        else:
            nt.assert_equal(paths.get_ipython_cache_dir(),
                            paths.get_ipython_dir())

def test_get_ipython_package_dir():
    ipdir = paths.get_ipython_package_dir()
    assert_isdir(ipdir)


def test_get_ipython_module_path():
    ipapp_path = paths.get_ipython_module_path('IPython.terminal.ipapp')
    assert_isfile(ipapp_path)
