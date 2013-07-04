# encoding: utf-8
"""Tests for IPython.utils.module_paths.py"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import with_statement

import os
import shutil
import sys
import tempfile

from os.path import join, abspath, split

from IPython.testing.tools import make_tempfile

import IPython.utils.module_paths as mp

env = os.environ
TEST_FILE_PATH = split(abspath(__file__))[0]
TMP_TEST_DIR = tempfile.mkdtemp()
#
# Setup/teardown functions/decorators
#

old_syspath = sys.path

def make_empty_file(fname):
    f = open(fname, 'w')
    f.close()


def setup():
    """Setup testenvironment for the module:

    """
    # Do not mask exceptions here.  In particular, catching WindowsError is a
    # problem because that exception is only defined on Windows...
    os.makedirs(join(TMP_TEST_DIR, "xmod"))
    os.makedirs(join(TMP_TEST_DIR, "nomod"))
    make_empty_file(join(TMP_TEST_DIR, "xmod/__init__.py"))
    make_empty_file(join(TMP_TEST_DIR, "xmod/sub.py"))
    make_empty_file(join(TMP_TEST_DIR, "pack.py"))
    make_empty_file(join(TMP_TEST_DIR, "packpyc.pyc"))
    sys.path = [TMP_TEST_DIR]

def teardown():
    """Teardown testenvironment for the module:

            - Remove tempdir
            - restore sys.path
    """
    # Note: we remove the parent test dir, which is the root of all test
    # subdirs we may have created.  Use shutil instead of os.removedirs, so
    # that non-empty directories are all recursively removed.
    shutil.rmtree(TMP_TEST_DIR)
    sys.path = old_syspath


def test_get_init_1():
    """See if get_init can find __init__.py in this testdir"""
    with make_tempfile(join(TMP_TEST_DIR, "__init__.py")):
        assert mp.get_init(TMP_TEST_DIR)

def test_get_init_2():
    """See if get_init can find __init__.pyw in this testdir"""
    with make_tempfile(join(TMP_TEST_DIR, "__init__.pyw")):
        assert mp.get_init(TMP_TEST_DIR)

def test_get_init_3():
    """get_init can't find __init__.pyc in this testdir"""
    with make_tempfile(join(TMP_TEST_DIR, "__init__.pyc")):
        assert mp.get_init(TMP_TEST_DIR) is None

def test_get_init_4():
    """get_init can't find __init__ in empty testdir"""
    assert mp.get_init(TMP_TEST_DIR) is None


def test_find_mod_1():
    modpath = join(TMP_TEST_DIR, "xmod", "__init__.py")
    assert mp.find_mod("xmod") == modpath

def test_find_mod_2():
    modpath = join(TMP_TEST_DIR, "xmod", "__init__.py")
    assert mp.find_mod("xmod") == modpath

def test_find_mod_3():
    modpath = join(TMP_TEST_DIR, "xmod", "sub.py")
    assert mp.find_mod("xmod.sub") == modpath

def test_find_mod_4():
    modpath = join(TMP_TEST_DIR, "pack.py")
    assert mp.find_mod("pack") == modpath

def test_find_mod_5():
    assert mp.find_mod("packpyc") is None

def test_find_module_1():
    modpath = join(TMP_TEST_DIR, "xmod")
    assert mp.find_module("xmod") == modpath

def test_find_module_2():
    """Testing sys.path that is empty"""
    assert mp.find_module("xmod", []) is None

def test_find_module_3():
    """Testing sys.path that is empty"""
    assert mp.find_module(None, None) is None

def test_find_module_4():
    """Testing sys.path that is empty"""
    assert mp.find_module(None) is None

def test_find_module_5():
    assert mp.find_module("xmod.nopack") is None
