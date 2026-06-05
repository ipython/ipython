# coding: utf-8
"""Test suite for our sysinfo utilities."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import sys
import platform

import pytest

from IPython.utils import sysinfo


def test_json_getsysinfo():
    """Test that get_sys_info returns JSON-serializable data."""
    json.dumps(sysinfo.get_sys_info())


def test_get_sys_info_returns_dict():
    info = sysinfo.get_sys_info()
    assert isinstance(info, dict)


@pytest.mark.parametrize("key", [
    "ipython_version",
    "ipython_path",
    "commit_source",
    "commit_hash",
    "sys_version",
    "sys_executable",
    "sys_platform",
    "platform",
    "os_name",
    "default_encoding",
])
def test_get_sys_info_has_key(key):
    info = sysinfo.get_sys_info()
    assert key in info


def test_get_sys_info_sys_version_matches():
    info = sysinfo.get_sys_info()
    assert info["sys_version"] == sys.version


def test_get_sys_info_sys_executable_matches():
    info = sysinfo.get_sys_info()
    assert info["sys_executable"] == sys.executable


def test_get_sys_info_platform_is_string():
    info = sysinfo.get_sys_info()
    assert isinstance(info["platform"], str)
    assert len(info["platform"]) > 0


def test_sys_info_returns_string():
    result = sysinfo.sys_info()
    assert isinstance(result, str)


def test_sys_info_contains_version():
    result = sysinfo.sys_info()
    from IPython.core import release
    assert release.version in result
