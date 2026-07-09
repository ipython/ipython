"""Tests for IPython.utils.importstring."""

# -----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# -----------------------------------------------------------------------------

import os
import os.path
import sys

import pytest

from IPython.utils.importstring import import_item

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


def test_import_plain():
    os2 = import_item("os")
    assert os is os2


def test_import_nested():
    path2 = import_item("os.path")
    assert os.path is path2


def test_import_raises():
    pytest.raises(ImportError, import_item, "IPython.foobar")


@pytest.mark.parametrize("name,expected", [
    ("os", os),
    ("sys", sys),
    ("os.path", os.path),
])
def test_import_returns_correct_object(name, expected):
    assert import_item(name) is expected


@pytest.mark.parametrize("bad_name", [
    "IPython.nonexistent_module",
    "completely.fake.module",
    "os.nonexistent_attribute",
])
def test_import_invalid_raises_importerror(bad_name):
    with pytest.raises(ImportError):
        import_item(bad_name)


def test_import_deep_nested():
    from collections import abc
    result = import_item("collections.abc")
    assert result is abc


def test_import_result_is_callable_for_functions():
    result = import_item("os.path.join")
    assert callable(result)
    assert result("a", "b") == os.path.join("a", "b")
