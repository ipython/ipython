# coding: utf-8
"""Tests for the compilerop module."""
# -----------------------------------------------------------------------------
#  Copyright (C) 2010-2011 The IPython Development Team.
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import linecache
import sys

import pytest

from IPython.core import compilerop


@pytest.mark.parametrize("cell_number,prefix", [
    (0, "<ipython-input-0"),
    (9, "<ipython-input-9"),
    (42, "<ipython-input-42"),
])
def test_code_name_cell_number(cell_number, prefix):
    name = compilerop.code_name("x=1", cell_number)
    assert name.startswith(prefix)


def test_code_name_default_is_zero():
    name = compilerop.code_name("x=1")
    assert name.startswith("<ipython-input-0")


def test_cache():
    """Test the compiler correctly compiles and caches inputs"""
    cp = compilerop.CachingCompiler()
    ncache = len(linecache.cache)
    cp.cache("x=1")
    assert len(linecache.cache) > ncache


def test_proper_default_encoding():
    assert sys.getdefaultencoding() == "utf-8"


@pytest.mark.parametrize("src", [
    "a_unique_var_for_test_1 = 1",
    "t = 'žćčšđ_unique'",
    "y = '日本語_unique'",
])
def test_cache_source(src):
    cp = compilerop.CachingCompiler()
    ncache = len(linecache.cache)
    cp.cache(src)
    assert len(linecache.cache) > ncache


def test_compiler_check_cache():
    """Test the compiler properly manages the cache."""
    cp = compilerop.CachingCompiler()
    cp.cache("x=1", 99)
    linecache.checkcache()
    assert any(
        k.startswith("<ipython-input-99") for k in linecache.cache
    ), "Entry for input-99 missing from linecache"
